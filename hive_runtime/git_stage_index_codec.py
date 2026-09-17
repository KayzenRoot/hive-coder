from __future__ import annotations

"""Bounded, data-only Git index codec for HCODER-WO-0023.

Division of responsibility (proven by the focused tests, not assumed):

* Dulwich 1.2.15 is used strictly as a bounded index-entry **parser and
  serializer primitive** behind this Hive-owned adapter. It is not an authority
  provider and cannot mint or interpret permits.
* Hive owns the envelope law: index version policy, conflict/extension policy,
  entry ordering, verbatim preservation of proven optional extensions, SHA-1
  trailer computation, and post-construction self-verification.

The codec returns **data only**. It never publishes to ``.git/index``, never
takes `.git/index.lock`, and never touches the object store. There is no
porcelain, no ``GitFile.close()``, no subprocess, no hook, no filter, no remote,
no credential and no network surface on this path.

Extensions are accepted when reading a validated source index and are **never
carried into a candidate that changes staged entries**. The ``TREE`` extension
is a cache-tree: each node records tree object ids that describe portions of the
*previous* index. Replacing a staged path invalidates every node covering it, so
appending the previous region verbatim would hand Git a structurally consistent
but semantically stale cache. Git does not detect that case, and a subsequent
``write-tree`` silently reuses the old subtree, discarding the staged change
without any error. ``TREE`` is optional, so the fail-safe rule for this slice is
to drop it and let Git recompute. Rebuilding a cache-tree is deliberately out of
scope; see the WO-0023 Context Lock.

Dulwich does not preserve the ``TREE`` extension through its own serializer and
does not write the index trailer. Hive therefore owns the trailer, and owns the
policy that no source extension survives into a mutated candidate.
"""

import hashlib
import io
import sys
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from typing import Protocol, Sequence

from .git_index_envelope import inspect_git_index_envelope
from .git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError
from .git_stage_contract import ABSENT_INDEX_SHA256, GitStageObservedState
from .git_stage_plan import GitStagePlan

DULWICH_CANDIDATE_VERSION = "1.2.15"
INDEX_CODEC_CONTRACT = "hive-git-index-codec-v1"
DULWICH_CODEC_ID = "dulwich-1.2.15-pure-python-index-codec-v1"
ADMITTED_DULWICH_WHEEL_TAG = "py3-none-any"
NEW_INDEX_VERSION = 2

# This slice produces candidates with an empty extension region, always.
CANDIDATE_EXTENSION_POLICY = "drop-source-extensions"
SOURCE_EXTENSIONS_ACCEPTED_FOR_VALIDATION = frozenset({"TREE"})

# Modules this path must never pull in. Import isolation is asserted, not assumed.
_FORBIDDEN_MODULES = (
    "urllib3",
    "dulwich.client",
    "dulwich.porcelain",
    "dulwich.repo",
    "dulwich.server",
    "socket",
    "ssl",
    "subprocess",
)

# Per-entry flag bits that carry behaviour this first slice does not model.
_FLAG_ASSUME_VALID = 0x8000
_FLAG_EXTENDED = 0x4000


@dataclass(frozen=True)
class GitIndexCandidate:
    """Data-only candidate index. Digest and length are derived, never supplied.

    ``source_extensions`` records what the validated source index carried, purely
    as evidence. The candidate itself carries **no** extension region: this slice
    never propagates a source extension into a mutated index.
    """

    codec_id: str
    source_index_sha256: str
    paths: tuple[str, ...]
    serialized: bytes
    index_version: int = 0
    source_extensions: tuple[str, ...] = ()
    candidate_extension_policy: str = CANDIDATE_EXTENSION_POLICY
    candidate_sha256: str = ""
    candidate_bytes: int = 0

    def __post_init__(self) -> None:
        if not self.codec_id:
            raise ValueError("codec_id is required")
        if self.source_index_sha256 != ABSENT_INDEX_SHA256 and len(self.source_index_sha256) != 64:
            raise ValueError("source index digest must be SHA-256 or the absent-index sentinel")
        if not self.paths or tuple(sorted(self.paths)) != self.paths or len(set(self.paths)) != len(self.paths):
            raise ValueError("candidate paths must be deterministic unique paths")
        if not isinstance(self.serialized, bytes):
            raise TypeError("serialized candidate must be bytes")
        object.__setattr__(self, "candidate_sha256", hashlib.sha256(self.serialized).hexdigest())
        object.__setattr__(self, "candidate_bytes", len(self.serialized))


