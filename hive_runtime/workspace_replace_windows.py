from __future__ import annotations

"""Windows implementation skeleton for HCODER-WO-0022.

The existing WO-0021 backend already proves handle-relative NT opens and
no-clobber create publication. Replacement requires a stronger expected-target
proof. Do not replace this skeleton with MoveFileEx/ReplaceFile/path-only logic
unless real race tests prove the exact Hive CAS contract.
"""

from typing import Callable

from .workspace_replace_contract import WorkspaceReplaceObservedState

_TEMP_PREFIX = ".hive-replace-"


class WindowsPreparedReplace:
    """Pinned Windows replacement candidate.

    Executor requirements:
    * traverse from the canonical root with NtCreateFile relative handles;
    * FILE_OPEN_REPARSE_POINT for parent and target surfaces;
    * reject any reparse-point component and non-regular target;
    * bind volume/file-id identity and digest bytes read from the pinned handle;
    * re-open the live pathname handle-relative before commit and compare exact
      identity + content state;
    * publish through a native primitive that can prove expected-target
      semantics under a real concurrent replacement race;
    * cleanup only a temp object whose file identity is still capability-owned.
    """

    def __init__(self, *, observed: WorkspaceReplaceObservedState) -> None:
        self.observed = observed
        self._closed = False

    def revalidate_expected(self, expected: WorkspaceReplaceObservedState) -> None:
        raise NotImplementedError("HCODER-WO-0022 executor must prove Windows live expected-target revalidation")

    def publish_replace(
        self,
        content: bytes,
        expected: WorkspaceReplaceObservedState,
        pre_publish_check: Callable[[], None],
    ) -> str:
        raise NotImplementedError("HCODER-WO-0022 forbids unproven Windows overwrite fallback")

    def close(self) -> None:
        self._closed = True
