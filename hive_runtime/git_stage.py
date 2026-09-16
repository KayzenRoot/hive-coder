from __future__ import annotations

"""Governed Git staging adapter boundary for HCODER-WO-0023.

This module is intentionally non-mutating until a backend is proven and the
Permission & Control Plane receives an explicit Context Lock delta.  Keeping
this adapter importable now lets contract/security tests target stable symbols
without accidentally granting repository mutation authority.
"""

import hashlib
import os
import threading
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence, runtime_checkable

from .control_plane import PermissionControlPlane
from .control_types import ActionRequest, ActionTarget, Capability, SessionState, normalize_workspace
from .errors import ControlPlaneError
from .git_stage_contract import (
    GIT_STAGE_ACTION,
    GIT_STAGE_ARGUMENT_KEYS,
    GIT_STAGE_CONTRACT,
    GIT_STAGE_TARGET_STATE,
    MAX_STAGE_PATHS,
    GitStageIndexCandidateBinding,
    GitStageObjectStoreBinding,
    GitStageObservedState,
    GitStagePathBinding,
    GitStageReceipt,
    GitStageRequestBinding,
    GitStageWorktreeState,
    GitStageWorktreeStat,
)

_MAX_WORKTREE_READ_BYTES = 16 * 1024 * 1024


class GitStageUnavailableError(RuntimeError):
    """Raised when governed Git staging has no proven backend/authority."""


class GitStageUnsupportedRepositoryError(GitStageUnavailableError):
    """Raised when a repository falls outside the deliberately narrow envelope."""


@dataclass(frozen=True)
class GitStagePreparation:
    """Non-authoritative prepared state.

    This object contains only bounded metadata. It is not a permit and cannot
    be converted into mutation authority by this module.
    """

    observed: GitStageObservedState
    paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.paths or self.paths != tuple(sorted(set(self.paths))):
            raise ValueError("prepared paths must be unique and deterministic")
        observed_paths = tuple(state.path for state in self.observed.worktree_states)
        if self.paths != observed_paths:
            raise ValueError("prepared paths must exactly match observed worktree state")


@runtime_checkable
class GitStageBackend(Protocol):
    """Backend contract. Implementations must not mint or interpret permits."""

    @property
    def backend_id(self) -> str:
        ...

    def observe(self, paths: Sequence[str]) -> GitStageObservedState:
        """Observe supported repository/index/worktree state without mutation."""
        ...

    def mutation_ready(self, prepared: GitStagePreparation) -> None:
        """Revalidate all backend-owned state immediately before authority use."""
        ...

    def publish(self, prepared: GitStagePreparation) -> GitStageReceipt:
        """Publish an already-authorized index transaction.

        WO-0023 must not call this method until an explicit control-plane delta
        defines and proves the permit boundary. Backends themselves do not
        decide authorization.
        """
        ...

    def close(self) -> None:
        ...


class UnsupportedGitStageBackend:
    """Default backend: deterministic fail-closed behavior, zero mutation."""

    backend_id = "unsupported-git-stage-v1"

    def observe(self, paths: Sequence[str]) -> GitStageObservedState:
        del paths
        raise GitStageUnavailableError(
            "governed Git staging backend is not proven for this runtime"
        )

    def mutation_ready(self, prepared: GitStagePreparation) -> None:
        del prepared
        raise GitStageUnavailableError(
            "governed Git staging mutation is not authorized or proven"
        )

    def publish(self, prepared: GitStagePreparation) -> GitStageReceipt:
        del prepared
        raise GitStageUnavailableError(
            "governed Git staging mutation is not authorized or proven"
        )

    def close(self) -> None:
        return None


