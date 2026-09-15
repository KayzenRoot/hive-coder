from __future__ import annotations

import json, tempfile, threading, unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from hive_runtime.agent_tasks import ActionKind, AgentTaskRuntime, CheckpointStore, NodeStatus, RecoveryDisposition, StepResult, TaskBudget, TaskNode, TaskPlan, TaskStatus
from hive_runtime.intelligence.capabilities import CapabilityEvidence, EvidenceState, ModelCapabilityRegistry, ModelProfile
from hive_runtime.providers import ModelRouter

KEY=b"k"*32

def router(*caps:str)->ModelRouter:
    registry=ModelCapabilityRegistry()
    registry.register(ModelProfile("opencode-go","alpha",tuple(CapabilityEvidence(c,EvidenceState.VERIFIED,"test") for c in caps)))
    return ModelRouter(registry)

class Ports:
    def __init__(self): self.prompts=[]; self.skills=[]; self.prompt_results=[]; self.skill_results=[]
    def prompt(self,model,node_id,prompt,cancellation):
        self.prompts.append((model.provider,model.model_id,node_id,prompt,cancellation.cancelled()))
        return self.prompt_results.pop(0) if self.prompt_results else StepResult(True,"prompt_ok")
    def skill(self,skill_id,version,node_id,cancellation):
        self.skills.append((skill_id,version,node_id,cancellation.cancelled()))
        return self.skill_results.pop(0) if self.skill_results else StepResult(True,"skill_ok")

def runtime_for(tmp,plan,ports=None,budget=TaskBudget(),model_router=None):
    ports=ports or Ports()
    return AgentTaskRuntime(plan,store=CheckpointStore(tmp,KEY),budget=budget,model_router=model_router or router("tool_calling"),prompt_port=ports.prompt,skill_port=ports.skill),ports

class PlanTests(unittest.TestCase):
    def test_cycle_rejected(self):
        plan=TaskPlan((TaskNode("a",ActionKind.SKILL,depends_on=("b",),skill_id="s",skill_version="1.0.0"),TaskNode("b",ActionKind.SKILL,depends_on=("a",),skill_id="s",skill_version="1.0.0")))
        with self.assertRaises(ValueError): plan.validate()
    def test_prompt_hash_changes_fingerprint(self):
        a=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="one"),)); b=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="two"),))
        self.assertNotEqual(a.fingerprint(),b.fingerprint())
    def test_skill_cannot_smuggle_model_fields(self):
        with self.assertRaises(ValueError): TaskPlan((TaskNode("n",ActionKind.SKILL,skill_id="s",skill_version="1.0.0",prompt="x"),)).validate()

