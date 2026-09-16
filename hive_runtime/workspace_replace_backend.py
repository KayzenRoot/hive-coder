from __future__ import annotations

"""Protocol-only seam for HCODER-WO-0022 replacement backends.

No implementation and no authority live here. The seam lets POSIX and Windows
prove the same Hive contract with platform-specific native primitives.
"""

from typing import Callable, Protocol

from .workspace_replace_contract import WorkspaceReplaceObservedState


class PreparedReplace(Protocol):
    @property
    def observed(self) -> WorkspaceReplaceObservedState: ...

    def revalidate_expected(self, expected: WorkspaceReplaceObservedState) -> None:
        """Fail closed unless the live target still equals the approved state."""
        ...

    def publish_replace(
        self,
        content: bytes,
        expected: WorkspaceReplaceObservedState,
        pre_publish_check: Callable[[], None],
    ) -> str:
        """Publish only if the expected target still owns the approved pathname."""
        ...

    def close(self) -> None: ...


class ReplaceBackend(Protocol):
    canonical_root: str

    def prepare_replace(self, relative_path: str) -> PreparedReplace:
        """Open/pin an existing regular target without following links/reparse points."""
        ...
