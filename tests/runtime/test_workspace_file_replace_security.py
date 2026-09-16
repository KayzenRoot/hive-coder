from __future__ import annotations

"""Adversarial contract for HCODER-WO-0022."""
import hashlib, os, tempfile, unittest
from pathlib import Path
from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.workspace_files import WorkspaceFileCapability

class WorkspaceReplaceSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/"src").mkdir();self.target=self.root/"src"/"module.py";self.target.write_bytes(b"old\n");self.plane=PermissionControlPlane()
    def tearDown(self):self.temp.cleanup()
    def capability(self):return WorkspaceFileCapability(self.root,self.plane)
    def test_dot_git_is_never_a_replace_target(self):
        (self.root/".git").mkdir();(self.root/".git"/"config").write_bytes(b"old");cap=self.capability()
        try:
            with self.assertRaises(Exception):cap.prepare_replace_request("session-1",".git/config",b"new")
        finally:cap.close()
    def test_traversal_is_never_a_replace_target(self):
        cap=self.capability()
        try:
            with self.assertRaises(Exception):cap.prepare_replace_request("session-1","../outside.txt",b"new")
        finally:cap.close()
    @unittest.skipIf(os.name=="nt","POSIX symlink fixture")
    def test_symlink_target_is_rejected(self):
        outside=self.root/"outside.txt";outside.write_bytes(b"owner");link=self.root/"src"/"link.py";link.symlink_to(outside);cap=self.capability()
        try:
            with self.assertRaises(Exception):cap.prepare_replace_request("session-1","src/link.py",b"new")
        finally:cap.close()
        self.assertEqual(outside.read_bytes(),b"owner")
    @unittest.skipIf(os.name=="nt","POSIX symlink fixture")
    def test_symlink_parent_is_rejected(self):
        outside=self.root/"outside-dir";outside.mkdir();(outside/"module.py").write_bytes(b"owner");(self.root/"linked").symlink_to(outside,target_is_directory=True);cap=self.capability()
        try:
            with self.assertRaises(Exception):cap.prepare_replace_request("session-1","linked/module.py",b"new")
        finally:cap.close()
        self.assertEqual((outside/"module.py").read_bytes(),b"owner")
    def test_old_content_change_after_approval_must_fail_closed(self):
        cap=self.capability()
        try:
            request=cap.prepare_replace_request("session-1","src/module.py",b"approved-new\n");self.target.write_bytes(b"concurrent-owner\n")
            with self.assertRaises(Exception):cap.replace_bytes(request,b"approved-new\n",permit_token="invalid-prebuilt-token")
        finally:cap.close()
        self.assertEqual(self.target.read_bytes(),b"concurrent-owner\n")
    def test_wrong_new_content_must_fail_before_mutation(self):
        cap=self.capability()
        try:
            request=cap.prepare_replace_request("session-1","src/module.py",b"approved-new\n")
            with self.assertRaises(Exception):cap.replace_bytes(request,b"different-new\n",permit_token="invalid-prebuilt-token")
        finally:cap.close()
        self.assertEqual(self.target.read_bytes(),b"old\n")
    @unittest.skipIf(os.name=="nt","POSIX native staging fixture")
    def test_stage_pathname_swap_is_rejected_and_attacker_path_is_not_cleaned(self):
        """A swapped temp pathname must never be published or deleted as Hive-owned."""
        from hive_runtime.workspace_replace_posix import PosixPreparedReplace
        cap=self.capability();prepared=None
        try:
            prepared=cap._backend.prepare_replace("src/module.py")
            expected=prepared.observed;prepared.stage_replace(b"approved-new\n",expected)
            stage_name=prepared._stage_name
            self.assertIsNotNone(stage_name)
            stage_path=self.root/"src"/stage_name
            displaced=self.root/"src"/(stage_name+".owned")
            os.rename(stage_path,displaced)
            stage_path.write_bytes(b"attacker-controlled\n")
            with self.assertRaises(Exception):prepared.mutation_ready(expected)
            self.assertEqual(self.target.read_bytes(),b"old\n")
            self.assertEqual(stage_path.read_bytes(),b"attacker-controlled\n")
            prepared.close();prepared=None
            self.assertTrue(stage_path.exists(),"cleanup must not unlink a swapped attacker pathname")
            self.assertEqual(stage_path.read_bytes(),b"attacker-controlled\n")
        finally:
            if prepared is not None:prepared.close()
            cap.close()
    @unittest.skipIf(os.name=="nt","POSIX native staging fixture")
    def test_stage_pathname_bytes_are_revalidated_before_mutation_ready(self):
        """The live staging pathname must still contain the exact approved staged bytes."""
        cap=self.capability();prepared=None
        try:
            prepared=cap._backend.prepare_replace("src/module.py");expected=prepared.observed;prepared.stage_replace(b"approved-new\n",expected)
            stage_path=self.root/"src"/prepared._stage_name
            # Mutating through the pathname changes the same inode, so both pinned and live
            # digest checks must reject it before publication.
            stage_path.write_bytes(b"tampered\n")
            with self.assertRaises(Exception):prepared.mutation_ready(expected)
            self.assertEqual(self.target.read_bytes(),b"old\n")
        finally:
            if prepared is not None:prepared.close()
            cap.close()

if __name__=="__main__":unittest.main()