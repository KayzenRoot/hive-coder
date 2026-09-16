from __future__ import annotations

"""Read-only Git repository observation and exact stale-state revalidation."""

import hashlib
import os
import stat
from pathlib import Path
from typing import Sequence

from .git_stage import GitStagePreparation, GitStageUnavailableError, GitStageUnsupportedRepositoryError
from .git_stage_contract import (
    ABSENT_INDEX_IDENTITY,
    ABSENT_INDEX_SHA256,
    GitStageObservedState,
    GitStageWorktreeState,
    GitStageWorktreeStat,
    UNBORN_HEAD,
)
from .workspace_files import normalize_relative_file_path

_MAX_HEAD_BYTES = 4096
_MAX_REF_BYTES = 256
_MAX_OBSERVED_FILE_BYTES = 16 * 1024 * 1024


def _sha256_file(fd: int) -> tuple[str, int]:
    digest = hashlib.sha256(); total = 0; os.lseek(fd, 0, os.SEEK_SET)
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk: break
        total += len(chunk)
        if total > _MAX_OBSERVED_FILE_BYTES: raise GitStageUnsupportedRepositoryError("observed file exceeds governed ceiling")
        digest.update(chunk)
    return digest.hexdigest(), total


def _identity(st: os.stat_result) -> str:
    return f"posix:{int(st.st_dev)}:{int(st.st_ino)}:{int(st.st_mode)}"