class GovernedGitStageAdapter:
    """Stable Hive-owned boundary around a future proven Git index backend.

    Only non-mutating preparation is exposed in this pre-authority phase.
    There is deliberately no public ``stage_paths`` method yet: adding it is an
    authority-bearing API change and therefore requires a Context Lock delta.
    """

    def __init__(self, backend: GitStageBackend | None = None) -> None:
        self._backend: GitStageBackend = backend or UnsupportedGitStageBackend()
        self._closed = False

    @property
    def backend_id(self) -> str:
        return self._backend.backend_id

    @property
    def mutation_authority_enabled(self) -> bool:
        return False

    def prepare(self, paths: Sequence[str]) -> GitStagePreparation:
        if self._closed:
            raise GitStageUnavailableError("Git staging adapter is closed")
        normalized = self._normalize_explicit_paths(paths)
        observed = self._backend.observe(normalized)
        return GitStagePreparation(observed=observed, paths=normalized)

    def close(self) -> None:
        if not self._closed:
            self._backend.close()
            self._closed = True

    @staticmethod
    def _normalize_explicit_paths(paths: Sequence[str]) -> tuple[str, ...]:
        if isinstance(paths, (str, bytes)):
            raise ValueError("paths must be an explicit sequence, not a pathspec string")
        normalized: list[str] = []
        for raw in paths:
            if not isinstance(raw, str) or not raw:
                raise ValueError("Git stage path must be a non-empty string")
            if "\x00" in raw:
                raise ValueError("Git stage path contains NUL")
            candidate = raw.replace("\\", "/")
            if candidate.startswith("/") or candidate.startswith("//"):
                raise ValueError("absolute Git stage paths are forbidden")
            parts = candidate.split("/")
            if any(part in {"", ".", ".."} for part in parts):
                raise ValueError("Git stage path traversal/ambiguous segments are forbidden")
            if parts[0].casefold() == ".git":
                raise ValueError(".git internals are not stageable workspace paths")
            # This first slice accepts literal file paths only, never Git pathspec magic.
            if any(ch in candidate for ch in "*?[") or candidate.startswith(":"):
                raise ValueError("Git pathspec/glob syntax is forbidden")
            normalized.append(candidate)
        if not normalized:
            raise ValueError("at least one explicit Git stage path is required")
        result = tuple(sorted(set(normalized)))
        if len(result) != len(normalized):
            raise ValueError("duplicate Git stage paths are forbidden")
        return result


__all__ = [
    "GitStageBackend",
    "GitStagePreparation",
    "GitStageUnavailableError",
    "GitStageUnsupportedRepositoryError",
    "GovernedGitStageAdapter",
    "GovernedGitStageCapability",
    "UnsupportedGitStageBackend",
]


