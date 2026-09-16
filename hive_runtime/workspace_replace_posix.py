from __future__ import annotations

"""POSIX implementation skeleton for HCODER-WO-0022.

This file deliberately contains the native-proof plan but no mutation fallback.
The executor must complete the handle-relative CAS publication or fail closed.
"""

import hashlib
import os
import stat
from typing import Callable

from .errors import WorkspaceBoundaryError
from .workspace_replace_contract import WorkspaceReplaceObservedState

_TEMP_PREFIX = ".hive-replace-"


def _digest_fd(fd: int) -> tuple[str, int]:
    """Digest a pinned regular-file descriptor without path re-resolution."""
    hasher = hashlib.sha256()
    total = 0
    offset = 0
    while True:
        chunk = os.pread(fd, 1024 * 128, offset)
        if not chunk:
            break
        hasher.update(chunk)
        total += len(chunk)
        offset += len(chunk)
    return hasher.hexdigest(), total


def _file_identity(info: os.stat_result) -> str:
    return f"posix-file:{info.st_dev}:{info.st_ino}"


class PosixPreparedReplace:
    """Pinned-parent + pinned-target replacement candidate.

    Required implementation invariants:
    * parent traversal uses dir_fd + O_DIRECTORY + O_NOFOLLOW;
    * target opens O_NOFOLLOW and must be S_ISREG;
    * observed digest is read from the pinned target fd;
    * revalidation proves root, parent pathname, target pathname identity and
      pinned-target digest/length still match the approved state;
    * publication uses a same-parent private temp with identity-owned cleanup;
    * an ordinary overwrite rename is NOT sufficient if a concurrent owner can
      replace the target between final validation and commit.
    """

    def __init__(self, backend, parent_fd: int, parent_parts: tuple[str, ...], leaf: str, target_fd: int) -> None:
        self._backend = backend
        self._parent_fd = parent_fd
        self._parent_parts = parent_parts
        self._leaf = leaf
        self._target_fd = target_fd
        self._closed = False
        parent_info = os.fstat(parent_fd)
        target_info = os.fstat(target_fd)
        if not stat.S_ISDIR(parent_info.st_mode):
            raise WorkspaceBoundaryError("replacement parent is not a directory")
        if not stat.S_ISREG(target_info.st_mode):
            raise WorkspaceBoundaryError("replacement target is not a regular file")
        digest, length = _digest_fd(target_fd)
        self.observed = WorkspaceReplaceObservedState(
            parent_identity=backend._dir_identity(parent_info),
            target_identity=_file_identity(target_info),
            content_sha256=digest,
            content_bytes=length,
        )

    def revalidate_expected(self, expected: WorkspaceReplaceObservedState) -> None:
        raise NotImplementedError("HCODER-WO-0022 executor must prove POSIX live expected-target revalidation")

    def publish_replace(
        self,
        content: bytes,
        expected: WorkspaceReplaceObservedState,
        pre_publish_check: Callable[[], None],
    ) -> str:
        raise NotImplementedError("HCODER-WO-0022 forbids unproven POSIX overwrite fallback")

    def close(self) -> None:
        if self._closed:
            return
        os.close(self._target_fd)
        os.close(self._parent_fd)
        self._closed = True
