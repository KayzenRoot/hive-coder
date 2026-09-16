from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.errors import WorkspaceBoundaryError
from hive_runtime.workspace_files import WorkspaceFileCapability


@unittest.skipUnless(os.name == "nt", "Windows replacement contract")
class WindowsReplaceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        (self.root / "src").mkdir(); self.target = self.root / "src" / "module.py"; self.target.write_bytes(b"old\r\n")
        self.cap = WorkspaceFileCapability(self.root, PermissionControlPlane())

    def tearDown(self) -> None:
        self.cap.close(); self.temp.cleanup()

    def test_prepare_replace_binds_real_windows_file_identity_and_bytes(self) -> None:
        request = self.cap.prepare_replace_request("session-1", "src/module.py", b"new\r\n")
        self.assertTrue(str(request.arguments["parent_identity"]).startswith("win-id:"))
        self.assertTrue(str(request.arguments["target_identity"]).startswith("win-id:"))
        self.assertEqual(request.arguments["old_content_bytes"], len(b"old\r\n"))

    def test_live_revalidation_accepts_unchanged_target(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try: prepared.revalidate_expected(prepared.observed)
        finally: prepared.close()

    def test_live_revalidation_rejects_changed_old_bytes(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try:
            expected = prepared.observed; self.target.write_bytes(b"owner-change\r\n")
            with self.assertRaises(WorkspaceBoundaryError): prepared.revalidate_expected(expected)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"owner-change\r\n")

    def test_staging_remains_fail_closed_without_consuming_publication_authority(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try:
            with self.assertRaises(NotImplementedError): prepared.stage_replace(b"new\r\n", prepared.observed)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"old\r\n")


if __name__ == "__main__": unittest.main()