class RuntimeTests(unittest.TestCase):
    def test_dag_executes_in_plan_order_after_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            ports=Ports(); plan=TaskPlan((TaskNode("plan",ActionKind.MODEL_PROMPT,prompt="plan",required_model_capabilities=frozenset({"tool_calling"})),TaskNode("apply",ActionKind.SKILL,depends_on=("plan",),skill_id="safe.skill",skill_version="1.0.0")))
            rt,_=runtime_for(tmp,plan,ports); rt.create("task1"); snap=rt.run_until_blocked()
            self.assertEqual(snap.status,TaskStatus.SUCCEEDED); self.assertEqual([x[2] for x in ports.prompts],["plan"]); self.assertEqual([x[2] for x in ports.skills],["apply"])
    def test_model_router_requirement_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x",required_model_capabilities=frozenset({"vision"})),))
            rt,_=runtime_for(tmp,plan,model_router=router("tool_calling")); rt.create("t"); snap=rt.run_until_blocked()
            self.assertEqual(snap.status,TaskStatus.FAILED); self.assertEqual(dict(snap.node_status)["n"],NodeStatus.FAILED); self.assertEqual(snap.events[-1].code,"exception:LookupError")
    def test_retryable_failure_obeys_node_attempt_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            ports=Ports(); ports.prompt_results=[StepResult(False,"transient",True),StepResult(True,"ok")]
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x",max_attempts=2),)); rt,_=runtime_for(tmp,plan,ports,model_router=router())
            rt.create("t"); snap=rt.run_until_blocked(); self.assertEqual(snap.status,TaskStatus.SUCCEEDED); self.assertEqual(dict(snap.attempts)["n"],2)
    def test_execution_budget_requires_explicit_extension(self):
        with tempfile.TemporaryDirectory() as tmp:
            initial=TaskBudget(1,1); plan=TaskPlan((TaskNode("a",ActionKind.MODEL_PROMPT,prompt="a"),TaskNode("b",ActionKind.MODEL_PROMPT,depends_on=("a",),prompt="b")))
            rt,_=runtime_for(tmp,plan,budget=initial,model_router=router()); rt.create("t"); snap=rt.run_until_blocked()
            self.assertEqual(snap.status,TaskStatus.PAUSED); self.assertEqual(snap.budget,initial)
            with self.assertRaises(ValueError): rt.continue_task()
            rt.extend_budget(TaskBudget(3,1)); rt.continue_task(); self.assertEqual(rt.run_until_blocked().status,TaskStatus.SUCCEEDED)
    def test_resume_cannot_silently_broaden_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); initial=TaskBudget(1,1); rt,_=runtime_for(tmp,plan,budget=initial,model_router=router()); rt.create("t")
            rt2,_=runtime_for(tmp,plan,budget=TaskBudget(20,2),model_router=router())
            with self.assertRaises(ValueError): rt2.resume("t")
    def test_budget_extension_is_monotonic_and_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,budget=TaskBudget(1,0),model_router=router()); rt.create("t")
            with self.assertRaises(ValueError): rt.extend_budget(TaskBudget(2,0))
            rt.pause(); snap=rt.extend_budget(TaskBudget(2,1)); self.assertEqual(snap.budget,TaskBudget(2,1)); self.assertEqual(snap.events[-1].kind,"budget_extended")
    def test_cancelled_task_never_executes(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,ports=runtime_for(tmp,plan,model_router=router()); rt.create("t"); rt.cancel(); snap=rt.run_until_blocked()
            self.assertEqual(snap.status,TaskStatus.CANCELLED); self.assertFalse(ports.prompts)
    def test_pause_requires_explicit_continue(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,model_router=router()); rt.create("t"); rt.pause()
            self.assertEqual(rt.run_until_blocked().status,TaskStatus.PAUSED); self.assertEqual(rt.continue_task().status,TaskStatus.PENDING); self.assertEqual(rt.run_until_blocked().status,TaskStatus.SUCCEEDED)
    def test_inflight_pause_is_preserved_after_node_settles(self):
        with tempfile.TemporaryDirectory() as tmp:
            started=threading.Event(); release=threading.Event()
            class Blocking(Ports):
                def prompt(self,*args): started.set(); release.wait(2); return StepResult(True,"ok")
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,Blocking(),model_router=router()); rt.create("t"); result=[]
            thread=threading.Thread(target=lambda: result.append(rt.run_until_blocked())); thread.start(); self.assertTrue(started.wait(1)); self.assertEqual(rt.pause().status,TaskStatus.PAUSED); release.set(); thread.join(2)
            self.assertFalse(thread.is_alive()); self.assertEqual(result[0].status,TaskStatus.PAUSED); self.assertEqual(dict(result[0].node_status)["n"],NodeStatus.SUCCEEDED)
            rt.continue_task(); self.assertEqual(rt.run_until_blocked().status,TaskStatus.SUCCEEDED)
    def test_snapshot_is_not_mutable_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,model_router=router()); snap=rt.create("t")
            with self.assertRaises(FrozenInstanceError): snap.status=TaskStatus.SUCCEEDED
    def test_invalid_port_result_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            class Bad(Ports):
                def prompt(self,*args): return {"success":True}
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,Bad(),model_router=router()); rt.create("t"); snap=rt.run_until_blocked()
            self.assertEqual(snap.status,TaskStatus.FAILED); self.assertEqual(snap.events[-1].code,"invalid_port_result")
    def test_malformed_result_code_not_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            ports=Ports(); ports.prompt_results=[StepResult(False,"bad code with spaces",False)]
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,ports,model_router=router()); rt.create("t"); snap=rt.run_until_blocked()
            self.assertEqual(snap.events[-1].code,"invalid_result_code")
    def test_exception_message_not_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker="marker-value-not-for-checkpoint"
            class Boom(Ports):
                def prompt(self,*args): raise RuntimeError(marker)
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,Boom(),model_router=router()); rt.create("t"); rt.run_until_blocked()
            raw=Path(tmp,"t.json").read_text(); self.assertNotIn(marker,raw); self.assertIn("exception:RuntimeError",raw)
    def test_raw_prompt_is_not_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker="prompt-marker-not-for-checkpoint"; plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt=marker),)); rt,_=runtime_for(tmp,plan,model_router=router()); rt.create("t")
            self.assertNotIn(marker,Path(tmp,"t.json").read_text())

