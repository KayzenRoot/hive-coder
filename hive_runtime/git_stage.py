from __future__ import annotations

"""Governed Git staging adapter boundary for HCODER-WO-0023.

This module is intentionally non-mutating until a backend is proven and the
Permission & Control Plane receives an explicit Context Lock delta.  Keeping
this adapter importable now lets contract/security tests target stable symbols
without accidentally granting repository mutation authority.
"""

from dataclasses import dataclass
from typing import Protocol, Sequence, runtime_checkable

from .git_stage_contract import GitStageObservedState, GitStageReceipt


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
    "UnsupportedGitStageBackend",
]
