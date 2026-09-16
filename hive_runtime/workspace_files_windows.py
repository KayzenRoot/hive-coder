from __future__ import annotations

import ctypes
import os
import secrets
from ctypes import wintypes
from typing import Callable

from .errors import WorkspaceBoundaryError, WorkspaceMutationError

_TEMP_PREFIX = ".hive-create-"

_NTSTATUS = ctypes.c_long
_ULONG_PTR = ctypes.c_size_t
_OBJ_CASE_INSENSITIVE = 0x00000040
_FILE_OPEN = 0x00000001
_FILE_CREATE = 0x00000002
_FILE_DIRECTORY_FILE = 0x00000001
_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
_FILE_NON_DIRECTORY_FILE = 0x00000040
_FILE_OPEN_REPARSE_POINT = 0x00200000
_FILE_LIST_DIRECTORY = 0x00000001
_FILE_READ_DATA = 0x00000001
_FILE_WRITE_DATA = 0x00000002
_FILE_READ_ATTRIBUTES = 0x00000080
_FILE_WRITE_ATTRIBUTES = 0x00000100
_DELETE = 0x00010000
_SYNCHRONIZE = 0x00100000
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_OPEN_EXISTING = 3
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_ATTRIBUTE_DIRECTORY = 0x00000010
_FILE_ATTRIBUTE_TEMPORARY = 0x00000100
_INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
_STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034
_STATUS_OBJECT_PATH_NOT_FOUND = 0xC000003A
_STATUS_OBJECT_NAME_COLLISION = 0xC0000035
_FILE_RENAME_INFORMATION_CLASS = 10
_FILE_DISPOSITION_INFORMATION_CLASS = 13


class _UNICODE_STRING(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.USHORT),
        ("MaximumLength", wintypes.USHORT),
        ("Buffer", wintypes.LPWSTR),
    ]


class _OBJECT_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.ULONG),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.POINTER(_UNICODE_STRING)),
        ("Attributes", wintypes.ULONG),
        ("SecurityDescriptor", wintypes.LPVOID),
        ("SecurityQualityOfService", wintypes.LPVOID),
    ]


class _IO_STATUS_UNION(ctypes.Union):
    _fields_ = [("Status", _NTSTATUS), ("Pointer", wintypes.LPVOID)]


class _IO_STATUS_BLOCK(ctypes.Structure):
    _fields_ = [("u", _IO_STATUS_UNION), ("Information", _ULONG_PTR)]


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("dwFileAttributes", wintypes.DWORD),
        ("ftCreationTime", wintypes.FILETIME),
        ("ftLastAccessTime", wintypes.FILETIME),
        ("ftLastWriteTime", wintypes.FILETIME),
        ("dwVolumeSerialNumber", wintypes.DWORD),
        ("nFileSizeHigh", wintypes.DWORD),
        ("nFileSizeLow", wintypes.DWORD),
        ("nNumberOfLinks", wintypes.DWORD),
        ("nFileIndexHigh", wintypes.DWORD),
        ("nFileIndexLow", wintypes.DWORD),
    ]


class _RENAME_UNION(ctypes.Union):
    _fields_ = [("ReplaceIfExists", ctypes.c_ubyte), ("Flags", wintypes.ULONG)]


class _FILE_RENAME_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("u", _RENAME_UNION),
        ("RootDirectory", wintypes.HANDLE),
        ("FileNameLength", wintypes.ULONG),
        ("FileName", wintypes.WCHAR * 1),
    ]


class _FILE_DISPOSITION_INFORMATION(ctypes.Structure):
    _fields_ = [("DeleteFile", ctypes.c_ubyte)]


_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_ntdll = ctypes.WinDLL("ntdll")

_CreateFileW = _kernel32.CreateFileW
_CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
_CreateFileW.restype = wintypes.HANDLE
_CloseHandle = _kernel32.CloseHandle
_CloseHandle.argtypes = [wintypes.HANDLE]
_CloseHandle.restype = wintypes.BOOL
_GetFileInformationByHandle = _kernel32.GetFileInformationByHandle
_GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION)]
_GetFileInformationByHandle.restype = wintypes.BOOL
_WriteFile = _kernel32.WriteFile
_WriteFile.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
_WriteFile.restype = wintypes.BOOL
_FlushFileBuffers = _kernel32.FlushFileBuffers
_FlushFileBuffers.argtypes = [wintypes.HANDLE]
_FlushFileBuffers.restype = wintypes.BOOL
_GetFinalPathNameByHandleW = _kernel32.GetFinalPathNameByHandleW
_GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
_GetFinalPathNameByHandleW.restype = wintypes.DWORD

