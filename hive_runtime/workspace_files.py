from __future__ import annotations

import ctypes
import hashlib
import os
import secrets
import stat
import threading
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from .control_plane import PermissionControlPlane
from .control_types import ActionRequest, ActionTarget, Capability, SessionState, normalize_workspace
from .errors import WorkspaceBoundaryError, WorkspaceMutationError

WRITE_CONTRACT = "hive-workspace-write-v1"
WRITE_ACTION = "write_file_v1"
DEFAULT_MAX_WRITE_BYTES = 1_048_576
MAX_RELATIVE_PATH_BYTES = 1024
MAX_COMPONENTS = 32
MAX_COMPONENT_BYTES = 255
_TEMP_PREFIX = ".hive-write-"
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


@dataclass(frozen=True)
class WorkspaceWriteReceipt:
    workspace: str
    relative_path: str
    content_sha256: str
    content_bytes: int
    previous_state: str
    committed_state: str


class _PreparedTarget(Protocol):
    state: str

    def revalidate(self) -> None: ...

    def commit(self, content: bytes, pre_commit_check: Callable[[], None]) -> str: ...

    def close(self) -> None: ...


class _Backend(Protocol):
    canonical_root: str

    def prepare(self, relative_path: str) -> _PreparedTarget: ...

    def close(self) -> None: ...


def normalize_relative_file_path(value: str) -> str:
    if not isinstance(value, str):
        raise WorkspaceBoundaryError("relative path must be text")
    if not value or value != value.strip():
        raise WorkspaceBoundaryError("relative path is empty or padded")
    if "\x00" in value:
        raise WorkspaceBoundaryError("relative path contains NUL")
    if unicodedata.normalize("NFC", value) != value:
        raise WorkspaceBoundaryError("relative path must be NFC-normalized")
    if "\\" in value:
        raise WorkspaceBoundaryError("backslash path syntax is not accepted")
    if value.startswith("/") or value.startswith("//"):
        raise WorkspaceBoundaryError("absolute paths are not accepted")
    encoded = value.encode("utf-8")
    if len(encoded) > MAX_RELATIVE_PATH_BYTES:
        raise WorkspaceBoundaryError("relative path exceeds byte ceiling")

    parts = value.split("/")
    if not parts or len(parts) > MAX_COMPONENTS:
        raise WorkspaceBoundaryError("relative path has too many components")
    normalized: list[str] = []
    for part in parts:
        if part in {"", ".", ".."}:
            raise WorkspaceBoundaryError("relative path contains traversal or empty component")
        if len(part.encode("utf-8")) > MAX_COMPONENT_BYTES:
            raise WorkspaceBoundaryError("path component exceeds byte ceiling")
        if ":" in part:
            raise WorkspaceBoundaryError("drive/device/alternate-stream syntax is not accepted")
        if part.endswith((" ", ".")):
            raise WorkspaceBoundaryError("ambiguous trailing dot/space component is not accepted")
        stem = part.split(".", 1)[0].casefold()
        if stem in _WINDOWS_RESERVED:
            raise WorkspaceBoundaryError("reserved device filename is not accepted")
        normalized.append(part)
    return "/".join(normalized)