class GovernedGitStageCapability:
    """Permit-gated governed Git staging capability for HCODER-WO-0023.

    The only product effect is: publish the approved content-addressed blob
    objects into the repository-local `.git/objects` store, then atomically
    publish the approved candidate index to `.git/index`. There is no generic Git
    command surface, no subprocess, no hook, no filter, no network and no
    credential path. The capability mints no approval and no permit: it consumes
    exactly one request-bound single-use permit at the final safe boundary.

    All preparation that can safely precede mutation happens in
    ``prepare_stage_request``. The owned ``.git/index.lock`` is deliberately
    acquired in ``stage_paths`` and not during preparation: holding the index lock
    across an unbounded human-approval window would block the user's own Git
    operations and manufacture a stale lock, which this Work Order forbids
    removing.
    """

    def __init__(self, workspace_root: str | os.PathLike[str], control_plane: PermissionControlPlane) -> None:
        # Lazy imports: the observer and transaction modules import this module for
        # its error types, so a module-level import here would be circular.
        from .git_stage_observer import PosixGitStageObserver

        if not isinstance(control_plane, PermissionControlPlane):
            raise TypeError("control_plane must be PermissionControlPlane")
        self._plane = control_plane
        self._observer = PosixGitStageObserver(workspace_root)
        self._lock = threading.RLock()
        self._closed = False
        self.workspace = normalize_workspace(str(self._observer.root))

    def __enter__(self) -> "GovernedGitStageCapability":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            self._closed = True

    # -- preparation ---------------------------------------------------------

    def prepare_stage_request(self, session_id: str, paths: Sequence[str]) -> ActionRequest:
        """Do all safe work and return the exact approval request. Mutates nothing."""
        from .git_loose_object_transaction import prepare_loose_blob
        from .git_object_store_inspector import inspect_local_object_store
        from .git_stage_index_codec import DulwichGitIndexCodec
        from .git_stage_plan import bind_stage_plan

        with self._lock:
            self._require_open()
            normalized = GovernedGitStageAdapter._normalize_explicit_paths(paths)
            if len(normalized) > MAX_STAGE_PATHS:
                raise ValueError("explicit Git stage paths exceed the governed ceiling")
            observed = self._observer.observe(normalized)
            prepared = self._prepare_objects(normalized, observed, prepare_loose_blob)
            plan = bind_stage_plan(GitStagePreparation(observed, normalized), tuple(item for item, _ in prepared))
            source_index = self._read_source_index(observed)
            candidate = DulwichGitIndexCodec().build_candidate(
                observed, normalized, source_index_bytes=source_index, stage_plan=plan
            )
            store = inspect_local_object_store(self._observer.root)
            binding = GitStageRequestBinding(
                observed=observed,
                path_bindings=tuple(
                    GitStagePathBinding(item.path, item.worktree_sha256, item.worktree_bytes, item.blob_oid)
                    for item in plan.paths
                ),
                candidate=GitStageIndexCandidateBinding(candidate.candidate_sha256, candidate.candidate_bytes),
                object_store=GitStageObjectStoreBinding(
                    contract=store.contract,
                    object_format=store.object_format,
                    git_dir_identity=store.git_dir_identity,
                    objects_identity=store.objects_identity,
                ),
            )
        return ActionRequest(
            session_id=str(session_id),
            capability=Capability.GIT_WRITE,
            action=GIT_STAGE_ACTION,
            target=ActionTarget(workspace=self.workspace),
            arguments=binding.arguments(),
        )

    # -- execution -----------------------------------------------------------

    def stage_paths(self, request: ActionRequest, *, permit_token: str) -> GitStageReceipt:
        """Consume the permit at the final safe boundary and publish the staged index."""
        from .git_loose_object_transaction import LooseObjectPublisher, prepare_loose_blob
        from .git_object_store_inspector import inspect_local_object_store
        from .git_stage_index_codec import DulwichGitIndexCodec, git_index_entry_oids
        from .git_stage_plan import bind_stage_plan
        from .git_stage_transaction import PosixGitIndexTransaction

        with self._lock:
            self._require_open()
            binding = self._validate_request(request)
            paths = tuple(item.path for item in binding.path_bindings)

            try:
                # 2) late observer revalidation of HEAD, source index and worktree state
                self._observer.revalidate(binding.observed)
                source_index = self._read_source_index(binding.observed)

                # Rebuild everything from live bytes and prove it reproduces the
                # approved binding exactly. Nothing is published on disagreement.
                prepared = self._prepare_objects(paths, binding.observed, prepare_loose_blob)
                approved_oids = {item.path: item.blob_oid for item in binding.path_bindings}
                for path, (item, _compressed) in zip(paths, prepared):
                    if item.candidate.oid != approved_oids[path]:
                        raise GitStageUnavailableError("blob identity changed after approval")

                # 3) late object-store revalidation
                store = inspect_local_object_store(self._observer.root)
                if (
                    store.contract != binding.object_store.contract
                    or store.object_format != binding.object_store.object_format
                    or store.git_dir_identity != binding.object_store.git_dir_identity
                    or store.objects_identity != binding.object_store.objects_identity
                ):
                    raise GitStageUnavailableError("Git object-store identity changed after approval")
                publisher = LooseObjectPublisher(self._observer.root)

                plan = bind_stage_plan(GitStagePreparation(binding.observed, paths), tuple(item for item, _ in prepared))
                candidate = DulwichGitIndexCodec().build_candidate(
                    binding.observed, paths, source_index_bytes=source_index, stage_plan=plan
                )
                if (
                    candidate.candidate_sha256 != binding.candidate.sha256
                    or candidate.candidate_bytes != binding.candidate.content_bytes
                ):
                    raise GitStageUnavailableError("rebuilt candidate index does not match the approved candidate")

                # 4) prepare and verify the owned index lock against the approved candidate
                transaction = PosixGitIndexTransaction(self._observer.git_dir)
                try:
                    transaction.acquire()
                    transaction.write_prepared_index(candidate.serialized)
                    transaction.verify_owned()

                    # 5) session and emergency state
                    self._require_active(request.session_id)

                    # 6) consume the request-bound single-use permit
                    self._plane.consume_execution_permit(permit_token, request)

                    # 7) session again, immediately after consumption
                    self._require_active(request.session_id)

                    # 8) publish required content-addressed blob objects. The
                    # session stays authoritative across a multi-object action, so
                    # it is re-checked immediately before and after each promotion.
                    for item, compressed in prepared:
                        self._require_active(request.session_id)
                        publisher.publish(item, compressed)
                        self._require_active(request.session_id)

                    # 9) last safe session/state recheck before index publication
                    self._require_active(request.session_id)
                    self._observer.revalidate(binding.observed)

                    # 10) atomic index publication
                    transaction.publish(
                        expected_sha256=binding.candidate.sha256, expected_bytes=binding.candidate.content_bytes
                    )

                    # 11) postconditions on the committed index
                    committed_oids = git_index_entry_oids(self._read_committed_index())
                    for item in binding.path_bindings:
                        if committed_oids.get(item.path) != item.blob_oid:
                            raise GitStageUnavailableError("committed index does not map an approved path to its blob")
                    staged = {item.path for item in binding.path_bindings}
                    source_oids = git_index_entry_oids(source_index) if source_index else {}
                    if {name for name in committed_oids if name not in staged} != {
                        name for name in source_oids if name not in staged
                    }:
                        raise GitStageUnavailableError("committed index changed unrelated paths")

                    # 12) success receipt only after verification
                    return GitStageReceipt(
                        workspace=self.workspace,
                        repository_identity=binding.observed.repository_identity,
                        repository_head=binding.observed.repository_head,
                        previous_index_sha256=binding.observed.index_sha256,
                        committed_index_sha256=binding.candidate.sha256,
                        staged_paths=paths,
                        committed_state="index_updated",
                    )
                finally:
                    transaction.close()
            except GitStageUnavailableError:
                raise
            except GitStageUnsupportedRepositoryError:
                raise
            except ControlPlaneError as exc:
                raise GitStageUnavailableError("control-plane authorization rejected Git staging") from exc

    # -- helpers -------------------------------------------------------------

    def _validate_request(self, request: ActionRequest) -> GitStageRequestBinding:
        try:
            capability = Capability(request.capability)
        except (TypeError, ValueError) as exc:
            raise GitStageUnsupportedRepositoryError("request capability is invalid") from exc
        if capability is not Capability.GIT_WRITE:
            raise GitStageUnsupportedRepositoryError("request capability is not git.write")
        if str(request.action).strip() != GIT_STAGE_ACTION:
            raise GitStageUnsupportedRepositoryError("request action is not the governed Git staging contract")
        if request.target.canonical().get("workspace") != self.workspace:
            raise GitStageUnsupportedRepositoryError("request workspace does not match the capability workspace")
        arguments = request.arguments
        if not isinstance(arguments, Mapping) or set(arguments) != GIT_STAGE_ARGUMENT_KEYS:
            raise GitStageUnsupportedRepositoryError("request arguments do not match the frozen git stage key set")
        if arguments.get("contract") != GIT_STAGE_CONTRACT or arguments.get("target_state") != GIT_STAGE_TARGET_STATE:
            raise GitStageUnsupportedRepositoryError("git stage contract or target state mismatch")
        if arguments.get("repository_identity") != self._observer.repository_identity:
            raise GitStageUnsupportedRepositoryError("request repository does not match the capability workspace")
        try:
            worktree_states = tuple(
                GitStageWorktreeState(
                    path=str(item["path"]),
                    file_identity=str(item["file_identity"]),
                    content_sha256=str(item["content_sha256"]),
                    content_bytes=int(item["content_bytes"]),
                    state=str(item["state"]),
                    stat=None if item.get("stat") is None else GitStageWorktreeStat(**item["stat"]),
                )
                for item in arguments["worktree_states"]  # type: ignore[union-attr]
            )
            observed = GitStageObservedState(
                repository_identity=str(arguments["repository_identity"]),
                repository_head=str(arguments["repository_head"]),
                index_state=str(arguments["index_state"]),
                index_identity=str(arguments["index_identity"]),
                index_sha256=str(arguments["index_sha256"]),
                worktree_states=worktree_states,
            )
            path_bindings = tuple(
                GitStagePathBinding(
                    path=str(item["path"]),
                    content_sha256=str(item["content_sha256"]),
                    content_bytes=int(item["content_bytes"]),
                    blob_oid=str(item["blob_oid"]),
                )
                for item in arguments["path_bindings"]  # type: ignore[union-attr]
            )
            binding = GitStageRequestBinding(
                observed=observed,
                path_bindings=path_bindings,
                candidate=GitStageIndexCandidateBinding(
                    sha256=str(arguments["candidate_index_sha256"]), content_bytes=int(arguments["candidate_index_bytes"])
                ),
                object_store=GitStageObjectStoreBinding(
                    contract=str(arguments["object_store_contract"]),
                    object_format=str(arguments["object_store_format"]),
                    git_dir_identity=str(arguments["git_dir_identity"]),
                    objects_identity=str(arguments["object_store_identity"]),
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GitStageUnsupportedRepositoryError("git stage request binding is malformed") from exc
        if int(arguments["path_count"]) != len(path_bindings):
            raise GitStageUnsupportedRepositoryError("git stage path count does not match the bindings")

        # The request carries three path representations plus a count. Contradiction
        # between them is a malformed request and must be rejected here, before any
        # permit consumption or mutation, rather than silently canonicalized.
        try:
            declared_paths = self._explicit_paths_argument(arguments["paths"])
        except ValueError as exc:
            raise GitStageUnsupportedRepositoryError("git stage declared paths are malformed") from exc
        observed_paths = tuple(state.path for state in observed.worktree_states)
        bound_paths = tuple(item.path for item in path_bindings)
        if declared_paths != observed_paths:
            raise GitStageUnsupportedRepositoryError("git stage declared paths disagree with the approved worktree state")
        if bound_paths != observed_paths:
            raise GitStageUnsupportedRepositoryError("git stage path bindings disagree with the approved worktree state")
        if int(arguments["path_count"]) != len(declared_paths):
            raise GitStageUnsupportedRepositoryError("git stage path count does not match the declared paths")
        return binding

    @staticmethod
    def _explicit_paths_argument(value: object) -> tuple[str, ...]:
        """Parse the declared paths through the same normalizer used for preparation."""
        if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
            raise ValueError("declared paths must be an explicit sequence of strings, not a pathspec string")
        return GovernedGitStageAdapter._normalize_explicit_paths(value)

    def _prepare_objects(self, paths: tuple[str, ...], observed: GitStageObservedState, prepare_loose_blob):
        prepared = []
        observed_by_path = {state.path: state for state in observed.worktree_states}
        for path in paths:
            data = self._read_worktree_file(path)
            item, compressed = prepare_loose_blob(self._observer.root, data)
            state = observed_by_path[path]
            if item.candidate.content_sha256 != state.content_sha256 or item.candidate.content_bytes != state.content_bytes:
                raise GitStageUnavailableError("worktree content no longer matches the approved state")
            prepared.append((item, compressed))
        return prepared

    def _read_source_index(self, observed: GitStageObservedState) -> bytes:
        data = self._observer.read_index_bytes()
        if observed.index_state == "absent":
            if data not in (None, b""):
                raise GitStageUnavailableError("index appeared after approval")
            return b""
        if data is None:
            raise GitStageUnavailableError("approved index disappeared")
        if hashlib.sha256(data).hexdigest() != observed.index_sha256:
            raise GitStageUnavailableError("source index bytes do not match the approved digest")
        return data

    def _read_worktree_file(self, relative: str) -> bytes:
        path = self._observer.root.joinpath(*relative.split("/"))
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise GitStageUnavailableError("approved worktree file is unreadable") from exc
        try:
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(fd, 1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > _MAX_WORKTREE_READ_BYTES:
                    raise GitStageUnavailableError("approved worktree file exceeds the governed ceiling")
                chunks.append(chunk)
            return b"".join(chunks)
        finally:
            os.close(fd)

    def _read_committed_index(self) -> bytes:
        data = self._observer.read_index_bytes()
        if data is None:
            raise GitStageUnavailableError("published index is not readable")
        return data

    def _require_active(self, session_id: str) -> None:
        if self._plane.session_state(session_id) is not SessionState.ACTIVE:
            raise GitStageUnavailableError("control session is not active")

    def _require_open(self) -> None:
        if self._closed:
            raise GitStageUnavailableError("Git staging capability is closed")
