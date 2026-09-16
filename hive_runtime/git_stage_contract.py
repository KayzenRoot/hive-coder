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
        "path_count",
        "paths",
        "worktree_states",
        "path_bindings",
        "candidate_index_sha256",
        "candidate_index_bytes",
        "object_store_contract",
        "object_store_format",
        "git_dir_identity",
        "object_store_identity",
        "target_state",
    }
)

_HEX = "0123456789abcdef"


def _require_hex(value: object, length: int, label: str) -> str:
    if not isinstance(value, str) or len(value) != length or any(ch not in _HEX for ch in value):
        raise ValueError(f"{label} must be a lowercase hexadecimal string of length {length}")
    return value


@dataclass(frozen=True)
class GitStagePathBinding:
    """Deterministic per-path binding of approved content to a Git blob identity."""

    path: str
    content_sha256: str
    content_bytes: int
    blob_oid: str

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("binding path must be non-empty")
        _require_hex(self.content_sha256, 64, "binding content digest")
        if not isinstance(self.content_bytes, int) or self.content_bytes < 0:
            raise ValueError("binding byte length must be a non-negative integer")
        _require_hex(self.blob_oid, 40, "binding blob object id")

    def canonical(self) -> dict[str, object]:
        return {
            "path": self.path,
            "content_sha256": self.content_sha256,
            "content_bytes": self.content_bytes,
            "blob_oid": self.blob_oid,
        }


@dataclass(frozen=True)
class GitStageObjectStoreBinding:
    """Bounded identity of the repository-local object store that will receive publication.

    Held as plain fields so the contract module keeps no dependency on the
    inspector that produces them.
    """

    contract: str
    object_format: str
    git_dir_identity: str
    objects_identity: str

    def __post_init__(self) -> None:
        for label, value in (
            ("object store contract", self.contract),
            ("object store format", self.object_format),
            ("git dir identity", self.git_dir_identity),
            ("objects identity", self.objects_identity),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{label} must be a non-empty string")

    def canonical(self) -> dict[str, str]:
        return {
            "object_store_contract": self.contract,
            "object_store_format": self.object_format,
            "git_dir_identity": self.git_dir_identity,
            "object_store_identity": self.objects_identity,
        }


@dataclass(frozen=True)
class GitStageIndexCandidateBinding:
    """Bounded identity of the exact candidate index the approval commits to."""

    sha256: str
    content_bytes: int

    def __post_init__(self) -> None:
        _require_hex(self.sha256, 64, "candidate index digest")
        if not isinstance(self.content_bytes, int) or self.content_bytes <= 0:
            raise ValueError("candidate index byte length must be a positive integer")

    def canonical(self) -> dict[str, object]:
        return {"candidate_index_sha256": self.sha256, "candidate_index_bytes": self.content_bytes}


@dataclass(frozen=True)
class GitStageRequestBinding:
    """The exact, raw-byte-free metadata a git.write approval authorizes.

    Every field is bounded metadata. Raw worktree bytes, raw index bytes and raw
    compressed object bytes have no representation here, by construction.
    """

    observed: GitStageObservedState
    path_bindings: tuple[GitStagePathBinding, ...]
    candidate: GitStageIndexCandidateBinding
    object_store: GitStageObjectStoreBinding

    def __post_init__(self) -> None:
        observed_paths = tuple(state.path for state in self.observed.worktree_states)
        bound_paths = tuple(binding.path for binding in self.path_bindings)
        if not self.path_bindings or bound_paths != observed_paths:
            raise ValueError("path bindings must exactly match the approved worktree paths")
        for state, binding in zip(self.observed.worktree_states, self.path_bindings):
            if binding.content_sha256 != state.content_sha256 or binding.content_bytes != state.content_bytes:
                raise ValueError("path binding disagrees with the approved worktree state")

    def arguments(self) -> dict[str, object]:
        """Canonical, JSON-safe argument mapping for the control-plane request."""
        arguments: dict[str, object] = {
            "contract": GIT_STAGE_CONTRACT,
            "repository_identity": self.observed.repository_identity,
            "repository_head": self.observed.repository_head,
            "index_state": self.observed.index_state,
            "index_identity": self.observed.index_identity,
            "index_sha256": self.observed.index_sha256,
            "path_count": len(self.path_bindings),
            "paths": [binding.path for binding in self.path_bindings],
            "worktree_states": [state.canonical() for state in self.observed.worktree_states],
            "path_bindings": [binding.canonical() for binding in self.path_bindings],
            "target_state": GIT_STAGE_TARGET_STATE,
        }
        arguments.update(self.candidate.canonical())
        arguments.update(self.object_store.canonical())
        if set(arguments) != GIT_STAGE_ARGUMENT_KEYS:
            raise ValueError("git stage arguments do not match the frozen argument key set")
        return arguments


@dataclass(frozen=True)
class GitStageWorktreeStat:
    """Bounded numeric stat record for one approved regular worktree file.

    A Git index entry carries stat data so Git can decide cheaply whether the
    worktree still matches the index. Without the exact observed values the
    codec would have to guess, so the values are captured here and bound into
    the same observation the approval is taken over.

    This mirrors exactly what a Git index entry stores. Access time is
    deliberately excluded: Git does not record it, and observing a file updates
    it, so including it would make an unchanged repository report as stale on
    the very revalidation that is meant to prove it is unchanged.
    """

    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    size: int
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
        for label, value in (("mtime_s", self.mtime_s), ("ctime_s", self.ctime_s)):
            if not isinstance(value, int):
                raise ValueError(f"worktree stat {label} must be an integer")
        for label, value in (("mtime_ns", self.mtime_ns), ("ctime_ns", self.ctime_ns)):
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
