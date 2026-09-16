from __future__ import annotations

"""Windows replacement backend for HCODER-WO-0022 / CR-001.

This increment proves handle-relative traversal, no-reparse target observation and
exact old-byte binding on Windows. Publication remains fail-closed until the next
native increment proves verified staging and atomic replacement on the Windows CI
runner. No strict expected-file-id CAS claim is made.
"""

import ctypes
import hashlib
from ctypes import wintypes
from typing import Callable

from .errors import WorkspaceBoundaryError, WorkspaceMutationError
from .workspace_replace_contract import WorkspaceReplaceObservedState
from .workspace_files_windows import (
    WindowsWorkspaceBackend,
    _FILE_ATTRIBUTE_DIRECTORY,
    _FILE_ATTRIBUTE_REPARSE_POINT,
    _FILE_NON_DIRECTORY_FILE,
    _FILE_OPEN,
    _FILE_OPEN_REPARSE_POINT,
    _FILE_READ_ATTRIBUTES,
    _FILE_READ_DATA,
    _FILE_SHARE_READ,
    _FILE_SHARE_WRITE,
    _FILE_SYNCHRONOUS_IO_NONALERT,
    _SYNCHRONIZE,
    _nt_open_relative,
    _win_close,
    _win_file_identity,
    _win_info,
)

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_ReadFile = _kernel32.ReadFile
_ReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
_ReadFile.restype = wintypes.BOOL
_SetFilePointerEx = _kernel32.SetFilePointerEx
_SetFilePointerEx.argtypes = [wintypes.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD]
_SetFilePointerEx.restype = wintypes.BOOL
_FILE_BEGIN = 0
_TEMP_PREFIX = ".hive-replace-"


def _read_handle_bytes(handle: int) -> bytes:
    if not _SetFilePointerEx(wintypes.HANDLE(handle), 0, None, _FILE_BEGIN):
        raise WorkspaceMutationError(f"SetFilePointerEx failed (winerror={ctypes.get_last_error()})")
    chunks: list[bytes] = []
    while True:
        buffer = ctypes.create_string_buffer(128 * 1024)
        read = wintypes.DWORD()
        if not _ReadFile(wintypes.HANDLE(handle), buffer, len(buffer), ctypes.byref(read), None):
            raise WorkspaceMutationError(f"ReadFile failed (winerror={ctypes.get_last_error()})")
        if read.value == 0:
            break
        chunks.append(buffer.raw[: read.value])
    return b"".join(chunks)


def _observed(parent_handle: int, target_handle: int) -> WorkspaceReplaceObservedState:
    parent_info = _win_info(parent_handle); target_info = _win_info(target_handle)
    if parent_info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT or not parent_info.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY:
        raise WorkspaceBoundaryError("replacement parent is not a pinned regular directory")
    if target_info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY):
        raise WorkspaceBoundaryError("replacement target is not a regular no-reparse file")
    data = _read_handle_bytes(target_handle)
    return WorkspaceReplaceObservedState(_win_file_identity(parent_info), _win_file_identity(target_info), hashlib.sha256(data).hexdigest(), len(data))


class WindowsReplaceWorkspaceBackend(WindowsWorkspaceBackend):
    def prepare_replace(self, relative_path: str) -> "WindowsPreparedReplace":
        if self._closed:
            raise WorkspaceBoundaryError("workspace backend is closed")
        self._revalidate_root_path()
        parts = relative_path.split("/"); chain: list[int] = []; parent = self._root_handle; parent_parts: list[str] = []
        try:
            for component in parts[:-1]:
                child = _nt_open_relative(parent, component, desired_access=0x00000001 | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE, disposition=_FILE_OPEN, options=0x00000001 | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT)
                info = _win_info(child)
                if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                    _win_close(child); raise WorkspaceBoundaryError("replacement parent component is a reparse point")
                if not info.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY:
                    _win_close(child); raise WorkspaceBoundaryError("replacement parent component is not a directory")
                chain.append(child); parent = child; parent_parts.append(component)
            target = _nt_open_relative(parent, parts[-1], desired_access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE, disposition=_FILE_OPEN, options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT)
            try:
                observed = _observed(parent, target)
                return WindowsPreparedReplace(self, chain, parent, tuple(parent_parts), parts[-1], target, observed)
            except Exception:
                _win_close(target); raise
        except Exception:
            for item in reversed(chain): _win_close(item)
            raise


class WindowsPreparedReplace:
    def __init__(self, backend: WindowsReplaceWorkspaceBackend, chain: list[int], parent_handle: int, parent_parts: tuple[str, ...], leaf: str, target_handle: int, observed: WorkspaceReplaceObservedState) -> None:
        self._backend, self._chain, self._parent_handle, self._parent_parts, self._leaf, self._target_handle = backend, chain, parent_handle, parent_parts, leaf, target_handle
        self.observed = observed; self._closed = False

    def revalidate_expected(self, expected: WorkspaceReplaceObservedState) -> None:
        if self._closed: raise WorkspaceBoundaryError("prepared Windows replacement is closed")
        if expected != self.observed: raise WorkspaceBoundaryError("approved Windows replacement state differs from pinned observation")
        self._backend._revalidate_root_path()
        if self._backend.current_parent_identity(self._parent_parts) != expected.parent_identity: raise WorkspaceBoundaryError("Windows replacement parent path identity changed")
        if _win_file_identity(_win_info(self._parent_handle)) != expected.parent_identity: raise WorkspaceBoundaryError("pinned Windows replacement parent identity changed")
        pinned = _observed(self._parent_handle, self._target_handle)
        if pinned.target_identity != expected.target_identity or pinned.content_sha256 != expected.content_sha256 or pinned.content_bytes != expected.content_bytes: raise WorkspaceBoundaryError("pinned Windows replacement target changed")
        live: int | None = None
        try:
            live = _nt_open_relative(self._parent_handle, self._leaf, desired_access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE, disposition=_FILE_OPEN, options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT)
            current = _observed(self._parent_handle, live)
            if current.target_identity != expected.target_identity or current.content_sha256 != expected.content_sha256 or current.content_bytes != expected.content_bytes: raise WorkspaceBoundaryError("live Windows replacement target changed")
        finally: _win_close(live)

    def stage_replace(self, content: bytes, expected: WorkspaceReplaceObservedState) -> None:
        self.revalidate_expected(expected)
        raise NotImplementedError("HCODER-WO-0022 Windows verified same-volume staging is the next native proof")

    def mutation_ready(self, expected: WorkspaceReplaceObservedState) -> None:
        raise NotImplementedError("HCODER-WO-0022 Windows atomic publication is not yet proven")

    def publish_replace(self, expected: WorkspaceReplaceObservedState, pre_publish_check: Callable[[], None]) -> str:
        raise NotImplementedError("HCODER-WO-0022 Windows replacement remains fail-closed pending staging/publication proof")

    def close(self) -> None:
        if self._closed: return
        _win_close(self._target_handle)
        for handle in reversed(self._chain): _win_close(handle)
        self._closed = True