def _content_bytes(content: bytes | bytearray | memoryview) -> bytes:
    if not isinstance(content, (bytes, bytearray, memoryview)):
        raise WorkspaceBoundaryError("content must be bytes-like")
    return bytes(content)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class WorkspaceFileCapability:
    """Permit-gated, bounded workspace file mutation boundary.

    The capability owns path/OS safety mechanics only. Approval and permit minting
    remain exclusively inside PermissionControlPlane/trusted UI authority.
    """

    def __init__(
        self,
        workspace_root: str | os.PathLike[str],
        control_plane: PermissionControlPlane,
        *,
        max_write_bytes: int = DEFAULT_MAX_WRITE_BYTES,
    ) -> None:
        if not isinstance(control_plane, PermissionControlPlane):
            raise TypeError("control_plane must be PermissionControlPlane")
        ceiling = int(max_write_bytes)
        if ceiling <= 0 or ceiling > DEFAULT_MAX_WRITE_BYTES:
            raise ValueError("max_write_bytes outside governed ceiling")
        self._plane = control_plane
        self._max_write_bytes = ceiling
        self._lock = threading.RLock()
        self._closed = False
        if os.name == "nt":
            self._backend: _Backend = _WindowsBackend(workspace_root)
        else:
            self._backend = _PosixBackend(workspace_root)
        self.workspace = normalize_workspace(self._backend.canonical_root)

    def __enter__(self) -> "WorkspaceFileCapability":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._backend.close()
            self._closed = True

    def prepare_write_request(
        self,
        session_id: str,
        relative_path: str,
        content: bytes | bytearray | memoryview,
    ) -> ActionRequest:
        data = _content_bytes(content)
        self._validate_size(data)
        relative = normalize_relative_file_path(relative_path)
        with self._lock:
            self._require_open()
            prepared = self._backend.prepare(relative)
            try:
                prepared.revalidate()
                expected_state = prepared.state
            finally:
                prepared.close()
        return ActionRequest(
            session_id=str(session_id),
            capability=Capability.FILESYSTEM_WRITE,
            action=WRITE_ACTION,
            target=ActionTarget(workspace=self.workspace),
            arguments={
                "contract": WRITE_CONTRACT,
                "path": relative,
                "content_sha256": _sha256(data),
                "content_bytes": len(data),
                "expected_state": expected_state,
            },
        )

    def write_bytes(
        self,
        request: ActionRequest,
        content: bytes | bytearray | memoryview,
        *,
        permit_token: str,
    ) -> WorkspaceWriteReceipt:
        data = _content_bytes(content)
        self._validate_size(data)
        relative, expected_state = self._validate_request(request, data)
        with self._lock:
            self._require_open()
            prepared = self._backend.prepare(relative)
            try:
                if prepared.state != expected_state:
                    raise WorkspaceBoundaryError("target state changed after approval request")
                prepared.revalidate()

                # Canonical CP permit is consumed only after all read-only target
                # validation succeeds and immediately before the first mutation.
                self._plane.consume_execution_permit(permit_token, request)
                self._require_active(request.session_id)

                def pre_commit_check() -> None:
                    self._require_active(request.session_id)
                    prepared.revalidate()

                committed_state = prepared.commit(data, pre_commit_check)
            except WorkspaceBoundaryError:
                raise
            except Exception as exc:
                if isinstance(exc, WorkspaceMutationError):
                    raise
                raise WorkspaceMutationError("workspace mutation failed closed") from exc
            finally:
                prepared.close()

        return WorkspaceWriteReceipt(
            workspace=self.workspace,
            relative_path=relative,
            content_sha256=_sha256(data),
            content_bytes=len(data),
            previous_state=expected_state,
            committed_state=committed_state,
        )

    def _validate_request(self, request: ActionRequest, data: bytes) -> tuple[str, str]:
        if request.capability is not Capability.FILESYSTEM_WRITE:
            raise WorkspaceBoundaryError("request capability is not filesystem.write")
        if str(request.action).strip() != WRITE_ACTION:
            raise WorkspaceBoundaryError("request action is not the governed write contract")
        canonical_target = request.target.canonical()
        if canonical_target.get("workspace") != self.workspace:
            raise WorkspaceBoundaryError("request workspace does not match capability workspace")
        args = request.arguments
        if not isinstance(args, dict):
            raise WorkspaceBoundaryError("request arguments must be a dict")
        if set(args) != {"contract", "path", "content_sha256", "content_bytes", "expected_state"}:
            raise WorkspaceBoundaryError("request arguments do not match write contract")
        if args.get("contract") != WRITE_CONTRACT:
            raise WorkspaceBoundaryError("write contract mismatch")
        relative = normalize_relative_file_path(args.get("path"))
        if args.get("content_bytes") != len(data):
            raise WorkspaceBoundaryError("content length does not match approved request")
        if args.get("content_sha256") != _sha256(data):
            raise WorkspaceBoundaryError("content digest does not match approved request")
        expected_state = args.get("expected_state")
        if not isinstance(expected_state, str) or not expected_state:
            raise WorkspaceBoundaryError("expected target state is missing")
        return relative, expected_state

    def _validate_size(self, data: bytes) -> None:
        if len(data) > self._max_write_bytes:
            raise WorkspaceBoundaryError("write payload exceeds governed byte ceiling")

    def _require_active(self, session_id: str) -> None:
        if self._plane.session_state(session_id) is not SessionState.ACTIVE:
            raise WorkspaceMutationError("control session is not active")

    def _require_open(self) -> None:
        if self._closed:
            raise WorkspaceBoundaryError("workspace capability is closed")


