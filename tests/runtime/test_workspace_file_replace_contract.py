from __future__ import annotations

"""HCODER-WO-0022 executable contract scaffold.

These tests intentionally fail until the governed existing-file replacement API is
implemented. They freeze the public contract before mutation code is added.
"""

import hashlib
import tempfile
import unittest
from pathlib import Path

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.workspace_files import WorkspaceFileCapability


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class WorkspaceReplaceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.target = self.root / "src" / "module.py"
        self.target.parent.mkdir()
        self.old = b"answer = 41\n"
        self.new = b"answer = 42\n"
        self.target.write_bytes(self.old)
        self.plane = PermissionControlPlane()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_replace_api_is_distinct_from_create_api(self) -> None:
        capability = WorkspaceFileCapability(self.root, self.plane)
        try:
            self.assertTrue(callable(getattr(capability, "prepare_write_request")))
            self.assertTrue(callable(getattr(capability, "write_bytes")))
            self.assertTrue(callable(getattr(capability, "prepare_replace_request")))
            self.assertTrue(callable(getattr(capability, "replace_bytes")))
        finally:
            capability.close()

    def test_prepare_replace_request_binds_exact_old_and_new_state(self) -> None:
        capability = WorkspaceFileCapability(self.root, self.plane)
        try:
            request = capability.prepare_replace_request("session-1", "src/module.py", self.new)
        finally:
            capability.close()

        self.assertEqual(request.action, "replace_file_v1")
        self.assertEqual(request.arguments["contract"], "hive-workspace-replace-v1")
        self.assertEqual(request.arguments["path"], "src/module.py")
        self.assertEqual(request.arguments["target_state"], "regular")
        self.assertEqual(request.arguments["old_content_sha256"], sha256(self.old))
        self.assertEqual(request.arguments["old_content_bytes"], len(self.old))
        self.assertEqual(request.arguments["new_content_sha256"], sha256(self.new))
        self.assertEqual(request.arguments["new_content_bytes"], len(self.new))
        self.assertIsInstance(request.arguments["parent_identity"], str)
        self.assertTrue(request.arguments["parent_identity"])
        self.assertIsInstance(request.arguments["target_identity"], str)
        self.assertTrue(request.arguments["target_identity"])
        self.assertNotIn("old_content", request.arguments)
        self.assertNotIn("new_content", request.arguments)

    def test_prepare_replace_rejects_missing_target(self) -> None:
        capability = WorkspaceFileCapability(self.root, self.plane)
        try:
            with self.assertRaises(Exception):
                capability.prepare_replace_request("session-1", "src/missing.py", self.new)
        finally:
            capability.close()

    def test_prepare_replace_rejects_directory_target(self) -> None:
        capability = WorkspaceFileCapability(self.root, self.plane)
        try:
            with self.assertRaises(Exception):
                capability.prepare_replace_request("session-1", "src", self.new)
        finally:
            capability.close()

    def test_prepare_replace_preserves_create_only_behavior(self) -> None:
        capability = WorkspaceFileCapability(self.root, self.plane)
        try:
            with self.assertRaises(Exception):
                capability.prepare_write_request("session-1", "src/module.py", self.new)
        finally:
            capability.close()

    def test_replace_request_contains_no_raw_payload(self) -> None:
        secret_old = b"OLD_SECRET_VALUE"
        secret_new = b"NEW_SECRET_VALUE"
        self.target.write_bytes(secret_old)
        capability = WorkspaceFileCapability(self.root, self.plane)
        try:
            request = capability.prepare_replace_request("session-1", "src/module.py", secret_new)
        finally:
            capability.close()
        rendered = repr(dict(request.arguments))
        self.assertNotIn("OLD_SECRET_VALUE", rendered)
        self.assertNotIn("NEW_SECRET_VALUE", rendered)
        self.assertEqual(request.arguments["old_content_sha256"], sha256(secret_old))
        self.assertEqual(request.arguments["new_content_sha256"], sha256(secret_new))


if __name__ == "__main__":
    unittest.main()
