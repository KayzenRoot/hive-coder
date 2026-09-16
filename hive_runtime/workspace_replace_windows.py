from __future__ import annotations

"""Windows bounded-race atomic replacement backend for HCODER-WO-0022 / CR-001.

Approval binds the observed destination identity/content and exact new bytes. The
backend revalidates both destination and owned staging as late as safely possible,
then performs a name-based NT atomic replacement. This is deliberately NOT called
strict expected-file-id CAS: an uncooperative external process can still race after
the final validation and before NtSetInformationFile publishes the staged object.
"""

import ctypes
import hashlib
import secrets
from ctypes import wintypes
from typing import Callable

from .errors import WorkspaceBoundaryError, WorkspaceMutationError
from .workspace_replace_contract import WorkspaceReplaceObservedState
from .workspace_files_windows import (
    WindowsWorkspaceBackend, _FILE_ATTRIBUTE_DIRECTORY, _FILE_ATTRIBUTE_REPARSE_POINT,
    _FILE_ATTRIBUTE_TEMPORARY, _FILE_CREATE, _FILE_NON_DIRECTORY_FILE, _FILE_OPEN,
    _FILE_OPEN_REPARSE_POINT, _FILE_READ_ATTRIBUTES, _FILE_READ_DATA, _FILE_SHARE_READ,
    _FILE_SHARE_WRITE, _FILE_SHARE_DELETE, _FILE_SYNCHRONOUS_IO_NONALERT,
    _FILE_WRITE_ATTRIBUTES, _FILE_WRITE_DATA, _SYNCHRONIZE, _DELETE, _FlushFileBuffers,
    _WriteFile, _nt_mark_delete, _nt_open_relative, _nt_rename_relative_replace,
    _win_close, _win_file_identity, _win_info,
)

_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_ReadFile = _kernel32.ReadFile
_ReadFile.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]; _ReadFile.restype = wintypes.BOOL
_SetFilePointerEx = _kernel32.SetFilePointerEx
_SetFilePointerEx.argtypes = [wintypes.HANDLE, ctypes.c_longlong, ctypes.POINTER(ctypes.c_longlong), wintypes.DWORD]; _SetFilePointerEx.restype = wintypes.BOOL
_FILE_BEGIN = 0
_TEMP_PREFIX = ".hive-replace-"


def _read_handle_bytes(handle: int) -> bytes:
    if not _SetFilePointerEx(wintypes.HANDLE(handle), 0, None, _FILE_BEGIN): raise WorkspaceMutationError(f"SetFilePointerEx failed (winerror={ctypes.get_last_error()})")
    chunks: list[bytes] = []
    while True:
        buffer = ctypes.create_string_buffer(128 * 1024); read = wintypes.DWORD()
        if not _ReadFile(wintypes.HANDLE(handle), buffer, len(buffer), ctypes.byref(read), None): raise WorkspaceMutationError(f"ReadFile failed (winerror={ctypes.get_last_error()})")
        if read.value == 0: break
        chunks.append(buffer.raw[: read.value])
    return b"".join(chunks)


def _write_handle_bytes(handle: int, content: bytes) -> None:
    if not _SetFilePointerEx(wintypes.HANDLE(handle), 0, None, _FILE_BEGIN): raise WorkspaceMutationError(f"SetFilePointerEx failed before staging write (winerror={ctypes.get_last_error()})")
    if content:
        buffer = ctypes.create_string_buffer(content); offset = 0
        while offset < len(content):
            chunk = min(len(content) - offset, 1 << 20); written = wintypes.DWORD(); pointer = ctypes.cast(ctypes.byref(buffer, offset), wintypes.LPCVOID)
            if not _WriteFile(wintypes.HANDLE(handle), pointer, chunk, ctypes.byref(written), None): raise WorkspaceMutationError(f"WriteFile failed for replacement staging (winerror={ctypes.get_last_error()})")
            if written.value <= 0: raise WorkspaceMutationError("short Windows replacement staging write")
            offset += int(written.value)
    if not _FlushFileBuffers(wintypes.HANDLE(handle)): raise WorkspaceMutationError(f"FlushFileBuffers failed for replacement staging (winerror={ctypes.get_last_error()})")


