from __future__ import annotations

"""Protocol seam for HCODER-WO-0022 / CR-001 replacement backends.

Authority does not live here. The seam separates read-only observation/revalidation
from platform staging and the final mutation-ready atomic publication boundary.
"""

from typing import Callable, Protocol

from .workspace_replace_contract import WorkspaceReplaceObservedState


class PreparedReplace(Protocol):
    @property
    def observed(self) -> WorkspaceReplaceObservedState: ...

    def revalidate_expected(self, expected: WorkspaceReplaceObservedState) -> None:
        """Fail closed unless all currently observable state equals the approved state."""
        ...

    def stage_replace(self, content: bytes, expected: WorkspaceReplaceObservedState) -> None:
        """Create and verify an identity-owned same-filesystem replacement object.

        This method must not mutate the approved destination pathname and must not
        consume authority. Failure leaves the destination unchanged.
        """
        ...

    def mutation_ready(self, expected: WorkspaceReplaceObservedState) -> None:
        """Fail closed unless a verified staged object and live destination are ready.

        This is the final read-only gate before the caller consumes a permit.
        Implementations must raise NotImplementedError/WorkspaceBoundaryError before
        permit consumption when publication is unavailable or unsupported.
        """
        ...

    def publish_replace(
        self,
        expected: WorkspaceReplaceObservedState,
        pre_publish_check: Callable[[], None],
    ) -> str:
        """Atomically publish the already-verified staged object.

        CR-001 does not claim strict expected-inode CAS across an uncooperative
        external writer acting after the last successful revalidation.
        """
        ...

    def close(self) -> None:
        """Close handles and remove only identity-owned unpublished staging state."""
        ...


class ReplaceBackend(Protocol):
    canonical_root: str

    def prepare_replace(self, relative_path: str) -> PreparedReplace:
        """Open/pin an existing regular target without following links/reparse points."""
        ...