_NtCreateFile = _ntdll.NtCreateFile
_NtCreateFile.argtypes = [
    ctypes.POINTER(wintypes.HANDLE),
    wintypes.DWORD,
    ctypes.POINTER(_OBJECT_ATTRIBUTES),
    ctypes.POINTER(_IO_STATUS_BLOCK),
    wintypes.LPVOID,
    wintypes.ULONG,
    wintypes.ULONG,
    wintypes.ULONG,
    wintypes.ULONG,
    wintypes.LPVOID,
    wintypes.ULONG,
]
_NtCreateFile.restype = _NTSTATUS

_NtSetInformationFile = _ntdll.NtSetInformationFile
_NtSetInformationFile.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(_IO_STATUS_BLOCK),
    wintypes.LPVOID,
    wintypes.ULONG,
    wintypes.ULONG,
]
_NtSetInformationFile.restype = _NTSTATUS


class _NtOpenError(WorkspaceBoundaryError):
    def __init__(self, message: str, status: int) -> None:
        super().__init__(f"{message} (ntstatus=0x{status:08x})")
        self.status = status


def _win_close(handle: int | None) -> None:
    if handle not in (None, 0, _INVALID_HANDLE_VALUE):
        _CloseHandle(wintypes.HANDLE(handle))


def _win_error(message: str) -> WorkspaceMutationError:
    return WorkspaceMutationError(f"{message} (winerror={ctypes.get_last_error()})")


def _nt_open_relative(
    root_handle: int,
    name: str,
    *,
    desired_access: int,
    share_access: int,
    disposition: int,
    options: int,
    file_attributes: int = 0,
) -> int:
    buffer = ctypes.create_unicode_buffer(name)
    encoded_len = len(name.encode("utf-16-le"))
    string = _UNICODE_STRING(encoded_len, encoded_len + 2, ctypes.cast(buffer, wintypes.LPWSTR))
    attrs = _OBJECT_ATTRIBUTES(
        ctypes.sizeof(_OBJECT_ATTRIBUTES),
        wintypes.HANDLE(root_handle),
        ctypes.pointer(string),
        _OBJ_CASE_INSENSITIVE,
        None,
        None,
    )
    iosb = _IO_STATUS_BLOCK()
    out = wintypes.HANDLE()
    status = int(
        _NtCreateFile(
            ctypes.byref(out),
            desired_access,
            ctypes.byref(attrs),
            ctypes.byref(iosb),
            None,
            file_attributes,
            share_access,
            disposition,
            options,
            None,
            0,
        )
    )
    if status < 0:
        raise _NtOpenError("relative Windows handle open failed closed", status & 0xFFFFFFFF)
    return int(out.value)


def _win_info(handle: int) -> _BY_HANDLE_FILE_INFORMATION:
    info = _BY_HANDLE_FILE_INFORMATION()
    if not _GetFileInformationByHandle(wintypes.HANDLE(handle), ctypes.byref(info)):
        raise _win_error("GetFileInformationByHandle failed")
    return info


def _win_file_identity(info: _BY_HANDLE_FILE_INFORMATION) -> str:
    file_id = (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow)
    return f"win-id:{int(info.dwVolumeSerialNumber)}:{file_id}"


def _win_file_state(info: _BY_HANDLE_FILE_INFORMATION) -> str:
    size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
    mtime = (int(info.ftLastWriteTime.dwHighDateTime) << 32) | int(info.ftLastWriteTime.dwLowDateTime)
    return f"{_win_file_identity(info)}:{size}:{mtime}"


def _win_final_path(handle: int) -> str:
    size = _GetFinalPathNameByHandleW(wintypes.HANDLE(handle), None, 0, 0)
    if not size:
        raise _win_error("GetFinalPathNameByHandleW sizing failed")
    buffer = ctypes.create_unicode_buffer(size + 1)
    written = _GetFinalPathNameByHandleW(wintypes.HANDLE(handle), buffer, len(buffer), 0)
    if not written or written >= len(buffer):
        raise _win_error("GetFinalPathNameByHandleW failed")
    value = buffer.value
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normpath(value)