class _PosixBackend:
    def __init__(self, workspace_root: str | os.PathLike[str]) -> None:
        raw = os.fspath(workspace_root)
        if not raw:
            raise WorkspaceBoundaryError("workspace root is empty")
        try:
            lst = os.lstat(raw)
        except OSError as exc:
            raise WorkspaceBoundaryError("workspace root is unavailable") from exc
        if stat.S_ISLNK(lst.st_mode) or not stat.S_ISDIR(lst.st_mode):
            raise WorkspaceBoundaryError("workspace root must be a real directory")
        self.canonical_root = os.path.realpath(raw)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            self._root_fd = os.open(self.canonical_root, flags)
        except OSError as exc:
            raise WorkspaceBoundaryError("workspace root could not be opened no-follow") from exc
        info = os.fstat(self._root_fd)
        if not stat.S_ISDIR(info.st_mode):
            os.close(self._root_fd)
            raise WorkspaceBoundaryError("workspace root handle is not a directory")
        self._root_identity = (info.st_dev, info.st_ino)
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        os.close(self._root_fd)
        self._closed = True

    def prepare(self, relative_path: str) -> "_PosixPreparedTarget":
        if self._closed:
            raise WorkspaceBoundaryError("workspace backend is closed")
        self._revalidate_root_path()
        parts = relative_path.split("/")
        parent_fd = os.dup(self._root_fd)
        try:
            flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            for component in parts[:-1]:
                next_fd = os.open(component, flags, dir_fd=parent_fd)
                info = os.fstat(next_fd)
                if not stat.S_ISDIR(info.st_mode):
                    os.close(next_fd)
                    raise WorkspaceBoundaryError("parent component is not a directory")
                os.close(parent_fd)
                parent_fd = next_fd
            return _PosixPreparedTarget(self, parent_fd, parts[-1])
        except Exception:
            os.close(parent_fd)
            raise

    def _revalidate_root_path(self) -> None:
        try:
            info = os.stat(self.canonical_root, follow_symlinks=False)
        except OSError as exc:
            raise WorkspaceBoundaryError("workspace root path is no longer available") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise WorkspaceBoundaryError("workspace root path changed type")
        if (info.st_dev, info.st_ino) != self._root_identity:
            raise WorkspaceBoundaryError("workspace root identity changed")