class GitIndexCodec(Protocol):
    codec_id: str

    def build_candidate(
        self,
        observed: GitStageObservedState,
        paths: Sequence[str],
        *,
        source_index_bytes: bytes | None = ...,
        stage_plan: GitStagePlan | None = ...,
    ) -> GitIndexCandidate: ...


class UnavailableGitIndexCodec:
    """Default codec until the governed dependency is materialized."""

    codec_id = "unavailable-git-index-codec-v1"

    def build_candidate(
        self,
        observed: GitStageObservedState,
        paths: Sequence[str],
        *,
        source_index_bytes: bytes | None = None,
        stage_plan: GitStagePlan | None = None,
    ) -> GitIndexCandidate:
        del observed, paths, source_index_bytes, stage_plan
        raise GitStageUnavailableError(
            "Git index codec is unavailable until the reviewed backend is explicitly enabled"
        )


def _provenance_gate() -> None:
    """Fail closed unless the exact admitted pure-Python artifact is installed.

    This is the runtime half of the WO-0023 backend/provenance gate: the reviewed
    version must be installed, and it must be the pure-Python artifact so
    correctness can never depend on an optional compiled extension.
    """
    try:
        dist = distribution("dulwich")
    except PackageNotFoundError as exc:
        raise GitStageUnavailableError(
            "governed Git index codec backend is not materialized; install with "
            "`python -m pip install --no-deps --require-hashes -r "
            "foundations/python-dependencies.requirements.txt`"
        ) from exc
    if dist.version != DULWICH_CANDIDATE_VERSION:
        raise GitStageUnavailableError("Git index codec backend version is not the reviewed version")
    wheel = dist._path / "WHEEL"  # type: ignore[attr-defined]
    tag = None
    try:
        for line in wheel.read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("tag:"):
                tag = line.split(":", 1)[1].strip()
                break
    except OSError as exc:
        raise GitStageUnavailableError("cannot prove the installed codec artifact identity") from exc
    if tag != ADMITTED_DULWICH_WHEEL_TAG:
        raise GitStageUnavailableError(
            "Git index codec backend must be the admitted pure-Python artifact, not a platform wheel"
        )


def _load_backend():
    """Import the admitted primitives and prove the import surface is isolated."""
    _provenance_gate()
    before = set(sys.modules)
    from dulwich.index import (  # noqa: PLC0415 - deliberate lazy, gated import
        ConflictedIndexEntry,
        IndexEntry,
        SerializedIndexEntry,
        read_index_dict_with_version,
        write_index,
    )

    introduced = set(sys.modules) - before
    present_forbidden = {name for name in _FORBIDDEN_MODULES if name in introduced}
    if present_forbidden:
        raise GitStageUnavailableError(
            "codec backend import surface is not isolated: " + ", ".join(sorted(present_forbidden))
        )
    return {
        "ConflictedIndexEntry": ConflictedIndexEntry,
        "IndexEntry": IndexEntry,
        "SerializedIndexEntry": SerializedIndexEntry,
        "read_index_dict_with_version": read_index_dict_with_version,
        "write_index": write_index,
    }


def _entry_name_bytes(path: str) -> bytes:
    try:
        name = path.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise GitStageUnsupportedRepositoryError("Git index path is not bounded UTF-8") from exc
    if not name:
        raise GitStageUnsupportedRepositoryError("Git index path is empty")
    return name