def _nt_rename_relative_no_clobber(file_handle: int, parent_handle: int, leaf: str) -> None:
    encoded = leaf.encode("utf-16-le")
    offset = _FILE_RENAME_INFORMATION.FileName.offset
    size = max(ctypes.sizeof(_FILE_RENAME_INFORMATION), offset + len(encoded))
    raw = ctypes.create_string_buffer(size)
    info = _FILE_RENAME_INFORMATION.from_buffer(raw)
    info.u.ReplaceIfExists = 0
    info.RootDirectory = wintypes.HANDLE(parent_handle)
    info.FileNameLength = len(encoded)
    ctypes.memmove(ctypes.addressof(raw) + offset, encoded, len(encoded))

    iosb = _IO_STATUS_BLOCK()
    status = int(
        _NtSetInformationFile(
            wintypes.HANDLE(file_handle),
            ctypes.byref(iosb),
            ctypes.byref(raw),
            size,
            _FILE_RENAME_INFORMATION_CLASS,
        )
    )
    if status < 0:
        unsigned = status & 0xFFFFFFFF
        if unsigned == _STATUS_OBJECT_NAME_COLLISION:
            raise WorkspaceBoundaryError("target appeared before atomic no-clobber publication")
        raise WorkspaceMutationError(f"NtSetInformationFile rename failed (ntstatus=0x{unsigned:08x})")


def _nt_mark_delete(file_handle: int) -> None:
    disposition = _FILE_DISPOSITION_INFORMATION(1)
    iosb = _IO_STATUS_BLOCK()
    _NtSetInformationFile(
        wintypes.HANDLE(file_handle),
        ctypes.byref(iosb),
        ctypes.byref(disposition),
        ctypes.sizeof(disposition),
        _FILE_DISPOSITION_INFORMATION_CLASS,
    )