class RecoveryTests(unittest.TestCase):
    def test_crashed_model_prompt_reissues_only_with_remaining_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            class Crash(Ports):
                def prompt(self,*args): raise SystemExit(9)
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x",max_attempts=2),)); rt,_=runtime_for(tmp,plan,Crash(),model_router=router()); rt.create("t")
            with self.assertRaises(SystemExit): rt.run_until_blocked()
            rt2,_=runtime_for(tmp,plan,Ports(),model_router=router()); snap=rt2.resume("t"); self.assertEqual(dict(snap.node_status)["n"],NodeStatus.PENDING); self.assertEqual(rt2.run_until_blocked().status,TaskStatus.SUCCEEDED)
    def test_crashed_skill_requires_host_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            class Crash(Ports):
                def skill(self,*args): raise SystemExit(8)
            plan=TaskPlan((TaskNode("n",ActionKind.SKILL,skill_id="safe.skill",skill_version="1.0.0",max_attempts=2),)); rt,_=runtime_for(tmp,plan,Crash()); rt.create("t")
            with self.assertRaises(SystemExit): rt.run_until_blocked()
            rt2,ports=runtime_for(tmp,plan,Ports()); snap=rt2.resume("t"); self.assertEqual(snap.status,TaskStatus.PAUSED); self.assertEqual(dict(snap.node_status)["n"],NodeStatus.INTERRUPTED); self.assertFalse(ports.skills)
            rt2.recover_interrupted("n",RecoveryDisposition.RETRY); self.assertEqual(rt2.run_until_blocked().status,TaskStatus.SUCCEEDED)
    def test_interrupted_skill_cannot_retry_after_attempt_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            class Crash(Ports):
                def skill(self,*args): raise SystemExit(8)
            plan=TaskPlan((TaskNode("n",ActionKind.SKILL,skill_id="s",skill_version="1.0.0",max_attempts=1),)); rt,_=runtime_for(tmp,plan,Crash()); rt.create("t")
            with self.assertRaises(SystemExit): rt.run_until_blocked()
            rt2,_=runtime_for(tmp,plan); rt2.resume("t")
            with self.assertRaises(ValueError): rt2.recover_interrupted("n",RecoveryDisposition.RETRY)

class CheckpointTests(unittest.TestCase):
    def test_hmac_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="x"),)); rt,_=runtime_for(tmp,plan,model_router=router()); rt.create("t")
            path=Path(tmp,"t.json"); data=json.loads(path.read_text()); data["payload"]["status"]="succeeded"; path.write_text(json.dumps(data))
            rt2,_=runtime_for(tmp,plan,model_router=router())
            with self.assertRaises(ValueError): rt2.resume("t")
    def test_plan_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="a"),)); b=TaskPlan((TaskNode("n",ActionKind.MODEL_PROMPT,prompt="b"),))
            rt,_=runtime_for(tmp,a,model_router=router()); rt.create("t"); rt2,_=runtime_for(tmp,b,model_router=router())
            with self.assertRaises(ValueError): rt2.resume("t")
    def test_checkpoint_contains_no_authority_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan=TaskPlan((TaskNode("n",ActionKind.SKILL,skill_id="s",skill_version="1.0.0"),)); rt,_=runtime_for(tmp,plan); rt.create("t"); raw=Path(tmp,"t.json").read_text().lower()
            for forbidden in ("approval_token","capability_grant","skill_content","model_output"):
                self.assertNotIn(forbidden,raw)

if __name__=="__main__": unittest.main()
