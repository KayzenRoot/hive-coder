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
        self.assertTrue(str(request.arguments["parent_identity"]).startswith("win-id:")); self.assertTrue(str(request.arguments["target_identity"]).startswith("win-id:")); self.assertEqual(request.arguments["old_content_bytes"], len(b"old\r\n"))

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

    def test_verified_staging_is_mutation_ready_and_close_cleans_unpublished_temp(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\r\n", expected); self.assertEqual(self.target.read_bytes(), b"old\r\n"); self.assertEqual(prepared._stage_bytes, len(b"new\r\n")); self.assertTrue(str(prepared._stage_identity).startswith("win-id:")); prepared.mutation_ready(expected)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"old\r\n"); self.assertEqual(list((self.root / "src").glob(".hive-replace-*.tmp")), [])

    def test_atomic_publication_replaces_destination_with_verified_stage(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\r\n", expected); prepared.mutation_ready(expected); stage_identity = prepared._stage_identity
            published_identity = prepared.publish_replace(expected, lambda: None)
            self.assertEqual(published_identity, stage_identity); self.assertEqual(self.target.read_bytes(), b"new\r\n"); self.assertEqual(list((self.root / "src").glob(".hive-replace-*.tmp")), [])
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"new\r\n")

    def test_pre_publish_check_failure_preserves_destination(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\r\n", expected); prepared.mutation_ready(expected)
            def reject() -> None: raise WorkspaceBoundaryError("cancelled")
            with self.assertRaises(WorkspaceBoundaryError): prepared.publish_replace(expected, reject)
            self.assertEqual(self.target.read_bytes(), b"old\r\n")
        finally: prepared.close()

    def test_stage_path_replacement_is_detected_before_mutation_ready(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\r\n", expected); stage_path = self.root / "src" / str(prepared._stage_name); displaced = stage_path.with_suffix(".owned")
            os.replace(stage_path, displaced); stage_path.write_bytes(b"attacker")
            with self.assertRaises(WorkspaceBoundaryError): prepared.mutation_ready(expected)
            self.assertEqual(self.target.read_bytes(), b"old\r\n"); stage_path.unlink(); os.replace(displaced, stage_path)
        finally: prepared.close()

    def test_stale_destination_after_staging_fails_before_publication(self) -> None:
        prepared = self.cap._backend.prepare_replace("src/module.py")
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\r\n", expected); self.target.write_bytes(b"owner-change\r\n")
            with self.assertRaises(WorkspaceBoundaryError): prepared.mutation_ready(expected)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"owner-change\r\n")


if __name__ == "__main__": unittest.main()