def _bounded_stat(st: os.stat_result) -> GitStageWorktreeStat:
    """Capture the exact numeric stat values a Git index entry needs.

    ``st_*time_ns`` is authoritative; the integer seconds are derived from it so
    the two can never disagree.
    """
    return GitStageWorktreeStat(
        dev=int(st.st_dev),
        ino=int(st.st_ino),
        mode=int(st.st_mode) & 0xFFFF,
        uid=int(st.st_uid),
        gid=int(st.st_gid),
        size=int(st.st_size),
        atime_s=int(st.st_atime_ns // 1_000_000_000),
        atime_ns=int(st.st_atime_ns % 1_000_000_000),
        mtime_s=int(st.st_mtime_ns // 1_000_000_000),
        mtime_ns=int(st.st_mtime_ns % 1_000_000_000),
        ctime_s=int(st.st_ctime_ns // 1_000_000_000),
        ctime_ns=int(st.st_ctime_ns % 1_000_000_000),
    )


def _open_regular_nofollow(path: Path) -> tuple[int, os.stat_result]:
    # O_BINARY is mandatory on Windows: the CRT otherwise opens in text mode,
    # where os.read stops at a 0x1A byte and os.write translates LF to CRLF.
    # Git metadata and index bytes are binary and routinely contain 0x1A.
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try: fd = os.open(path, flags)
    except FileNotFoundError: raise
    except OSError as exc: raise GitStageUnsupportedRepositoryError("required Git/worktree object is not safely readable") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode): raise GitStageUnsupportedRepositoryError("only regular files are supported")
        return fd, st
    except Exception:
        os.close(fd); raise


def _read_bounded_regular(path: Path, ceiling: int) -> str:
    fd, _ = _open_regular_nofollow(path)
    try:
        data = os.read(fd, ceiling + 1)
        if len(data) > ceiling: raise GitStageUnsupportedRepositoryError("Git metadata exceeds governed ceiling")
        return data.decode("ascii", "strict").strip()
    except UnicodeError as exc: raise GitStageUnsupportedRepositoryError("Git metadata is not bounded ASCII") from exc
    finally: os.close(fd)


def _read_optional_bounded_regular(path: Path, ceiling: int) -> str | None:
    """Return None only for true absence; unsafe/corrupt metadata remains an error."""
    try: return _read_bounded_regular(path, ceiling)
    except FileNotFoundError: return None


class PosixGitStageObserver:
    backend_id = "posix-git-stage-observer-v1"

    def __init__(self, workspace_root: str | os.PathLike[str]) -> None:
        root = Path(workspace_root)
        try: canonical = root.resolve(strict=True)
        except OSError as exc: raise GitStageUnsupportedRepositoryError("workspace root is unavailable") from exc
        if not canonical.is_dir(): raise GitStageUnsupportedRepositoryError("workspace root is not a directory")
        self.root = canonical; self.git_dir = canonical / ".git"
        try: git_lstat = self.git_dir.lstat()
        except OSError as exc: raise GitStageUnsupportedRepositoryError("workspace root is not a supported Git repository") from exc
        if stat.S_ISLNK(git_lstat.st_mode) or not stat.S_ISDIR(git_lstat.st_mode): raise GitStageUnsupportedRepositoryError("gitdir indirection/linked worktrees are unsupported")
        self.repository_identity = f"posix-repo:{int(git_lstat.st_dev)}:{int(git_lstat.st_ino)}"

    def observe(self, paths: Sequence[str]) -> GitStageObservedState:
        normalized = tuple(sorted(normalize_relative_file_path(path) for path in paths))
        if not normalized or len(normalized) != len(set(normalized)): raise GitStageUnsupportedRepositoryError("paths must be unique explicit files")
        self._reject_unsupported_repository_features(); head = self._observe_head(); index_state, index_identity, index_sha = self._observe_index()
        worktree = tuple(self._observe_worktree(path) for path in normalized)
        return GitStageObservedState(repository_identity=self.repository_identity, repository_head=head, index_state=index_state, index_identity=index_identity, index_sha256=index_sha, worktree_states=worktree)

    def revalidate(self, expected: GitStageObservedState) -> None:
        paths = tuple(item.path for item in expected.worktree_states); current = self.observe(paths)
        if current != expected: raise GitStageUnavailableError("approved Git repository state is stale")

    def _reject_unsupported_repository_features(self) -> None:
        for name in ("commondir", "modules", "shallow"):
            try: (self.git_dir / name).lstat()
            except FileNotFoundError: continue
            except OSError as exc: raise GitStageUnsupportedRepositoryError("cannot prove repository envelope") from exc
            raise GitStageUnsupportedRepositoryError(f"unsupported Git repository feature: {name}")

    def _observe_head(self) -> str:
        try: value = _read_bounded_regular(self.git_dir / "HEAD", _MAX_HEAD_BYTES)
        except FileNotFoundError as exc: raise GitStageUnsupportedRepositoryError("Git HEAD is absent") from exc
        if value.startswith("ref: "):
            ref = value[5:]
            if not ref.startswith("refs/heads/") or ".." in ref or "\\" in ref: raise GitStageUnsupportedRepositoryError("HEAD symbolic ref is outside supported envelope")
            oid = _read_optional_bounded_regular(self.git_dir.joinpath(*ref.split("/")), _MAX_REF_BYTES)
            if oid is None:
                oid = self._packed_ref(ref)
                if oid is None: return UNBORN_HEAD
            return self._validate_oid(oid)
        return self._validate_oid(value)

    def _packed_ref(self, ref: str) -> str | None:
        text = _read_optional_bounded_regular(self.git_dir / "packed-refs", 1024 * 1024)
        if text is None: return None
        for line in text.splitlines():
            if not line or line.startswith(("#", "^")): continue
            parts = line.split(" ", 1)
            if len(parts) == 2 and parts[1] == ref: return parts[0]
        return None

    @staticmethod
    def _validate_oid(value: str) -> str:
        if len(value) not in {40, 64} or any(ch not in "0123456789abcdef" for ch in value): raise GitStageUnsupportedRepositoryError("HEAD object id is invalid")
        return value

    def _observe_index(self) -> tuple[str, str, str]:
        path = self.git_dir / "index"
        try: fd, st = _open_regular_nofollow(path)
        except FileNotFoundError: return "absent", ABSENT_INDEX_IDENTITY, ABSENT_INDEX_SHA256
        try:
            digest, _ = _sha256_file(fd); return "regular", _identity(st), digest
        finally: os.close(fd)

    def _reject_nested_git_boundary(self, relative: str) -> None:
        """Reject any `.git` marker below the trusted repository root.

        A nested `.git` directory is a nested repository boundary. A nested
        regular `.git` file is gitdir indirection, as used by submodules and
        linked worktrees. Symlink/special `.git` markers are unsafe too. Only
        true absence is allowed. This check is path-scoped and never traverses
        unrelated workspace directories.
        """
        components = relative.split("/")
        cursor = self.root
        for component in components[:-1]:
            cursor = cursor / component
            marker = cursor / ".git"
            try: marker.lstat()
            except FileNotFoundError: continue
            except OSError as exc: raise GitStageUnsupportedRepositoryError("cannot prove nested Git boundary absence") from exc
            raise GitStageUnsupportedRepositoryError("approved path crosses a nested Git repository/submodule boundary")

    def _observe_worktree(self, relative: str) -> GitStageWorktreeState:
        self._reject_nested_git_boundary(relative)
        path = self.root.joinpath(*relative.split("/")); cursor = self.root
        for component in relative.split("/"):
            cursor = cursor / component
            try: st = cursor.lstat()
            except OSError as exc: raise GitStageUnsupportedRepositoryError("approved worktree path is unavailable") from exc
            if stat.S_ISLNK(st.st_mode): raise GitStageUnsupportedRepositoryError("symlink worktree paths are unsupported")
        try: fd, st = _open_regular_nofollow(path)
        except FileNotFoundError as exc: raise GitStageUnsupportedRepositoryError("approved worktree path is unavailable") from exc
        try:
            digest, size = _sha256_file(fd); return GitStageWorktreeState(relative, _identity(st), digest, size, stat=_bounded_stat(st))
        finally: os.close(fd)

    def mutation_ready(self, prepared: GitStagePreparation) -> None:
        self.revalidate(prepared.observed); raise GitStageUnavailableError("repository state is current but Git mutation authority is unavailable")

    def publish(self, prepared):
        del prepared; raise GitStageUnavailableError("observer has no mutation authority")

    def close(self) -> None: return None