class WindowsWorkspaceBackend:
    def __init__(self, workspace_root: str | os.PathLike[str]) -> None:
        raw = os.path.abspath(os.fspath(workspace_root))
        handle = _CreateFileW(
            raw,
            _FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE,
            None,
            _OPEN_EXISTING,
            _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle == _INVALID_HANDLE_VALUE:
            raise WorkspaceBoundaryError("workspace root could not be opened no-follow")
        self._root_handle = int(handle)
        try:
            info = _win_info(self._root_handle)
            if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                raise WorkspaceBoundaryError("workspace root is a reparse point")
            if not info.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY:
                raise WorkspaceBoundaryError("workspace root is not a directory")
            self._root_identity = _win_file_identity(info)
            self.canonical_root = _win_final_path(self._root_handle)
        except Exception:
            _win_close(self._root_handle)
            raise
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            _win_close(self._root_handle)
            self._closed = True

    def prepare_create(self, relative_path: str) -> "WindowsPreparedCreate":
        if self._closed:
            raise WorkspaceBoundaryError("workspace backend is closed")
        self._revalidate_root_path()
        parts = relative_path.split("/")
        chain: list[int] = []
        parent = self._root_handle
        parent_parts: list[str] = []
        try:
            for component in parts[:-1]:
                child = _nt_open_relative(
                    parent,
                    component,
                    desired_access=_FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                    share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE,
                    disposition=_FILE_OPEN,
                    options=_FILE_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
                )
                info = _win_info(child)
                if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                    _win_close(child)
                    raise WorkspaceBoundaryError("parent component is a reparse point")
                if not info.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY:
                    _win_close(child)
                    raise WorkspaceBoundaryError("parent component is not a directory")
                chain.append(child)
                parent = child
                parent_parts.append(component)
            return WindowsPreparedCreate(self, chain, parent, tuple(parent_parts), parts[-1])
        except Exception:
            for item in reversed(chain):
                _win_close(item)
            raise

    def current_parent_identity(self, parent_parts: tuple[str, ...]) -> str:
        parent = self._root_handle
        chain: list[int] = []
        try:
            for component in parent_parts:
                child = _nt_open_relative(
                    parent,
                    component,
                    desired_access=_FILE_LIST_DIRECTORY | _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                    share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE,
                    disposition=_FILE_OPEN,
                    options=_FILE_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
                )
                info = _win_info(child)
                if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                    _win_close(child)
                    raise WorkspaceBoundaryError("current parent component is a reparse point")
                chain.append(child)
                parent = child
            return _win_file_identity(_win_info(parent))
        finally:
            for item in reversed(chain):
                _win_close(item)

    def _revalidate_root_path(self) -> None:
        handle = _CreateFileW(
            self.canonical_root,
            _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE,
            None,
            _OPEN_EXISTING,
            _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle == _INVALID_HANDLE_VALUE:
            raise WorkspaceBoundaryError("workspace root path is no longer available")
        try:
            info = _win_info(int(handle))
            if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                raise WorkspaceBoundaryError("workspace root path became a reparse point")
            if _win_file_identity(info) != self._root_identity:
                raise WorkspaceBoundaryError("workspace root identity changed")
        finally:
            _win_close(int(handle))


class WindowsPreparedCreate:
    def __init__(
        self,
        backend: WindowsWorkspaceBackend,
        chain: list[int],
        parent_handle: int,
        parent_parts: tuple[str, ...],
        leaf: str,
    ) -> None:
        self._backend = backend
        self._chain = chain
        self._parent_handle = parent_handle
        self._parent_parts = parent_parts
        self._leaf = leaf
        self._closed = False
        self.parent_identity = _win_file_identity(_win_info(parent_handle))
        self.revalidate_absent()

    def close(self) -> None:
        if self._closed:
            return
        for handle in reversed(self._chain):
            _win_close(handle)
        self._closed = True

    def revalidate_absent(self) -> None:
        if self._closed:
            raise WorkspaceBoundaryError("prepared target is closed")
        self._backend._revalidate_root_path()
        if self._backend.current_parent_identity(self._parent_parts) != self.parent_identity:
            raise WorkspaceBoundaryError("parent path identity changed")
        if _win_file_identity(_win_info(self._parent_handle)) != self.parent_identity:
            raise WorkspaceBoundaryError("pinned parent identity changed")

        handle: int | None = None
        try:
            handle = _nt_open_relative(
                self._parent_handle,
                self._leaf,
                desired_access=_FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE,
                disposition=_FILE_OPEN,
                options=_FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
            )
        except _NtOpenError as exc:
            if exc.status in {_STATUS_OBJECT_NAME_NOT_FOUND, _STATUS_OBJECT_PATH_NOT_FOUND}:
                return
            raise
        else:
            info = _win_info(handle)
            if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                raise WorkspaceBoundaryError("WO-0021 target is an existing reparse point")
            raise WorkspaceBoundaryError("WO-0021 create-only target already exists")
        finally:
            _win_close(handle)

    def publish(self, content: bytes, pre_publish_check: Callable[[], None]) -> str:
        temp_name = f"{_TEMP_PREFIX}{secrets.token_hex(16)}.tmp"
        temp_handle: int | None = None
        renamed = False
        try:
            temp_handle = _nt_open_relative(
                self._parent_handle,
                temp_name,
                desired_access=_FILE_READ_DATA | _FILE_WRITE_DATA | _FILE_READ_ATTRIBUTES | _FILE_WRITE_ATTRIBUTES | _DELETE | _SYNCHRONIZE,
                share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE,
                disposition=_FILE_CREATE,
                options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
                file_attributes=_FILE_ATTRIBUTE_TEMPORARY,
            )
            temp_info = _win_info(temp_handle)
            if temp_info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY):
                raise WorkspaceBoundaryError("temporary target is not a regular file")

            if content:
                buffer = ctypes.create_string_buffer(content)
                offset = 0
                while offset < len(content):
                    chunk = min(len(content) - offset, 1 << 20)
                    written = wintypes.DWORD()
                    pointer = ctypes.cast(ctypes.byref(buffer, offset), wintypes.LPCVOID)
                    if not _WriteFile(wintypes.HANDLE(temp_handle), pointer, chunk, ctypes.byref(written), None):
                        raise _win_error("WriteFile failed")
                    if written.value <= 0:
                        raise WorkspaceMutationError("short Windows workspace write")
                    offset += int(written.value)
            if not _FlushFileBuffers(wintypes.HANDLE(temp_handle)):
                raise _win_error("FlushFileBuffers failed")

            pre_publish_check()
            _nt_rename_relative_no_clobber(temp_handle, self._parent_handle, self._leaf)
            renamed = True
            info = _win_info(temp_handle)
            if info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY):
                raise WorkspaceMutationError("published Windows target is not a regular file")
            return _win_file_state(info)
        finally:
            if temp_handle is not None:
                if not renamed:
                    _nt_mark_delete(temp_handle)
                _win_close(temp_handle)
