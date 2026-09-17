from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.git_loose_object_transaction import prepare_loose_blob
from hive_runtime.git_object_private_prep import PRIVATE_OBJECT_PREP_CONTRACT, PrivateObjectPreparer
from hive_runtime.git_stage import GitStagePreparation, GitStageUnavailableError
from hive_runtime.git_stage_contract import GitStageObservedState, GitStageWorktreeState
from hive_runtime.git_stage_plan import STAGE_PLAN_CONTRACT, PreAuthorityStageExecutor, bind_stage_plan


def _repo(root:Path)->None:
    git=root/".git";(git/"objects"/"info").mkdir(parents=True);(git/"objects"/"pack").mkdir();(git/"config").write_text("[core]\n repositoryformatversion = 0\n",encoding="ascii")

def _stage(content:bytes)->GitStagePreparation:
    state=GitStageWorktreeState("src/a.py","posix:1:2:33188",hashlib.sha256(content).hexdigest(),len(content))
    observed=GitStageObservedState("posix-repo:1:2","1"*40,"absent","absent","absent",(state,))
    return GitStagePreparation(observed,("src/a.py",))

@unittest.skipIf(os.name=="nt","POSIX pre-authority frontier proof")
class GitStagePrebuiltFrontierTests(unittest.TestCase):
    def test_private_plan_binds_exact_compressed_candidate_without_writing(self)->None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_repo(root);prepared,compressed=prepare_loose_blob(root,b"source");before=sorted(str(p.relative_to(root)) for p in root.rglob("*"));planner=PrivateObjectPreparer();plan=planner.plan(prepared,compressed);after=sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            self.assertEqual(plan.contract,PRIVATE_OBJECT_PREP_CONTRACT);self.assertEqual(plan.oid,prepared.candidate.oid);self.assertEqual(plan.compressed_sha256,prepared.compressed_sha256);self.assertEqual(before,after);self.assertFalse(planner.mutation_authority_enabled)
            with self.assertRaises(GitStageUnavailableError):planner.materialize_private_temp(plan,compressed)
            with self.assertRaises(GitStageUnavailableError):planner.publish(plan)
    def test_private_plan_rejects_changed_compressed_bytes(self)->None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_repo(root);prepared,compressed=prepare_loose_blob(root,b"source")
            with self.assertRaises(ValueError):PrivateObjectPreparer().plan(prepared,compressed+b"x")
    def test_stage_plan_binds_worktree_digest_to_exact_blob_oid(self)->None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_repo(root);content=b"source";obj,_=prepare_loose_blob(root,content);plan=bind_stage_plan(_stage(content),(obj,))
            self.assertEqual(plan.contract,STAGE_PLAN_CONTRACT);self.assertEqual(plan.paths[0].path,"src/a.py");self.assertEqual(plan.paths[0].blob_oid,obj.candidate.oid);self.assertEqual(plan.paths[0].worktree_sha256,hashlib.sha256(content).hexdigest())
    def test_stage_plan_rejects_unbound_or_extra_object_candidates(self)->None:
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_repo(root);good,_=prepare_loose_blob(root,b"source");bad,_=prepare_loose_blob(root,b"other")
            with self.assertRaises(ValueError):bind_stage_plan(_stage(b"source"),(bad,))
            with self.assertRaises(ValueError):bind_stage_plan(_stage(b"source"),(good,bad))
    def test_executor_remains_fail_closed_even_with_token_shaped_input(self)->None:
        executor=PreAuthorityStageExecutor();self.assertFalse(executor.mutation_authority_enabled)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);_repo(root);obj,_=prepare_loose_blob(root,b"source");plan=bind_stage_plan(_stage(b"source"),(obj,))
            with self.assertRaises(GitStageUnavailableError):executor.publish(plan,permit_token="not-a-real-permit")

if __name__=="__main__":unittest.main()
