from __future__ import annotations

import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from hive_runtime.errors import WorkspaceBoundaryError
from hive_runtime.workspace_files import WorkspaceFileCapability
from tests.runtime.test_workspace_files import authorize_write, make_plane, write_policy


@unittest.skipUnless(os.name == "nt", "Windows-only HIGH_ASSURANCE workspace capability tests")
class WindowsWorkspaceCapabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        self.plane = make_plane()
        self.capability = WorkspaceFileCapability(self.root, self.plane)
        self.session = self.plane.create_session(write_policy(str(self.root)), duration_seconds=60)

    def tearDown(self) -> None:
        self.capability.close()
        self.temp.cleanup()

    def test_target_created_at_native_publication_is_preserved(self) -> None:
        import hive_runtime.workspace_files_windows as windows_backend

        target = self.root / "src" / "race.txt"
        request, token = authorize_write(
            self.plane,
            self.capability,
            self.session,
            "src/race.txt",
            b"approved-content",
        )
        original = windows_backend._nt_rename_relative_no_clobber

        def race(file_handle: int, parent_handle: int, leaf: str) -> None:
            target.write_bytes(b"concurrent-owner")
            original(file_handle, parent_handle, leaf)

        with mock.patch.object(windows_backend, "_nt_rename_relative_no_clobber", side_effect=race):
            with self.assertRaises(WorkspaceBoundaryError):
                self.capability.write_bytes(request, b"approved-content", permit_token=token)

        self.assertEqual(target.read_bytes(), b"concurrent-owner")
        self.assertEqual(list((self.root / "src").glob(".hive-create-*.tmp")), [])

    def test_real_junction_parent_is_rejected_without_following(self) -> None:
        outside = self.root.parent / f"{self.root.name}-outside-parent"
        outside.mkdir()
        junction = self.root / "linked"
        _create_directory_junction(junction, outside)
        try:
            with self.assertRaises(WorkspaceBoundaryError):
                self.capability.prepare_write_request(self.session, "linked/escape.txt", b"blocked")
            self.assertFalse((outside / "escape.txt").exists())
        finally:
            os.rmdir(junction)
            outside.rmdir()

    def test_real_junction_target_is_rejected_as_existing_reparse_point(self) -> None:
        outside = self.root.parent / f"{self.root.name}-outside-target"
        outside.mkdir()
        junction = self.root / "src" / "junction-target"
        _create_directory_junction(junction, outside)
        try:
            with self.assertRaises(WorkspaceBoundaryError):
                self.capability.prepare_write_request(self.session, "src/junction-target", b"blocked")
            self.assertEqual(list(outside.iterdir()), [])
        finally:
            os.rmdir(junction)
            outside.rmdir()


def _create_directory_junction(link: Path, target: Path) -> None:
    """Create a real NTFS mount-point reparse point without symlink privilege."""
    if os.name != "nt":
        raise RuntimeError("Windows only")

    import ctypes
    from ctypes import wintypes

    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
    FSCTL_SET_REPARSE_POINT = 0x000900A4
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    device_io_control = kernel32.DeviceIoControl
    device_io_control.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    device_io_control.restype = wintypes.BOOL
    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    link.mkdir()
    resolved = target.resolve(strict=True)
    substitute = f"\\??\\{resolved}"
    printable = str(resolved)
    substitute_bytes = substitute.encode("utf-16-le")
    printable_bytes = printable.encode("utf-16-le")
    path_buffer = substitute_bytes + b"\x00\x00" + printable_bytes + b"\x00\x00"

    substitute_offset = 0
    substitute_length = len(substitute_bytes)
    print_offset = len(substitute_bytes) + 2
    print_length = len(printable_bytes)
    reparse_data_length = 8 + len(path_buffer)
    raw = struct.pack(
        "<IHHHHHH",
        IO_REPARSE_TAG_MOUNT_POINT,
        reparse_data_length,
        0,
        substitute_offset,
        substitute_length,
        print_offset,
        print_length,
    ) + path_buffer

    handle = create_file(
        str(link),
        GENERIC_WRITE,
        0,
        None,
        OPEN_EXISTING,
        FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    if handle == INVALID_HANDLE_VALUE:
        error = ctypes.get_last_error()
        os.rmdir(link)
        raise OSError(error, "CreateFileW failed while constructing junction fixture")
    try:
        returned = wintypes.DWORD()
        buffer = ctypes.create_string_buffer(raw)
        ok = device_io_control(
            handle,
            FSCTL_SET_REPARSE_POINT,
            buffer,
            len(raw),
            None,
            0,
            ctypes.byref(returned),
            None,
        )
        if not ok:
            error = ctypes.get_last_error()
            raise OSError(error, "FSCTL_SET_REPARSE_POINT failed while constructing junction fixture")
    finally:
        close_handle(handle)


if __name__ == "__main__":
    unittest.main()