def _observed(parent_handle: int, target_handle: int) -> WorkspaceReplaceObservedState:
    parent_info = _win_info(parent_handle); target_info = _win_info(target_handle)
    if parent_info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT or not parent_info.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY: raise WorkspaceBoundaryError("replacement parent is not a pinned regular directory")
    if target_info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY): raise WorkspaceBoundaryError("replacement target is not a regular no-reparse file")
    data = _read_handle_bytes(target_handle)
    return WorkspaceReplaceObservedState(_win_file_identity(parent_info), _win_file_identity(target_info), hashlib.sha256(data).hexdigest(), len(data))


class WindowsReplaceWorkspaceBackend(WindowsWorkspaceBackend):
    def prepare_replace(self, relative_path: str) -> "WindowsPreparedReplace":
        if self._closed: raise WorkspaceBoundaryError("workspace backend is closed")
        self._revalidate_root_path(); parts = relative_path.split("/"); chain: list[int] = []; parent = self._root_handle; parent_parts: list[str] = []
        try:
            for component in parts[:-1]:
                child = _nt_open_relative(parent, component, desired_access=0x00000001 | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE, disposition=_FILE_OPEN, options=0x00000001 | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT)
                info = _win_info(child)
                if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT: _win_close(child); raise WorkspaceBoundaryError("replacement parent component is a reparse point")
                if not info.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY: _win_close(child); raise WorkspaceBoundaryError("replacement parent component is not a directory")
                chain.append(child); parent = child; parent_parts.append(component)
            # DELETE is required on the pinned destination handle for NTFS replacement
            # semantics. FILE_SHARE_DELETE keeps external/cooperative handles from
            # turning that requirement into a sharing violation. This grants no new
            # path authority: the handle is still opened relative to the pinned parent.
            target = _nt_open_relative(parent, parts[-1], desired_access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _DELETE | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE, disposition=_FILE_OPEN, options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT)
            try: return WindowsPreparedReplace(self, chain, parent, tuple(parent_parts), parts[-1], target, _observed(parent, target))
            except Exception: _win_close(target); raise
        except Exception:
            for item in reversed(chain): _win_close(item)
            raise


