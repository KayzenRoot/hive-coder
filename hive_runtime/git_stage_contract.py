from __future__ import annotations

from dataclasses import dataclass

GIT_STAGE_CONTRACT = "hive-git-stage-v1"
GIT_STAGE_ACTION = "git_stage_paths_v1"
GIT_STAGE_TARGET_STATE = "index_update"
MAX_STAGE_PATHS = 128
ABSENT_INDEX_IDENTITY = "absent"
ABSENT_INDEX_SHA256 = "absent"
UNBORN_HEAD = "unborn"

GIT_STAGE_ARGUMENT_KEYS = frozenset(
    {
        "contract",
        "repository_identity",
        "repository_head",
        "index_state",
        "index_identity",
        "index_sha256",
        "paths",
        "worktree_states",
        "path_count",
        "target_state",
    }
)


@dataclass(frozen=True)
class GitStageWorktreeStat:
    """Bounded numeric stat record for one approved regular worktree file.

    A Git index entry carries stat data so Git can decide cheaply whether the
    worktree still matches the index. Without the exact observed values the
    codec would have to guess, so the values are captured here and bound into
    the same observation the approval is taken over.
    """

    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
    atime_s: int
    atime_ns: int
    mtime_s: int
    mtime_ns: int
    ctime_s: int
    ctime_ns: int

    def __post_init__(self) -> None:
        for label, value in (
            ("dev", self.dev),
            ("ino", self.ino),
            ("mode", self.mode),
            ("uid", self.uid),
            ("gid", self.gid),
            ("size", self.size),
        ):
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"worktree stat {label} must be a non-negative integer")
        if not 0 <= self.mode <= 0xFFFF:
            raise ValueError("worktree stat mode is outside the bounded range")
        for label, value in (
            ("atime_s", self.atime_s),
            ("mtime_s", self.mtime_s),
            ("ctime_s", self.ctime_s),
        ):
            if not isinstance(value, int):
                raise ValueError(f"worktree stat {label} must be an integer")
        for label, value in (
            ("atime_ns", self.atime_ns),
            ("mtime_ns", self.mtime_ns),
            ("ctime_ns", self.ctime_ns),
        ):
            if not isinstance(value, int) or not 0 <= value < 1_000_000_000:
                raise ValueError(f"worktree stat {label} must be sub-second nanoseconds")

    @property
    def git_mode(self) -> int:
        """Git index file mode for this regular file (100644 or 100755)."""
        return 0o100755 if self.mode & 0o111 else 0o100644

    def canonical(self) -> dict[str, int]:
        return {
            "dev": self.dev,
            "ino": self.ino,
            "mode": self.mode,
            "uid": self.uid,
            "gid": self.gid,
            "size": self.size,
            "atime_s": self.atime_s,
            "atime_ns": self.atime_ns,
            "mtime_s": self.mtime_s,
            "mtime_ns": self.mtime_ns,
            "ctime_s": self.ctime_s,
            "ctime_ns": self.ctime_ns,
        }


@dataclass(frozen=True)
class GitStageWorktreeState:
    """Bounded approved state for one regular worktree file. Raw bytes never belong here."""

    path: str
    file_identity: str
    content_sha256: str
    content_bytes: int
    state: str = "regular"
    stat: GitStageWorktreeStat | None = None

    def __post_init__(self) -> None:
        if not self.path or not self.file_identity:
            raise ValueError("worktree path/identity must be non-empty")
        if self.state != "regular":
            raise ValueError("WO-0023 only supports regular worktree files")
        if len(self.content_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.content_sha256):
            raise ValueError("worktree digest must be lowercase SHA-256")
        if not isinstance(self.content_bytes, int) or self.content_bytes < 0:
            raise ValueError("worktree byte length is invalid")
        if self.stat is not None and self.stat.size != self.content_bytes:
            raise ValueError("worktree stat size must equal the observed byte length")

    def canonical(self) -> dict[str, object]:
        return {
            "path": self.path,
            "file_identity": self.file_identity,
            "content_sha256": self.content_sha256,
            "content_bytes": self.content_bytes,
            "state": self.state,
            "stat": None if self.stat is None else self.stat.canonical(),
        }


@dataclass(frozen=True)
class GitStageObservedState:
    repository_identity: str
    repository_head: str
    index_state: str
    index_identity: str
    index_sha256: str
    worktree_states: tuple[GitStageWorktreeState, ...]

    def __post_init__(self) -> None:
        if not self.repository_identity:
            raise ValueError("repository identity must be non-empty")
        if self.repository_head != UNBORN_HEAD:
            if len(self.repository_head) not in {40, 64} or any(
                ch not in "0123456789abcdef" for ch in self.repository_head
            ):
                raise ValueError("repository HEAD must be an object id or unborn sentinel")
        if self.index_state not in {"absent", "regular"}:
            raise ValueError("index state is unsupported")
        if self.index_state == "absent":
            if self.index_identity != ABSENT_INDEX_IDENTITY or self.index_sha256 != ABSENT_INDEX_SHA256:
                raise ValueError("absent index sentinels do not match")
        else:
            if not self.index_identity or self.index_identity == ABSENT_INDEX_IDENTITY:
                raise ValueError("regular index identity is missing")
            if len(self.index_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.index_sha256):
                raise ValueError("index digest must be lowercase SHA-256")
        if not 1 <= len(self.worktree_states) <= MAX_STAGE_PATHS:
            raise ValueError("worktree state count outside governed ceiling")
        paths = tuple(state.path for state in self.worktree_states)
        if paths != tuple(sorted(set(paths))):
            raise ValueError("worktree states must use unique deterministic path order")


@dataclass(frozen=True)
class GitStageReceipt:
    workspace: str
    repository_identity: str
    repository_head: str
    previous_index_sha256: str
    committed_index_sha256: str
    staged_paths: tuple[str, ...]
    committed_state: str

    def __post_init__(self) -> None:
        if not self.workspace or not self.repository_identity:
            raise ValueError("receipt identity is missing")
        if not self.staged_paths or self.staged_paths != tuple(sorted(set(self.staged_paths))):
            raise ValueError("receipt paths must be unique and deterministic")
        if self.committed_state != "index_updated":
            raise ValueError("unexpected Git stage committed state")
