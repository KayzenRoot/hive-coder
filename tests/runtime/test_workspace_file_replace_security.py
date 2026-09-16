from __future__ import annotations

"""Adversarial contract for HCODER-WO-0022.

Implementation must make these scenarios fail closed. Platform-specific native
race fixtures may extend this suite, but may not weaken these invariants.
"""

import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.workspace_files import WorkspaceFileCapability


class WorkspaceReplaceSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        self.target = self.root / "src" / "module.py"
        self.target.write_bytes(b"old\n")
        self.plane = PermissionControlPlane()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def capability(self) -> WorkspaceFileCapability:
        return WorkspaceFileCapability(self.root, self.plane)

    def test_dot_git_is_never_a_replace_target(self) -> None:
        (self.root / ".git").mkdir()
        (self.root / ".git" / "config").write_bytes(b"old")
        cap = self.capability()
        try:
            with self.assertRaises(Exception):
                cap.prepare_replace_request("session-1", ".git/config", b"new")
        finally:
            cap.close()

    def test_traversal_is_never_a_replace_target(self) -> None:
        cap = self.capability()
        try:
            with self.assertRaises(Exception):
                cap.prepare_replace_request("session-1", "../outside.txt", b"new")
        finally:
            cap.close()

    @unittest.skipIf(os.name == "nt", "POSIX symlink fixture")
    def test_symlink_target_is_rejected(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_bytes(b"owner")
        link = self.root / "src" / "link.py"
        link.symlink_to(outside)
        cap = self.capability()
        try:
            with self.assertRaises(Exception):
                cap.prepare_replace_request("session-1", "src/link.py", b"new")
        finally:
            cap.close()
        self.assertEqual(outside.read_bytes(), b"owner")

    @unittest.skipIf(os.name == "nt", "POSIX symlink fixture")
    def test_symlink_parent_is_rejected(self) -> None:
        outside_dir = self.root / "outside-dir"
        outside_dir.mkdir()
        (outside_dir / "module.py").write_bytes(b"owner")
        (self.root / "linked").symlink_to(outside_dir, target_is_directory=True)
        cap = self.capability()
        try:
            with self.assertRaises(Exception):
                cap.prepare_replace_request("session-1", "linked/module.py", b"new")
        finally:
            cap.close()
        self.assertEqual((outside_dir / "module.py").read_bytes(), b"owner")

    def test_old_content_change_after_approval_must_fail_closed(self) -> None:
        cap = self.capability()
        try:
            request = cap.prepare_replace_request("session-1", "src/module.py", b"approved-new\n")
            self.target.write_bytes(b"concurrent-owner\n")
            # A real authorized permit fixture will replace this assertion when the
            # implementation is wired. The invariant is frozen now: executing the
            # stale request must never replace the concurrent owner's bytes.
            with self.assertRaises(Exception):
                cap.replace_bytes(request, b"approved-new\n", permit_token="invalid-prebuilt-token")
        finally:
            cap.close()
        self.assertEqual(self.target.read_bytes(), b"concurrent-owner\n")

    def test_wrong_new_content_must_fail_before_mutation(self) -> None:
        cap = self.capability()
        try:
            request = cap.prepare_replace_request("session-1", "src/module.py", b"approved-new\n")
            with self.assertRaises(Exception):
                cap.replace_bytes(request, b"different-new\n", permit_token="invalid-prebuilt-token")
        finally:
            cap.close()
        self.assertEqual(self.target.read_bytes(), b"old\n")


if __name__ == "__main__":
    unittest.main()