class WindowsPreparedReplace:
    def __init__(self, backend: WindowsReplaceWorkspaceBackend, chain: list[int], parent_handle: int, parent_parts: tuple[str, ...], leaf: str, target_handle: int, observed: WorkspaceReplaceObservedState) -> None:
        self._backend, self._chain, self._parent_handle, self._parent_parts, self._leaf, self._target_handle = backend, chain, parent_handle, parent_parts, leaf, target_handle
        self.observed = observed; self._closed = False; self._stage_handle: int | None = None; self._stage_name: str | None = None; self._stage_identity: str | None = None; self._stage_digest: str | None = None; self._stage_bytes: int | None = None; self._published = False

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
            # The live-path proof also requests DELETE so it proves the currently
            # named destination is replaceable under the same access contract.
            live = _nt_open_relative(self._parent_handle, self._leaf, desired_access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _DELETE | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE, disposition=_FILE_OPEN, options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT)
            current = _observed(self._parent_handle, live)
            if current.target_identity != expected.target_identity or current.content_sha256 != expected.content_sha256 or current.content_bytes != expected.content_bytes: raise WorkspaceBoundaryError("live Windows replacement target changed")
        finally: _win_close(live)

    def _revalidate_stage(self) -> None:
        if self._stage_handle is None or self._stage_name is None or self._stage_identity is None or self._stage_digest is None or self._stage_bytes is None: raise WorkspaceBoundaryError("Windows replacement staging is not complete")
        info = _win_info(self._stage_handle)
        if info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY) or _win_file_identity(info) != self._stage_identity: raise WorkspaceBoundaryError("pinned Windows replacement staging identity changed")
        pinned = _read_handle_bytes(self._stage_handle)
        if hashlib.sha256(pinned).hexdigest() != self._stage_digest or len(pinned) != self._stage_bytes: raise WorkspaceBoundaryError("pinned Windows replacement staging bytes changed")
        live: int | None = None
        try:
            live = _nt_open_relative(self._parent_handle, self._stage_name, desired_access=_FILE_READ_DATA | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE, disposition=_FILE_OPEN, options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT)
            live_info = _win_info(live)
            if live_info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY) or _win_file_identity(live_info) != self._stage_identity: raise WorkspaceBoundaryError("live Windows replacement staging pathname identity changed")
            data = _read_handle_bytes(live)
            if hashlib.sha256(data).hexdigest() != self._stage_digest or len(data) != self._stage_bytes: raise WorkspaceBoundaryError("live Windows replacement staging pathname bytes changed")
        finally: _win_close(live)

    def stage_replace(self, content: bytes, expected: WorkspaceReplaceObservedState) -> None:
        if self._stage_handle is not None: raise WorkspaceBoundaryError("Windows replacement staging already exists")
        self.revalidate_expected(expected); name = f"{_TEMP_PREFIX}{secrets.token_hex(16)}.tmp"
        handle = _nt_open_relative(self._parent_handle, name, desired_access=_FILE_READ_DATA | _FILE_WRITE_DATA | _FILE_READ_ATTRIBUTES | _FILE_WRITE_ATTRIBUTES | _DELETE | _SYNCHRONIZE, share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE | _FILE_SHARE_DELETE, disposition=_FILE_CREATE, options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT, file_attributes=_FILE_ATTRIBUTE_TEMPORARY)
        try:
            info = _win_info(handle)
            if info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY): raise WorkspaceBoundaryError("Windows replacement staging object is not a regular file")
            self._stage_handle, self._stage_name, self._stage_identity = handle, name, _win_file_identity(info); _write_handle_bytes(handle, content); data = _read_handle_bytes(handle); digest = hashlib.sha256(data).hexdigest()
            if data != content: raise WorkspaceMutationError("Windows replacement staging verification mismatch")
            self._stage_digest, self._stage_bytes = digest, len(data); self._revalidate_stage(); self.revalidate_expected(expected)
        except Exception:
            if self._stage_handle is None: _win_close(handle)
            raise

    def mutation_ready(self, expected: WorkspaceReplaceObservedState) -> None:
        self.revalidate_expected(expected); self._revalidate_stage()

    def publish_replace(self, expected: WorkspaceReplaceObservedState, pre_publish_check: Callable[[], None]) -> str:
        if self._closed or self._stage_handle is None or self._stage_identity is None or self._stage_digest is None or self._stage_bytes is None: raise WorkspaceBoundaryError("Windows replacement is not staged")
        pre_publish_check(); self.revalidate_expected(expected); self._revalidate_stage()
        _nt_rename_relative_replace(self._stage_handle, self._parent_handle, self._leaf); self._published = True
        final_info = _win_info(self._stage_handle)
        if final_info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY) or _win_file_identity(final_info) != self._stage_identity: raise WorkspaceMutationError("published Windows replacement identity differs from verified stage")
        final_data = _read_handle_bytes(self._stage_handle)
        if hashlib.sha256(final_data).hexdigest() != self._stage_digest or len(final_data) != self._stage_bytes: raise WorkspaceMutationError("published Windows replacement bytes differ from verified stage")
        return self._stage_identity

    def close(self) -> None:
        if self._closed: return
        if self._stage_handle is not None:
            if not self._published and self._stage_identity is not None:
                try:
                    if _win_file_identity(_win_info(self._stage_handle)) == self._stage_identity: _nt_mark_delete(self._stage_handle)
                except Exception: pass
            _win_close(self._stage_handle); self._stage_handle = None
        _win_close(self._target_handle)
        for handle in reversed(self._chain): _win_close(handle)
        self._closed = True
