from __future__ import annotations
"""Adversarial and permit-ordering contract for HCODER-WO-0022."""
import os,tempfile,unittest
from pathlib import Path
from unittest import mock
from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.control_policy import CapabilityRule,ControlPolicy
from hive_runtime.control_types import Capability
from hive_runtime.workspace_files import WorkspaceFileCapability
from hive_runtime.workspace_replace_contract import REPLACE_ACTION

def replace_policy(root):return ControlPolicy.build([CapabilityRule.build(Capability.FILESYSTEM_WRITE,allowed_actions={REPLACE_ACTION},allowed_workspace_roots={str(root)})])
def authorize_replace(plane,cap,session,path,content):
    request=cap.prepare_replace_request(session,path,content);challenge=plane.create_approval_challenge(request);approval=plane.approve_challenge_from_trusted_ui(challenge.challenge_id,session_id=session);permit=plane.authorize(request,approval_token=approval);return request,permit.token
class WorkspaceReplaceSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);(self.root/"src").mkdir();self.target=self.root/"src"/"module.py";self.target.write_bytes(b"old\n");self.plane=PermissionControlPlane(token_key=b"r"*32)
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
        cap=self.capability();prepared=None
        try:
            prepared=cap._backend.prepare_replace("src/module.py");expected=prepared.observed;prepared.stage_replace(b"approved-new\n",expected);stage_name=prepared._stage_name;stage_path=self.root/"src"/stage_name;displaced=self.root/"src"/(stage_name+".owned");os.rename(stage_path,displaced);stage_path.write_bytes(b"attacker-controlled\n")
            with self.assertRaises(Exception):prepared.mutation_ready(expected)
            self.assertEqual(self.target.read_bytes(),b"old\n");prepared.close();prepared=None;self.assertEqual(stage_path.read_bytes(),b"attacker-controlled\n")
        finally:
            if prepared is not None:prepared.close()
            cap.close()
    @unittest.skipIf(os.name=="nt","POSIX native staging fixture")
    def test_stage_pathname_bytes_are_revalidated_before_mutation_ready(self):
        cap=self.capability();prepared=None
        try:
            prepared=cap._backend.prepare_replace("src/module.py");expected=prepared.observed;prepared.stage_replace(b"approved-new\n",expected);(self.root/"src"/prepared._stage_name).write_bytes(b"tampered\n")
            with self.assertRaises(Exception):prepared.mutation_ready(expected)
            self.assertEqual(self.target.read_bytes(),b"old\n")
        finally:
            if prepared is not None:prepared.close()
            cap.close()
    def _authorized(self):
        cap=self.capability();session=self.plane.create_session(replace_policy(self.root),duration_seconds=60);request,token=authorize_replace(self.plane,cap,session,"src/module.py",b"approved-new\n");return cap,request,token
    def test_stale_state_before_mutation_ready_does_not_consume_permit(self):
        cap,request,token=self._authorized()
        try:
            self.target.write_bytes(b"concurrent-owner\n")
            with self.assertRaises(Exception):cap.replace_bytes(request,b"approved-new\n",permit_token=token)
            consumed=[e for e in self.plane.audit_events() if e.event_type=="control.execution_permit_consumed"]
            self.assertEqual(consumed,[])
        finally:cap.close()
    def test_staging_failure_does_not_consume_permit(self):
        cap,request,token=self._authorized()
        try:
            prepared=cap._backend.prepare_replace("src/module.py")
            with mock.patch.object(cap._backend,"prepare_replace",return_value=prepared),mock.patch.object(prepared,"stage_replace",side_effect=RuntimeError("synthetic staging failure")):
                with self.assertRaises(Exception):cap.replace_bytes(request,b"approved-new\n",permit_token=token)
            self.assertFalse(any(e.event_type=="control.execution_permit_consumed" for e in self.plane.audit_events()))
        finally:cap.close()
    def test_unsupported_mutation_ready_does_not_consume_permit(self):
        cap,request,token=self._authorized()
        try:
            prepared=cap._backend.prepare_replace("src/module.py")
            with mock.patch.object(cap._backend,"prepare_replace",return_value=prepared),mock.patch.object(prepared,"mutation_ready",side_effect=NotImplementedError("unsupported publication")):
                with self.assertRaises(NotImplementedError):cap.replace_bytes(request,b"approved-new\n",permit_token=token)
            self.assertFalse(any(e.event_type=="control.execution_permit_consumed" for e in self.plane.audit_events()))
        finally:cap.close()
    def test_permit_is_consumed_after_mutation_ready_and_before_publish(self):
        cap,request,token=self._authorized();events=[];prepared=cap._backend.prepare_replace("src/module.py")
        original_ready=prepared.mutation_ready;original_consume=self.plane.consume_execution_permit;original_publish=prepared.publish_replace
        def ready(expected):result=original_ready(expected);events.append("ready");return result
        def consume(value,req):events.append("consume");return original_consume(value,req)
        def publish(expected,check):events.append("publish");return original_publish(expected,check)
        try:
            with mock.patch.object(cap._backend,"prepare_replace",return_value=prepared),mock.patch.object(prepared,"mutation_ready",side_effect=ready),mock.patch.object(self.plane,"consume_execution_permit",side_effect=consume),mock.patch.object(prepared,"publish_replace",side_effect=publish):cap.replace_bytes(request,b"approved-new\n",permit_token=token)
            self.assertEqual(events,["ready","consume","publish"]);self.assertEqual(self.target.read_bytes(),b"approved-new\n")
        finally:cap.close()
if __name__=="__main__":unittest.main()