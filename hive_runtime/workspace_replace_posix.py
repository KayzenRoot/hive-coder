from __future__ import annotations

"""POSIX bounded-race atomic replacement for HCODER-WO-0022 / CR-001.

The adapter proves all observable approved state immediately before publication,
stages exact bytes as an identity-owned object in the pinned parent, then uses a
same-filesystem atomic rename. This is deliberately not described as strict CAS:
an uncooperative external writer may race after final revalidation and before the
native publication call where POSIX exposes no expected-destination identity predicate.
"""

import hashlib
import os
import secrets
import stat
from typing import Callable

from .errors import WorkspaceBoundaryError, WorkspaceMutationError
from .workspace_replace_contract import WorkspaceReplaceObservedState

_TEMP_PREFIX = ".hive-replace-"


def _digest_fd(fd: int) -> tuple[str, int]:
    hasher = hashlib.sha256(); total = 0; offset = 0
    while True:
        chunk = os.pread(fd, 1024 * 128, offset)
        if not chunk: break
        hasher.update(chunk); total += len(chunk); offset += len(chunk)
    return hasher.hexdigest(), total


def _file_identity(info: os.stat_result) -> str:
    return f"posix-file:{info.st_dev}:{info.st_ino}"


class PosixPreparedReplace:
    def __init__(self, backend, parent_fd: int, parent_parts: tuple[str, ...], leaf: str, target_fd: int) -> None:
        self._backend, self._parent_fd, self._parent_parts, self._leaf, self._target_fd = backend, parent_fd, parent_parts, leaf, target_fd
        self._closed = False; self._stage_fd: int | None = None; self._stage_name: str | None = None; self._stage_identity: str | None = None; self._published = False
        parent_info, target_info = os.fstat(parent_fd), os.fstat(target_fd)
        if not stat.S_ISDIR(parent_info.st_mode): raise WorkspaceBoundaryError("replacement parent is not a directory")
        if not stat.S_ISREG(target_info.st_mode): raise WorkspaceBoundaryError("replacement target is not a regular file")
        digest, length = _digest_fd(target_fd)
        self.observed = WorkspaceReplaceObservedState(backend._dir_identity(parent_info), _file_identity(target_info), digest, length)

    def revalidate_expected(self, expected: WorkspaceReplaceObservedState) -> None:
        if self._closed: raise WorkspaceBoundaryError("prepared replacement target is closed")
        if expected != self.observed: raise WorkspaceBoundaryError("approved replacement state differs from pinned target")
        self._backend._revalidate_root_path()
        if self._backend.current_parent_identity(self._parent_parts) != expected.parent_identity: raise WorkspaceBoundaryError("replacement parent path identity changed")
        if self._backend._dir_identity(os.fstat(self._parent_fd)) != expected.parent_identity: raise WorkspaceBoundaryError("pinned replacement parent identity changed")
        pinned_info = os.fstat(self._target_fd)
        if not stat.S_ISREG(pinned_info.st_mode) or _file_identity(pinned_info) != expected.target_identity: raise WorkspaceBoundaryError("pinned replacement target identity changed")
        pinned_digest, pinned_length = _digest_fd(self._target_fd)
        if pinned_digest != expected.content_sha256 or pinned_length != expected.content_bytes: raise WorkspaceBoundaryError("pinned replacement target content changed")
        live_fd: int | None = None
        try:
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            try: live_fd = os.open(self._leaf, flags, dir_fd=self._parent_fd)
            except OSError as exc: raise WorkspaceBoundaryError("replacement target pathname cannot be reopened no-follow") from exc
            live_info = os.fstat(live_fd)
            if not stat.S_ISREG(live_info.st_mode): raise WorkspaceBoundaryError("replacement target pathname is not a regular file")
            if _file_identity(live_info) != expected.target_identity: raise WorkspaceBoundaryError("replacement target pathname identity changed")
            live_digest, live_length = _digest_fd(live_fd)
            if live_digest != expected.content_sha256 or live_length != expected.content_bytes: raise WorkspaceBoundaryError("replacement target pathname content changed")
        finally:
            if live_fd is not None: os.close(live_fd)

    def stage_replace(self, content: bytes, expected: WorkspaceReplaceObservedState) -> None:
        if self._stage_fd is not None or self._stage_name is not None: raise WorkspaceBoundaryError("replacement content is already staged")
        self.revalidate_expected(expected)
        # Read-write is intentional: the capability verifies staged bytes through
        # the same pinned descriptor before that object can become mutation-ready.
        flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        for _ in range(32):
            name = f"{_TEMP_PREFIX}{secrets.token_hex(16)}"
            try: fd = os.open(name, flags, 0o600, dir_fd=self._parent_fd)
            except FileExistsError: continue
            except OSError as exc: raise WorkspaceMutationError("replacement staging object cannot be created") from exc
            self._stage_fd, self._stage_name = fd, name; break
        else: raise WorkspaceMutationError("replacement staging namespace exhausted")
        try:
            view = memoryview(content); offset = 0
            while offset < len(view):
                written = os.write(self._stage_fd, view[offset:])
                if written <= 0: raise WorkspaceMutationError("replacement staging write made no progress")
                offset += written
            os.fsync(self._stage_fd)
            info = os.fstat(self._stage_fd)
            if not stat.S_ISREG(info.st_mode): raise WorkspaceBoundaryError("replacement staging object is not regular")
            self._stage_identity = _file_identity(info)
            digest, length = _digest_fd(self._stage_fd); wanted_digest = hashlib.sha256(content).hexdigest()
            if digest != wanted_digest or length != len(content): raise WorkspaceMutationError("replacement staging bytes failed verification")
            if info.st_dev != os.fstat(self._target_fd).st_dev: raise WorkspaceBoundaryError("replacement staging object is not on target filesystem")
        except Exception:
            self._cleanup_stage(); raise

    def mutation_ready(self, expected: WorkspaceReplaceObservedState) -> None:
        if self._stage_fd is None or self._stage_name is None or self._stage_identity is None: raise NotImplementedError("POSIX replacement publication has no verified staged object")
        stage_info = os.fstat(self._stage_fd)
        if not stat.S_ISREG(stage_info.st_mode) or _file_identity(stage_info) != self._stage_identity: raise WorkspaceBoundaryError("replacement staging identity changed")
        self.revalidate_expected(expected)

    def publish_replace(self, expected: WorkspaceReplaceObservedState, pre_publish_check: Callable[[], None]) -> str:
        if self._stage_fd is None or self._stage_name is None or self._stage_identity is None: raise WorkspaceBoundaryError("replacement staging object is not mutation-ready")
        pre_publish_check(); stage_info = os.fstat(self._stage_fd)
        if _file_identity(stage_info) != self._stage_identity or not stat.S_ISREG(stage_info.st_mode): raise WorkspaceBoundaryError("replacement staging identity changed before publication")
        try: os.rename(self._stage_name, self._leaf, src_dir_fd=self._parent_fd, dst_dir_fd=self._parent_fd)
        except OSError as exc: raise WorkspaceMutationError("POSIX atomic replacement publication failed") from exc
        self._published = True; self._stage_name = None
        live_fd: int | None = None
        try:
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0); live_fd = os.open(self._leaf, flags, dir_fd=self._parent_fd)
            info = os.fstat(live_fd)
            if not stat.S_ISREG(info.st_mode) or _file_identity(info) != self._stage_identity: raise WorkspaceMutationError("published replacement identity verification failed")
            digest, length = _digest_fd(live_fd); stage_digest, stage_length = _digest_fd(self._stage_fd)
            if digest != stage_digest or length != stage_length: raise WorkspaceMutationError("published replacement bytes verification failed")
            return "replaced"
        finally:
            if live_fd is not None: os.close(live_fd)

    def _cleanup_stage(self) -> None:
        if self._stage_name is None: return
        try: live_fd = os.open(self._stage_name, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0), dir_fd=self._parent_fd)
        except OSError: self._stage_name = None; return
        try: live_identity = _file_identity(os.fstat(live_fd))
        finally: os.close(live_fd)
        if self._stage_identity is not None and live_identity != self._stage_identity: self._stage_name = None; return
        try: os.unlink(self._stage_name, dir_fd=self._parent_fd)
        except FileNotFoundError: pass
        finally: self._stage_name = None

    def close(self) -> None:
        if self._closed: return
        if not self._published: self._cleanup_stage()
        if self._stage_fd is not None: os.close(self._stage_fd); self._stage_fd = None
        os.close(self._target_fd); os.close(self._parent_fd); self._closed = True