class DulwichGitIndexCodec:
    """Hive-owned codec that serialises a candidate index as data only."""

    codec_id = DULWICH_CODEC_ID

    def build_candidate(
        self,
        observed: GitStageObservedState,
        paths: Sequence[str],
        *,
        source_index_bytes: bytes | None = None,
        stage_plan: GitStagePlan | None = None,
    ) -> GitIndexCandidate:
        backend = _load_backend()

        requested = tuple(paths)
        if not requested or requested != tuple(sorted(set(requested))):
            raise GitStageUnsupportedRepositoryError("candidate paths must be unique and deterministically ordered")
        observed_paths = tuple(state.path for state in observed.worktree_states)
        if requested != observed_paths:
            raise GitStageUnsupportedRepositoryError("candidate paths must exactly match the approved worktree state")
        if stage_plan is None:
            raise GitStageUnavailableError("an authority-free stage plan is required to build an index candidate")
        if tuple(item.path for item in stage_plan.paths) != requested:
            raise GitStageUnsupportedRepositoryError("stage plan paths must exactly match the candidate paths")
        if stage_plan.repository_head != observed.repository_head:
            raise GitStageUnavailableError("stage plan was built for a different repository HEAD")
        if stage_plan.index_sha256 != observed.index_sha256:
            raise GitStageUnavailableError("stage plan was built for a different index state")

        blob_oids = {item.path: item.blob_oid for item in stage_plan.paths}
        stat_by_path = {state.path: state.stat for state in observed.worktree_states}

        if observed.index_state == "absent":
            if source_index_bytes not in (None, b""):
                raise GitStageUnsupportedRepositoryError("an absent index must not carry source index bytes")
            base_entries: dict[bytes, object] = {}
            version = NEW_INDEX_VERSION
            source_extensions: tuple[str, ...] = ()
        else:
            if not isinstance(source_index_bytes, bytes):
                raise GitStageUnavailableError("source index bytes are required for a regular index")
            if hashlib.sha256(source_index_bytes).hexdigest() != observed.index_sha256:
                raise GitStageUnavailableError("source index bytes do not match the approved index digest")
            envelope = inspect_git_index_envelope(source_index_bytes)
            version = envelope.version
            source_extensions = envelope.extensions
            base_entries, parsed_version, _ = backend["read_index_dict_with_version"](io.BytesIO(source_index_bytes))
            if parsed_version != version:
                raise GitStageUnsupportedRepositoryError("Git index version disagrees between envelope and codec")
            for name, entry in base_entries.items():
                if isinstance(entry, backend["ConflictedIndexEntry"]):
                    raise GitStageUnsupportedRepositoryError("conflicted Git index entries are unsupported")

        staged_names = {_entry_name_bytes(path) for path in requested}

        # Fail closed rather than silently discarding per-entry behaviour we do not model.
        for name in staged_names:
            existing = base_entries.get(name)
            if existing is None:
                continue
            if getattr(existing, "extended_flags", 0) or (getattr(existing, "flags", 0) & _FLAG_EXTENDED):
                raise GitStageUnsupportedRepositoryError("staging a path with extended index flags is unsupported")
            if getattr(existing, "flags", 0) & _FLAG_ASSUME_VALID:
                raise GitStageUnsupportedRepositoryError("staging an assume-valid index entry is unsupported")

        SerializedIndexEntry = backend["SerializedIndexEntry"]
        serialized: list[object] = []
        for name, entry in base_entries.items():
            if name in staged_names:
                continue
            serialized.append(
                SerializedIndexEntry(
                    name=name,
                    ctime=entry.ctime,
                    mtime=entry.mtime,
                    dev=entry.dev,
                    ino=entry.ino,
                    mode=entry.mode,
                    uid=entry.uid,
                    gid=entry.gid,
                    size=entry.size,
                    sha=entry.sha,
                    flags=entry.flags,
                    extended_flags=entry.extended_flags,
                )
            )

        for path in requested:
            stat = stat_by_path[path]
            if stat is None:
                raise GitStageUnsupportedRepositoryError(
                    "approved worktree state must carry the exact stat record required by a Git index entry"
                )
            state = next(item for item in observed.worktree_states if item.path == path)
            if stat.size != state.content_bytes:
                raise GitStageUnsupportedRepositoryError("approved stat size disagrees with approved byte length")
            serialized.append(
                SerializedIndexEntry(
                    name=_entry_name_bytes(path),
                    ctime=(stat.ctime_s, stat.ctime_ns),
                    mtime=(stat.mtime_s, stat.mtime_ns),
                    dev=stat.dev,
                    ino=stat.ino,
                    mode=stat.git_mode,
                    uid=stat.uid,
                    gid=stat.gid,
                    size=stat.size,
                    sha=blob_oids[path].encode("ascii"),
                    flags=0,
                    extended_flags=0,
                )
            )

        # Git requires entries in ascending name order; the backend preserves the
        # caller's order, so ordering is Hive-owned.
        serialized.sort(key=lambda item: item.name)

        buffer = io.BytesIO()
        backend["write_index"](buffer, serialized, version, [])
        core = buffer.getvalue()

        # No source extension is ever propagated: a mutated index cannot carry a
        # cache-tree that still describes the pre-mutation entries.
        candidate_bytes = core + hashlib.sha1(core).digest()

        self._verify_candidate(candidate_bytes, version, len(serialized), staged_names, blob_oids, requested)

        return GitIndexCandidate(
            codec_id=self.codec_id,
            source_index_sha256=observed.index_sha256,
            paths=requested,
            serialized=candidate_bytes,
            index_version=version,
            source_extensions=source_extensions,
        )

    @staticmethod
    def _verify_candidate(
        candidate_bytes: bytes,
        version: int,
        entry_count: int,
        staged_names: set[bytes],
        blob_oids: dict[str, str],
        requested: tuple[str, ...],
    ) -> None:
        """Self-verify the produced bytes against Hive envelope law before returning."""
        envelope = inspect_git_index_envelope(candidate_bytes)
        if envelope.version != version or envelope.entry_count != entry_count:
            raise GitStageUnavailableError("produced index candidate failed envelope self-verification")
        if envelope.extensions:
            raise GitStageUnavailableError("produced index candidate must not carry any index extension")
        backend = _load_backend()
        entries, parsed_version, _ = backend["read_index_dict_with_version"](io.BytesIO(candidate_bytes))
        if parsed_version != version or len(entries) != entry_count:
            raise GitStageUnavailableError("produced index candidate failed entry self-verification")
        for path in requested:
            entry = entries.get(_entry_name_bytes(path))
            if entry is None:
                raise GitStageUnavailableError("produced index candidate is missing a staged path")
            sha = entry.sha
            if isinstance(sha, bytes):
                sha = sha.decode("ascii")
            if sha != blob_oids[path]:
                raise GitStageUnavailableError("produced index candidate bound the wrong blob identity")
        if not staged_names.issubset(set(entries.keys())):
            raise GitStageUnavailableError("produced index candidate lost a staged path")