class _PosixPreparedTarget:
    def __init__(self, backend: _PosixBackend, parent_fd: int, leaf: str) -> None:
        self._backend = backend
        self._parent_fd = parent_fd
        self._leaf = leaf
        self._closed = False
        self.state = self._read_state()

    def close(self) -> None:
        if not self._closed:
            os.close(self._parent_fd)
            self._closed = True

    def revalidate(self) -> None:
        if self._closed:
            raise WorkspaceBoundaryError("prepared target is closed")
        self._backend._revalidate_root_path()
        if self._read_state() != self.state:
            raise WorkspaceBoundaryError("target identity/content metadata changed")

    def commit(self, content: bytes, pre_commit_check: Callable[[], None]) -> str:
        temp_name = f"{_TEMP_PREFIX}{secrets.token_hex(16)}.tmp"
        fd: int | None = None
        temp_identity: tuple[int, int] | None = None
        created = False
        try:
            mode = self._existing_mode_or_default()
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(temp_name, flags, mode, dir_fd=self._parent_fd)
            created = True
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise WorkspaceBoundaryError("temporary target is not a regular file")
            temp_identity = (info.st_dev, info.st_ino)
            view = memoryview(content)
            offset = 0
            while offset < len(view):
                written = os.write(fd, view[offset:])
                if written <= 0:
                    raise OSError("short workspace write")
                offset += written
            os.fsync(fd)

            pre_commit_check()
            if self._read_state() != self.state:
                raise WorkspaceBoundaryError("target changed before commit")
            os.replace(temp_name, self._leaf, src_dir_fd=self._parent_fd, dst_dir_fd=self._parent_fd)
            created = False
            try:
                os.fsync(self._parent_fd)
            except OSError:
                # Some filesystems do not permit directory fsync. The rename is
                # still atomic; power-loss durability is not claimed here.
                pass
            return self._read_state()
        except WorkspaceBoundaryError:
            raise
        except OSError as exc:
            raise WorkspaceMutationError("atomic workspace replace failed") from exc
        finally:
            if fd is not None:
                os.close(fd)
            if created and temp_identity is not None:
                self._unlink_temp_if_same(temp_name, temp_identity)

    def _existing_mode_or_default(self) -> int:
        try:
            info = os.stat(self._leaf, dir_fd=self._parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return 0o600
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise WorkspaceBoundaryError("target is not a regular no-follow file")
        return stat.S_IMODE(info.st_mode) or 0o600

    def _read_state(self) -> str:
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(self._leaf, flags, dir_fd=self._parent_fd)
        except FileNotFoundError:
            return "absent"
        except OSError as exc:
            raise WorkspaceBoundaryError("target cannot be opened no-follow") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise WorkspaceBoundaryError("target is not a regular file")
            return f"posix:{info.st_dev}:{info.st_ino}:{info.st_size}:{info.st_mtime_ns}"
        finally:
            os.close(fd)

    def _unlink_temp_if_same(self, temp_name: str, identity: tuple[int, int]) -> None:
        try:
            info = os.stat(temp_name, dir_fd=self._parent_fd, follow_symlinks=False)
            if stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identity:
                os.unlink(temp_name, dir_fd=self._parent_fd)
        except OSError:
            pass


if os.name == "nt":
    from ctypes import wintypes

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
    _FILE_RENAME_INFO_CLASS = 3
    _FILE_DISPOSITION_INFO_CLASS = 4
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

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

    class _FILE_RENAME_INFO(ctypes.Structure):
        _fields_ = [
            ("ReplaceIfExists", ctypes.c_ubyte),
            ("RootDirectory", wintypes.HANDLE),
            ("FileNameLength", wintypes.DWORD),
            ("FileName", wintypes.WCHAR * 1),
        ]

    class _FILE_DISPOSITION_INFO(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOL)]

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
    _SetFileInformationByHandle = _kernel32.SetFileInformationByHandle
    _SetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    _SetFileInformationByHandle.restype = wintypes.BOOL
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
            raise WorkspaceBoundaryError(f"relative Windows handle open failed closed (ntstatus=0x{status & 0xffffffff:08x})")
        return int(out.value)


    def _win_info(handle: int) -> _BY_HANDLE_FILE_INFORMATION:
        info = _BY_HANDLE_FILE_INFORMATION()
        if not _GetFileInformationByHandle(wintypes.HANDLE(handle), ctypes.byref(info)):
            raise _win_error("GetFileInformationByHandle failed")
        return info


    def _win_identity_state(info: _BY_HANDLE_FILE_INFORMATION) -> str:
        file_id = (int(info.nFileIndexHigh) << 32) | int(info.nFileIndexLow)
        size = (int(info.nFileSizeHigh) << 32) | int(info.nFileSizeLow)
        mtime = (int(info.ftLastWriteTime.dwHighDateTime) << 32) | int(info.ftLastWriteTime.dwLowDateTime)
        return f"win:{int(info.dwVolumeSerialNumber)}:{file_id}:{size}:{mtime}"


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


    class _WindowsBackend:
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
                self._root_identity = _win_identity_state(info)
                self.canonical_root = _win_final_path(self._root_handle)
            except Exception:
                _win_close(self._root_handle)
                raise
            self._closed = False

        def close(self) -> None:
            if not self._closed:
                _win_close(self._root_handle)
                self._closed = True

        def prepare(self, relative_path: str) -> "_WindowsPreparedTarget":
            if self._closed:
                raise WorkspaceBoundaryError("workspace backend is closed")
            self._revalidate_root_path()
            parts = relative_path.split("/")
            chain: list[int] = []
            parent = self._root_handle
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
                return _WindowsPreparedTarget(self, chain, parent, parts[-1])
            except Exception:
                for handle in reversed(chain):
                    _win_close(handle)
                raise

        def _revalidate_root_path(self) -> None:
            handle = _CreateFileW(
                self.canonical_root,
                _FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                _FILE_SHARE_READ | _FILE_SHARE_WRITE | 0x00000004,
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
                if _win_identity_state(info) != self._root_identity:
                    raise WorkspaceBoundaryError("workspace root identity changed")
            finally:
                _win_close(int(handle))


    class _WindowsPreparedTarget:
        def __init__(self, backend: _WindowsBackend, chain: list[int], parent_handle: int, leaf: str) -> None:
            self._backend = backend
            self._chain = chain
            self._parent_handle = parent_handle
            self._leaf = leaf
            self._closed = False
            self.state = self._read_state()

        def close(self) -> None:
            if self._closed:
                return
            for handle in reversed(self._chain):
                _win_close(handle)
            self._closed = True

        def revalidate(self) -> None:
            if self._closed:
                raise WorkspaceBoundaryError("prepared target is closed")
            self._backend._revalidate_root_path()
            if self._read_state() != self.state:
                raise WorkspaceBoundaryError("target identity/content metadata changed")

        def commit(self, content: bytes, pre_commit_check: Callable[[], None]) -> str:
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
                info = _win_info(temp_handle)
                if info.dwFileAttributes & (_FILE_ATTRIBUTE_REPARSE_POINT | _FILE_ATTRIBUTE_DIRECTORY):
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

                pre_commit_check()
                if self._read_state() != self.state:
                    raise WorkspaceBoundaryError("target changed before commit")
                self._rename_temp(temp_handle, replace=self.state != "absent")
                renamed = True
                return self._read_state()
            except WorkspaceBoundaryError:
                raise
            except OSError as exc:
                raise WorkspaceMutationError("Windows workspace replace failed") from exc
            finally:
                if temp_handle is not None:
                    if not renamed:
                        self._mark_delete(temp_handle)
                    _win_close(temp_handle)

        def _read_state(self) -> str:
            handle: int | None = None
            try:
                handle = _nt_open_relative(
                    self._parent_handle,
                    self._leaf,
                    desired_access=_FILE_READ_ATTRIBUTES | _SYNCHRONIZE,
                    share_access=_FILE_SHARE_READ | _FILE_SHARE_WRITE | 0x00000004,
                    disposition=_FILE_OPEN,
                    options=_FILE_NON_DIRECTORY_FILE | _FILE_OPEN_REPARSE_POINT | _FILE_SYNCHRONOUS_IO_NONALERT,
                )
            except WorkspaceBoundaryError as exc:
                text = str(exc)
                # STATUS_OBJECT_NAME_NOT_FOUND / STATUS_OBJECT_PATH_NOT_FOUND.
                if "c0000034" in text.casefold() or "c000003a" in text.casefold():
                    return "absent"
                raise
            try:
                info = _win_info(handle)
                if info.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT:
                    raise WorkspaceBoundaryError("target is a reparse point")
                if info.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY:
                    raise WorkspaceBoundaryError("target is a directory")
                return _win_identity_state(info)
            finally:
                _win_close(handle)

        def _rename_temp(self, temp_handle: int, *, replace: bool) -> None:
            encoded = self._leaf.encode("utf-16-le")
            offset = _FILE_RENAME_INFO.FileName.offset
            size = offset + len(encoded)
            raw = ctypes.create_string_buffer(size)
            info = _FILE_RENAME_INFO.from_buffer(raw)
            info.ReplaceIfExists = 1 if replace else 0
            info.RootDirectory = wintypes.HANDLE(self._parent_handle)
            info.FileNameLength = len(encoded)
            ctypes.memmove(ctypes.addressof(raw) + offset, encoded, len(encoded))
            if not _SetFileInformationByHandle(
                wintypes.HANDLE(temp_handle),
                _FILE_RENAME_INFO_CLASS,
                ctypes.byref(raw),
                size,
            ):
                raise _win_error("handle-relative rename failed")

        def _mark_delete(self, handle: int) -> None:
            info = _FILE_DISPOSITION_INFO(True)
            _SetFileInformationByHandle(
                wintypes.HANDLE(handle),
                _FILE_DISPOSITION_INFO_CLASS,
                ctypes.byref(info),
                ctypes.sizeof(info),
            )

else:
    class _WindowsBackend:  # pragma: no cover - construction is OS-gated.
        def __init__(self, workspace_root: str | os.PathLike[str]) -> None:
            raise WorkspaceBoundaryError("Windows backend is unavailable on this platform")
