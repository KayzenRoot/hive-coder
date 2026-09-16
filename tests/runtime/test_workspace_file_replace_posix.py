from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.errors import WorkspaceBoundaryError
from hive_runtime.workspace_files import WorkspaceFileCapability


@unittest.skipIf(os.name == "nt", "POSIX replacement proof")
class PosixWorkspaceReplaceProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        (self.root / "src").mkdir(); self.target = self.root / "src" / "module.py"; self.target.write_bytes(b"old\n")
        self.cap = WorkspaceFileCapability(self.root, PermissionControlPlane())

    def tearDown(self) -> None:
        self.cap.close(); self.temp.cleanup()

    def _prepared(self): return self.cap._backend.prepare_replace("src/module.py")

    def test_revalidate_accepts_unchanged_pinned_and_live_target(self) -> None:
        prepared = self._prepared()
        try: prepared.revalidate_expected(prepared.observed)
        finally: prepared.close()

    def test_revalidate_rejects_in_place_content_change(self) -> None:
        prepared = self._prepared()
        try:
            expected = prepared.observed; self.target.write_bytes(b"changed-by-owner\n")
            with self.assertRaises(WorkspaceBoundaryError): prepared.revalidate_expected(expected)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"changed-by-owner\n")

    def test_revalidate_rejects_pathname_inode_replacement(self) -> None:
        prepared = self._prepared()
        try:
            expected = prepared.observed; replacement = self.root / "src" / "owner.tmp"; replacement.write_bytes(b"owner\n"); os.replace(replacement, self.target)
            with self.assertRaises(WorkspaceBoundaryError): prepared.revalidate_expected(expected)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"owner\n")

    def test_revalidate_rejects_target_path_becoming_symlink(self) -> None:
        prepared = self._prepared(); outside = self.root / "outside.txt"; outside.write_bytes(b"outside-owner\n")
        try:
            expected = prepared.observed; self.target.unlink(); self.target.symlink_to(outside)
            with self.assertRaises(WorkspaceBoundaryError): prepared.revalidate_expected(expected)
        finally: prepared.close()
        self.assertEqual(outside.read_bytes(), b"outside-owner\n")

    def test_stage_does_not_mutate_destination_and_close_cleans_owned_temp(self) -> None:
        prepared = self._prepared(); parent = self.root / "src"
        try:
            prepared.stage_replace(b"new\n", prepared.observed)
            self.assertEqual(self.target.read_bytes(), b"old\n")
            self.assertEqual(len(list(parent.glob(".hive-replace-*"))), 1)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"old\n")
        self.assertEqual(list(parent.glob(".hive-replace-*")), [])

    def test_mutation_ready_rejects_owner_change_after_staging(self) -> None:
        prepared = self._prepared()
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\n", expected)
            owner = self.root / "src" / "owner.tmp"; owner.write_bytes(b"owner\n"); os.replace(owner, self.target)
            with self.assertRaises(WorkspaceBoundaryError): prepared.mutation_ready(expected)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"owner\n")

    def test_publish_atomically_replaces_with_verified_staged_bytes(self) -> None:
        prepared = self._prepared()
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\n", expected); prepared.mutation_ready(expected)
            state = prepared.publish_replace(expected, lambda: prepared.revalidate_expected(expected))
            self.assertEqual(state, "replaced")
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"new\n")
        self.assertEqual(list((self.root / "src").glob(".hive-replace-*")), [])

    def test_pre_publish_check_failure_preserves_destination_and_cleans_stage(self) -> None:
        prepared = self._prepared()
        try:
            expected = prepared.observed; prepared.stage_replace(b"new\n", expected); prepared.mutation_ready(expected)
            def reject() -> None: raise WorkspaceBoundaryError("cancelled before publication")
            with self.assertRaises(WorkspaceBoundaryError): prepared.publish_replace(expected, reject)
        finally: prepared.close()
        self.assertEqual(self.target.read_bytes(), b"old\n")
        self.assertEqual(list((self.root / "src").glob(".hive-replace-*")), [])


if __name__ == "__main__": unittest.main()
