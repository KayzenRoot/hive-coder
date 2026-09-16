from __future__ import annotations

"""Read-only Git repository observation and exact stale-state revalidation."""

import hashlib
import os
import stat
from pathlib import Path
from typing import Sequence

from .git_stage import GitStagePreparation, GitStageUnavailableError, GitStageUnsupportedRepositoryError
from .git_stage_contract import ABSENT_INDEX_IDENTITY, ABSENT_INDEX_SHA256, GitStageObservedState, GitStageWorktreeState, UNBORN_HEAD
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


def _open_regular_nofollow(path: Path) -> tuple[int, os.stat_result]:
    # O_NONBLOCK prevents hostile FIFOs/devices from stalling before fstat rejects them.
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try: fd = os.open(path, flags)
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
        """Require exact equality with the approved repository/index/worktree observation."""
        paths = tuple(item.path for item in expected.worktree_states)
        current = self.observe(paths)
        if current != expected:
            raise GitStageUnavailableError("approved Git repository state is stale")

    def _reject_unsupported_repository_features(self) -> None:
        for name in ("commondir", "modules", "shallow"):
            try: (self.git_dir / name).lstat()
            except FileNotFoundError: continue
            except OSError as exc: raise GitStageUnsupportedRepositoryError("cannot prove repository envelope") from exc
            raise GitStageUnsupportedRepositoryError(f"unsupported Git repository feature: {name}")

    def _observe_head(self) -> str:
        value = _read_bounded_regular(self.git_dir / "HEAD", _MAX_HEAD_BYTES)
        if value.startswith("ref: "):
            ref = value[5:]
            if not ref.startswith("refs/heads/") or ".." in ref or "\\" in ref: raise GitStageUnsupportedRepositoryError("HEAD symbolic ref is outside supported envelope")
            try: oid = _read_bounded_regular(self.git_dir.joinpath(*ref.split("/")), _MAX_REF_BYTES)
            except GitStageUnsupportedRepositoryError:
                oid = self._packed_ref(ref)
                if oid is None: return UNBORN_HEAD
            return self._validate_oid(oid)
        return self._validate_oid(value)

    def _packed_ref(self, ref: str) -> str | None:
        try: text = _read_bounded_regular(self.git_dir / "packed-refs", 1024 * 1024)
        except GitStageUnsupportedRepositoryError: return None
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
        except GitStageUnsupportedRepositoryError:
            if not path.exists(): return "absent", ABSENT_INDEX_IDENTITY, ABSENT_INDEX_SHA256
            raise
        try:
            digest, _ = _sha256_file(fd); return "regular", _identity(st), digest
        finally: os.close(fd)

    def _observe_worktree(self, relative: str) -> GitStageWorktreeState:
        path = self.root.joinpath(*relative.split("/")); cursor = self.root
        for component in relative.split("/"):
            cursor = cursor / component
            try: st = cursor.lstat()
            except OSError as exc: raise GitStageUnsupportedRepositoryError("approved worktree path is unavailable") from exc
            if stat.S_ISLNK(st.st_mode): raise GitStageUnsupportedRepositoryError("symlink worktree paths are unsupported")
        fd, st = _open_regular_nofollow(path)
        try:
            digest, size = _sha256_file(fd); return GitStageWorktreeState(relative, _identity(st), digest, size)
        finally: os.close(fd)

    def mutation_ready(self, prepared: GitStagePreparation) -> None:
        self.revalidate(prepared.observed)
        raise GitStageUnavailableError("repository state is current but Git mutation authority is unavailable")

    def publish(self, prepared):
        del prepared; raise GitStageUnavailableError("observer has no mutation authority")

    def close(self) -> None: return None
