from __future__ import annotations

"""Ownership-safe Git index transaction preparation for HCODER-WO-0023.

This module may acquire a capability-owned `.git/index.lock`, but it cannot
publish an index and it never removes a foreign lock. Lock acquisition is a
pre-authority concurrency reservation, not Git staging authority.
"""

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError


def _digest_fd(fd: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    os.lseek(fd, 0, os.SEEK_SET)
    total = 0
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        digest.update(chunk)
    return digest.hexdigest(), total


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

    def publish(self, *, expected_sha256: str, expected_bytes: int) -> None:
        """Atomically publish the prepared lock as the live `.git/index`.

        The candidate digest and length are re-verified from the lock's own bytes
        immediately before the atomic replacement, so the published index is
        provably the exact approved candidate. A foreign or pre-existing
        `index.lock` can never reach this method: acquisition fails closed.

        The replacement primitive is `os.replace`, which is an atomic
        same-filesystem rename on POSIX and an atomic replace-existing move on
        Windows. Consistent with CP-0022, this is an atomic *publication*, not a
        strict CAS: an external process may still act between the last
        revalidation and this call.
        """
        if len(expected_sha256) != 64:
            raise ValueError("expected candidate digest must be SHA-256")
        self.verify_owned()
        assert self._fd is not None
        actual_digest, actual_bytes = _digest_fd(self._fd)
        if actual_bytes != expected_bytes or actual_digest != expected_sha256:
            raise GitStageUnavailableError("prepared index.lock no longer matches the approved candidate")
        self.verify_owned()

        # Windows refuses to rename a file that still has an open handle, so the
        # owned handle is released immediately before the atomic replacement. The
        # lock identity is re-proved on the pathname in between, so a lock that is
        # no longer ours can never be published.
        os.close(self._fd)
        self._fd = None
        try:
            live = GitIndexLockIdentity.from_stat(os.lstat(self.lock_path))
        except OSError as exc:
            raise GitStageUnavailableError("owned index.lock is no longer provable") from exc
        if live != self._identity:
            raise GitStageUnavailableError("owned index.lock identity changed before publication")

        target = self.git_dir / "index"
        try:
            os.replace(self.lock_path, target)
        except OSError as exc:
            raise GitStageUnavailableError("atomic index publication failed") from exc
        self._published = True
        self.verify_published(expected_sha256=expected_sha256, expected_bytes=expected_bytes)

    def verify_published(self, *, expected_sha256: str, expected_bytes: int) -> None:
        """Postcondition: the live index bytes hash exactly to the approved candidate."""
        path = self.git_dir / "index"
        try:
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        except OSError as exc:
            raise GitStageUnavailableError("published index is not readable") from exc
        try:
            digest, size = _digest_fd(fd)
        finally:
            os.close(fd)
        if size != expected_bytes or digest != expected_sha256:
            raise GitStageUnavailableError("published index does not match the approved candidate")

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
