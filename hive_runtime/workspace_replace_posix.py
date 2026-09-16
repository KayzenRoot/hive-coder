from __future__ import annotations

"""POSIX expected-state proof for HCODER-WO-0022.

Read-only revalidation is implemented. Mutation publication deliberately remains
blocked until an expected-target atomic replacement primitive is proven under a
real late race. Ordinary rename-overwrite is not accepted as CAS proof.
"""

import hashlib
import os
import stat
from typing import Callable

from .errors import WorkspaceBoundaryError
from .workspace_replace_contract import WorkspaceReplaceObservedState

_TEMP_PREFIX = ".hive-replace-"


def _digest_fd(fd: int) -> tuple[str, int]:
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
        if self._closed:
            raise WorkspaceBoundaryError("prepared replacement target is closed")
        if expected != self.observed:
            raise WorkspaceBoundaryError("approved replacement state differs from pinned target")

        self._backend._revalidate_root_path()
        if self._backend.current_parent_identity(self._parent_parts) != expected.parent_identity:
            raise WorkspaceBoundaryError("replacement parent path identity changed")
        if self._backend._dir_identity(os.fstat(self._parent_fd)) != expected.parent_identity:
            raise WorkspaceBoundaryError("pinned replacement parent identity changed")

        pinned_info = os.fstat(self._target_fd)
        if not stat.S_ISREG(pinned_info.st_mode) or _file_identity(pinned_info) != expected.target_identity:
            raise WorkspaceBoundaryError("pinned replacement target identity changed")
        pinned_digest, pinned_length = _digest_fd(self._target_fd)
        if pinned_digest != expected.content_sha256 or pinned_length != expected.content_bytes:
            raise WorkspaceBoundaryError("pinned replacement target content changed")

        live_fd: int | None = None
        try:
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            try:
                live_fd = os.open(self._leaf, flags, dir_fd=self._parent_fd)
            except OSError as exc:
                raise WorkspaceBoundaryError("replacement target pathname cannot be reopened no-follow") from exc
            live_info = os.fstat(live_fd)
            if not stat.S_ISREG(live_info.st_mode):
                raise WorkspaceBoundaryError("replacement target pathname is not a regular file")
            if _file_identity(live_info) != expected.target_identity:
                raise WorkspaceBoundaryError("replacement target pathname identity changed")
            live_digest, live_length = _digest_fd(live_fd)
            if live_digest != expected.content_sha256 or live_length != expected.content_bytes:
                raise WorkspaceBoundaryError("replacement target pathname content changed")
        finally:
            if live_fd is not None:
                os.close(live_fd)

    def publish_replace(
        self,
        content: bytes,
        expected: WorkspaceReplaceObservedState,
        pre_publish_check: Callable[[], None],
    ) -> str:
        # Critical STOP gate: validation followed by os.rename/os.replace would
        # leave a late race where another owner can replace the pathname between
        # check and overwrite. WO-0022 requires expected-target publication, not
        # best-effort validation. Keep mutation unavailable until proven.
        raise NotImplementedError("POSIX expected-target atomic replacement primitive not yet proven")

    def close(self) -> None:
        if self._closed:
            return
        os.close(self._target_fd)
        os.close(self._parent_fd)
        self._closed = True
