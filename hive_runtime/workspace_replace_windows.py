from __future__ import annotations

"""Windows replacement seam for HCODER-WO-0022 / CR-001.

Windows support is deliberately fail-closed until the handle-pinned implementation
proves the same bounded-race contract already implemented on POSIX. The contract
requires latest observable target revalidation, verified same-volume staging and
an atomic native publication. It does NOT claim strict expected-file-id CAS across
an uncooperative external writer in the final native-call interval.
"""

from typing import Callable

from .workspace_replace_contract import WorkspaceReplaceObservedState

_TEMP_PREFIX = ".hive-replace-"


class WindowsPreparedReplace:
    """Pinned Windows replacement candidate.

    Native implementation requirements:
    * traverse from the canonical root with NtCreateFile relative handles;
    * use FILE_OPEN_REPARSE_POINT and reject reparse/non-regular components;
    * bind volume/file-id identity and SHA-256/length read from a pinned target handle;
    * re-open the live pathname handle-relative before publication and compare exact
      identity + approved old content;
    * stage exact approved bytes in an exclusive capability-owned regular file on
      the same volume, flush and verify its identity/digest/length;
    * expose mutation_ready only after publication is objectively available;
    * consume no permit merely to discover this adapter is unavailable;
    * perform latest revalidation immediately before the native atomic replacement;
    * cleanup only an unpublished staging object whose file identity is still owned.

    `MoveFileEx`, `ReplaceFile` or an NT rename may be selected only as the atomic
    publication primitive for CR-001 after native evidence. None may be described
    as strict CAS because they expose no approved-destination file-id predicate.
    """

    def __init__(self, *, observed: WorkspaceReplaceObservedState) -> None:
        self.observed = observed
        self._closed = False

    def revalidate_expected(self, expected: WorkspaceReplaceObservedState) -> None:
        raise NotImplementedError("HCODER-WO-0022 Windows live expected-state revalidation is not yet proven")

    def stage_replace(self, content: bytes, expected: WorkspaceReplaceObservedState) -> None:
        raise NotImplementedError("HCODER-WO-0022 Windows verified same-volume staging is not yet proven")

    def mutation_ready(self, expected: WorkspaceReplaceObservedState) -> None:
        raise NotImplementedError("HCODER-WO-0022 Windows atomic publication is not yet proven")

    def publish_replace(
        self,
        expected: WorkspaceReplaceObservedState,
        pre_publish_check: Callable[[], None],
    ) -> str:
        raise NotImplementedError("HCODER-WO-0022 Windows replacement remains fail-closed pending native proof")

    def close(self) -> None:
        self._closed = True