def git_index_entry_oids(data: bytes) -> dict[str, str]:
    """Return ``path -> blob object id`` for a validated index, as data only.

    Used to verify postconditions on a published index and to compare a source
    index against a committed one. The envelope inspector already enforces the
    extension policy, so a source index that carries a proven optional extension
    is still inspectable here; only a *candidate* must be extension-free, and that
    is enforced by the codec's own self-verification.
    """
    envelope = inspect_git_index_envelope(data)
    backend = _load_backend()
    entries, version, _ = backend["read_index_dict_with_version"](io.BytesIO(data))
    if version != envelope.version or len(entries) != envelope.entry_count:
        raise GitStageUnsupportedRepositoryError("Git index disagrees between envelope and codec")
    result: dict[str, str] = {}
    for name, entry in entries.items():
        if isinstance(entry, backend["ConflictedIndexEntry"]):
            raise GitStageUnsupportedRepositoryError("conflicted Git index entries are unsupported")
        sha = entry.sha
        if isinstance(sha, bytes):
            sha = sha.decode("ascii")
        result[name.decode("utf-8")] = str(sha)
    return result


__all__ = [
    "ADMITTED_DULWICH_WHEEL_TAG",
    "CANDIDATE_EXTENSION_POLICY",
    "DULWICH_CANDIDATE_VERSION",
    "DULWICH_CODEC_ID",
    "DulwichGitIndexCodec",
    "GitIndexCandidate",
    "GitIndexCodec",
    "INDEX_CODEC_CONTRACT",
    "SOURCE_EXTENSIONS_ACCEPTED_FOR_VALIDATION",
    "UnavailableGitIndexCodec",
    "git_index_entry_oids",
]
