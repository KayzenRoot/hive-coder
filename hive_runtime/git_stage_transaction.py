from __future__ import annotations

"""Ownership-safe Git index transaction preparation for HCODER-WO-0023.

This module may acquire a capability-owned `.git/index.lock`, but it cannot
publish an index and it never removes a foreign lock. Lock acquisition is a
pre-authority concurrency reservation, not Git staging authority.
"""

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError


@dataclass(frozen=True)
class GitIndexLockIdentity:
    device: int
    inode: int
    mode: int

    @classmethod
    def from_stat(cls, st: os.stat_result) -> "GitIndexLockIdentity":
        return cls(int(st.st_dev), int(st.st_ino), int(st.st_mode))


class GitIndexLockBusyError(GitStageUnavailableError):
    """A foreign/existing Git index lock blocks safe preparation."""


class PosixGitIndexTransaction:
    """Own exactly one exclusive index.lock and clean up only that identity."""

    def __init__(self, git_dir: str | os.PathLike[str]) -> None:
        self.git_dir = Path(git_dir)
        self.lock_path = self.git_dir / "index.lock"
        self._fd: int | None = None
        self._identity: GitIndexLockIdentity | None = None
        self._published = False

    @property
    def owns_lock(self) -> bool:
        return self._fd is not None and self._identity is not None and not self._published

    @property
    def lock_identity(self) -> GitIndexLockIdentity | None:
        return self._identity

    def acquire(self) -> GitIndexLockIdentity:
        if self._fd is not None:
            raise GitStageUnavailableError("index transaction already owns a lock")
        # O_BINARY is required on Windows: without it the CRT opens in text mode
        # and os.write translates every LF to CRLF, corrupting binary index bytes.
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(self.lock_path, flags, 0o600)
        except FileExistsError as exc:
            raise GitIndexLockBusyError("foreign/existing index.lock fails closed") from exc
        except OSError as exc:
            raise GitStageUnsupportedRepositoryError("cannot safely acquire index.lock") from exc
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise GitStageUnsupportedRepositoryError("index.lock is not a regular file")
            identity = GitIndexLockIdentity.from_stat(st)
            live = os.lstat(self.lock_path)
            if GitIndexLockIdentity.from_stat(live) != identity:
                raise GitStageUnsupportedRepositoryError("index.lock identity changed during acquisition")
            self._fd = fd
            self._identity = identity
            return identity
        except Exception:
            os.close(fd)
            self._unlink_if_owned_identity_from_stat(locals().get("st"))
            raise

    def verify_owned(self) -> None:
        if self._fd is None or self._identity is None:
            raise GitStageUnavailableError("index transaction does not own a lock")
        try:
            fd_identity = GitIndexLockIdentity.from_stat(os.fstat(self._fd))
            live_identity = GitIndexLockIdentity.from_stat(os.lstat(self.lock_path))
        except OSError as exc:
            raise GitStageUnavailableError("owned index.lock is no longer provable") from exc
        if fd_identity != self._identity or live_identity != self._identity:
            raise GitStageUnavailableError("owned index.lock identity changed")

    def write_prepared_index(self, data: bytes) -> None:
        """Write candidate bytes only to our private lock, never to `.git/index`."""
        if not isinstance(data, bytes):
            raise TypeError("prepared index payload must be bytes")
        self.verify_owned()
        assert self._fd is not None
        os.ftruncate(self._fd, 0)
        os.lseek(self._fd, 0, os.SEEK_SET)
        view = memoryview(data)
        while view:
            written = os.write(self._fd, view)
            if written <= 0:
                raise GitStageUnavailableError("short write while preparing index.lock")
            view = view[written:]
        os.fsync(self._fd)
        self.verify_owned()

    def publish(self) -> None:
        raise GitStageUnavailableError(
            "index publication is intentionally unavailable before Git mutation authority"
        )

    def close(self) -> None:
        fd, identity = self._fd, self._identity
        self._fd = None
        self._identity = None
        if fd is not None:
            try:
                os.close(fd)
            finally:
                if identity is not None and not self._published:
                    self._unlink_if_owned(identity)

    def _unlink_if_owned(self, identity: GitIndexLockIdentity) -> None:
        try:
            live = GitIndexLockIdentity.from_stat(os.lstat(self.lock_path))
        except FileNotFoundError:
            return
        except OSError:
            return
        if live == identity:
            try:
                os.unlink(self.lock_path)
            except OSError:
                return

    def _unlink_if_owned_identity_from_stat(self, st: os.stat_result | None) -> None:
        if st is not None:
            self._unlink_if_owned(GitIndexLockIdentity.from_stat(st))

    def __enter__(self) -> "PosixGitIndexTransaction":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
