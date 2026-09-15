"""Resumable Hive Agent Task Runtime.

Checkpoints govern workflow progress only. They never persist credentials, permission
grants, Cua permits, skill content, prompts or model output.
"""
from __future__ import annotations

import hashlib, hmac, json, os, re, tempfile, threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping, Protocol

from .intelligence.capabilities import CapabilityRequest, ModelProfile
from .providers import ModelRouter

CHECKPOINT_SCHEMA = "hive-agent-task-checkpoint-v1"
_SAFE_CODE = re.compile(r"^[a-zA-Z0-9_.:-]{1,80}$")
_SAFE_ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,128}$")


class ActionKind(str, Enum): MODEL_PROMPT = "model_prompt"; SKILL = "skill"
class TaskStatus(str, Enum):
    PENDING="pending"; RUNNING="running"; PAUSED="paused"; SUCCEEDED="succeeded"; FAILED="failed"; CANCELLED="cancelled"
class NodeStatus(str, Enum):
    PENDING="pending"; RUNNING="running"; INTERRUPTED="interrupted"; SUCCEEDED="succeeded"; FAILED="failed"
class RecoveryDisposition(str, Enum): RETRY="retry"; FAIL="fail"


@dataclass(frozen=True)
class TaskNode:
    node_id: str
    action: ActionKind
    depends_on: tuple[str, ...] = ()
    required_model_capabilities: frozenset[str] = frozenset()
    provider: str | None = None
    prompt: str | None = None
    skill_id: str | None = None
    skill_version: str | None = None
    max_attempts: int = 1

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.node_id): raise ValueError("invalid node_id")
        if not 1 <= self.max_attempts <= 20: raise ValueError("max_attempts must be between 1 and 20")
        if len(set(self.depends_on)) != len(self.depends_on) or self.node_id in self.depends_on: raise ValueError("invalid dependencies")
        if any(not _SAFE_ID.fullmatch(item) for item in self.depends_on): raise ValueError("invalid dependency id")
        if any(not cap.strip() for cap in self.required_model_capabilities): raise ValueError("empty model capability")
        if self.provider is not None and not self.provider.strip(): raise ValueError("empty provider")
        if self.action is ActionKind.MODEL_PROMPT:
            if not isinstance(self.prompt, str) or not self.prompt.strip(): raise ValueError("model_prompt requires non-empty prompt")
            if self.skill_id is not None or self.skill_version is not None: raise ValueError("model_prompt cannot declare skill identity")
        elif self.action is ActionKind.SKILL:
            if not self.skill_id or not self.skill_version: raise ValueError("skill action requires skill_id and skill_version")
            if self.prompt is not None or self.required_model_capabilities or self.provider is not None: raise ValueError("skill action cannot carry model fields")
        else: raise ValueError("unsupported action kind")


@dataclass(frozen=True)
class TaskPlan:
    nodes: tuple[TaskNode, ...]
    def validate(self) -> None:
        if not self.nodes: raise ValueError("task plan requires at least one node")
        ids=[n.node_id for n in self.nodes]
        if len(ids)!=len(set(ids)): raise ValueError("duplicate node id")
        known=set(ids)
        for node in self.nodes:
            node.validate()
            if not set(node.depends_on).issubset(known): raise ValueError("unknown dependency")
        graph={n.node_id:n.depends_on for n in self.nodes}; visiting=set(); visited=set()
        def visit(node_id:str)->None:
            if node_id in visited: return
            if node_id in visiting: raise ValueError("task plan contains a dependency cycle")
            visiting.add(node_id)
            for dep in graph[node_id]: visit(dep)
            visiting.remove(node_id); visited.add(node_id)
        for node_id in ids: visit(node_id)
    def fingerprint(self)->str:
        self.validate(); canonical=[]
        for n in self.nodes:
            canonical.append({"node_id":n.node_id,"action":n.action.value,"depends_on":list(n.depends_on),
                "required_model_capabilities":sorted(n.required_model_capabilities),"provider":n.provider,
                "prompt_sha256":hashlib.sha256((n.prompt or "").encode()).hexdigest(),"skill_id":n.skill_id,
                "skill_version":n.skill_version,"max_attempts":n.max_attempts})
        return hashlib.sha256(json.dumps(canonical,sort_keys=True,separators=(",",":")).encode()).hexdigest()


@dataclass(frozen=True)
class TaskBudget:
    max_executions:int=100; max_failures:int=10
    def validate(self)->None:
        if not 1<=self.max_executions<=100_000: raise ValueError("invalid max_executions")
        if not 0<=self.max_failures<=self.max_executions: raise ValueError("invalid max_failures")


@dataclass(frozen=True)
class StepResult:
    success:bool; code:str="ok"; retryable:bool=False
    def normalized_code(self)->str: return self.code if isinstance(self.code,str) and _SAFE_CODE.fullmatch(self.code) else "invalid_result_code"


@dataclass(frozen=True)
class TaskEvent:
    sequence:int; kind:str; node_id:str|None=None; code:str="ok"


@dataclass
class _TaskState:
    task_id:str; plan_fingerprint:str; status:TaskStatus; node_status:dict[str,NodeStatus]; attempts:dict[str,int]
    max_executions:int; max_failures:int; executions:int=0; failures:int=0; sequence:int=0; events:list[TaskEvent]=field(default_factory=list)


@dataclass(frozen=True)
class TaskSnapshot:
    task_id:str; plan_fingerprint:str; status:TaskStatus; node_status:tuple[tuple[str,NodeStatus],...]; attempts:tuple[tuple[str,int],...]
    budget:TaskBudget; executions:int; failures:int; sequence:int; events:tuple[TaskEvent,...]


class CancellationToken:
    def __init__(self)->None: self._event=threading.Event()
    def cancel(self)->None: self._event.set()
    def cancelled(self)->bool: return self._event.is_set()


class PromptExecutionPort(Protocol):
    def __call__(self,model:ModelProfile,node_id:str,prompt:str,cancellation:CancellationToken)->StepResult: ...
class SkillExecutionPort(Protocol):
    def __call__(self,skill_id:str,skill_version:str,node_id:str,cancellation:CancellationToken)->StepResult: ...


class CheckpointStore:
    """HMAC-authenticated atomic checkpoint store. Integrity key belongs to trusted host."""
    def __init__(self,directory:str|os.PathLike[str],integrity_key:bytes)->None:
        if not isinstance(integrity_key,bytes) or len(integrity_key)<32: raise ValueError("integrity_key must contain at least 32 bytes")
        self.directory=Path(directory); self._key=bytes(integrity_key)
    def _path(self,task_id:str)->Path:
        if not _SAFE_ID.fullmatch(task_id): raise ValueError("invalid task_id")
        return self.directory/f"{task_id}.json"
    def exists(self,task_id:str)->bool: return self._path(task_id).exists()
    def save(self,state:_TaskState)->None:
        self.directory.mkdir(parents=True,exist_ok=True); payload=self._to_payload(state)
        canonical=json.dumps(payload,sort_keys=True,separators=(",",":")); envelope={"schema":CHECKPOINT_SCHEMA,"payload":payload,
            "hmac_sha256":hmac.new(self._key,canonical.encode(),hashlib.sha256).hexdigest()}
        fd,tmp=tempfile.mkstemp(prefix=f".{state.task_id}.",suffix=".tmp",dir=str(self.directory)); target=self._path(state.task_id)
        try:
            with os.fdopen(fd,"w",encoding="utf-8",newline="\n") as handle:
                handle.write(json.dumps(envelope,sort_keys=True,separators=(",",":"))); handle.flush(); os.fsync(handle.fileno())
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    def load(self,task_id:str,expected_plan_fingerprint:str)->_TaskState:
        envelope=json.loads(self._path(task_id).read_text(encoding="utf-8"))
        if not isinstance(envelope,dict) or envelope.get("schema")!=CHECKPOINT_SCHEMA or not isinstance(envelope.get("payload"),dict): raise ValueError("invalid checkpoint envelope")
        payload=envelope["payload"]; canonical=json.dumps(payload,sort_keys=True,separators=(",",":")); expected=hmac.new(self._key,canonical.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(str(envelope.get("hmac_sha256","")),expected): raise ValueError("checkpoint integrity verification failed")
        if payload.get("task_id")!=task_id or payload.get("plan_fingerprint")!=expected_plan_fingerprint: raise ValueError("checkpoint task/plan mismatch")
        return self._from_payload(payload)
    @staticmethod
    def _to_payload(s:_TaskState)->dict:
        return {"task_id":s.task_id,"plan_fingerprint":s.plan_fingerprint,"status":s.status.value,
            "node_status":{k:v.value for k,v in sorted(s.node_status.items())},"attempts":dict(sorted(s.attempts.items())),
            "budget":{"max_executions":s.max_executions,"max_failures":s.max_failures},
            "executions":s.executions,"failures":s.failures,"sequence":s.sequence,
            "events":[{"sequence":e.sequence,"kind":e.kind,"node_id":e.node_id,"code":e.code} for e in s.events]}
    @staticmethod
    def _from_payload(p:Mapping[str,object])->_TaskState:
        try:
            task_id=str(p["task_id"]); ns=p["node_status"]; attempts=p["attempts"]; raw_events=p["events"]; raw_budget=p["budget"]
            if not _SAFE_ID.fullmatch(task_id) or not isinstance(ns,dict) or not isinstance(attempts,dict) or not isinstance(raw_events,list) or not isinstance(raw_budget,dict): raise ValueError
            budget=TaskBudget(int(raw_budget["max_executions"]),int(raw_budget["max_failures"])); budget.validate(); events=[]
            for raw in raw_events:
                if not isinstance(raw,dict): raise ValueError
                node_id=raw.get("node_id")
                if node_id is not None and (not isinstance(node_id,str) or not _SAFE_ID.fullmatch(node_id)): raise ValueError
                kind=str(raw["kind"]); code=str(raw.get("code","ok"))
                if not _SAFE_CODE.fullmatch(kind) or not _SAFE_CODE.fullmatch(code): raise ValueError
                events.append(TaskEvent(int(raw["sequence"]),kind,node_id,code))
            state=_TaskState(task_id,str(p["plan_fingerprint"]),TaskStatus(str(p["status"])),{str(k):NodeStatus(str(v)) for k,v in ns.items()},
                {str(k):int(v) for k,v in attempts.items()},budget.max_executions,budget.max_failures,int(p["executions"]),int(p["failures"]),int(p["sequence"]),events)
        except (KeyError,TypeError,ValueError) as exc: raise ValueError("invalid checkpoint payload") from exc
        if state.executions<0 or state.failures<0 or state.sequence<0: raise ValueError("invalid checkpoint counters")
        if any(not _SAFE_ID.fullmatch(k) or v<0 for k,v in state.attempts.items()): raise ValueError("invalid checkpoint attempts")
        if any(not _SAFE_ID.fullmatch(k) for k in state.node_status): raise ValueError("invalid checkpoint node")
        if state.executions!=sum(state.attempts.values()): raise ValueError("checkpoint execution/attempt counters disagree")
        if len(state.events)!=state.sequence or any(e.sequence!=i+1 for i,e in enumerate(state.events)): raise ValueError("invalid checkpoint event sequence")
        return state


class AgentTaskRuntime:
    """Sequential resumable task engine. External ports remain the sole execution authority."""
    def __init__(self,plan:TaskPlan,*,store:CheckpointStore,budget:TaskBudget,model_router:ModelRouter,
                 prompt_port:PromptExecutionPort,skill_port:SkillExecutionPort)->None:
        plan.validate(); budget.validate(); self.plan=plan; self._fingerprint=plan.fingerprint(); self.store=store; self._configured_budget=budget
        self.model_router=model_router; self.prompt_port=prompt_port; self.skill_port=skill_port; self.cancellation=CancellationToken()
        self._lock=threading.RLock(); self._state:_TaskState|None=None
    def snapshot(self)->TaskSnapshot:
        with self._lock:
            s=self._require_state(); return TaskSnapshot(s.task_id,s.plan_fingerprint,s.status,tuple(sorted(s.node_status.items())),tuple(sorted(s.attempts.items())),TaskBudget(s.max_executions,s.max_failures),s.executions,s.failures,s.sequence,tuple(s.events))
    def create(self,task_id:str)->TaskSnapshot:
        with self._lock:
            if self.store.exists(task_id): raise FileExistsError("task checkpoint already exists")
            b=self._configured_budget
            self._state=_TaskState(task_id,self._fingerprint,TaskStatus.PENDING,{n.node_id:NodeStatus.PENDING for n in self.plan.nodes},{n.node_id:0 for n in self.plan.nodes},b.max_executions,b.max_failures)
            self._event("task_created"); self.store.save(self._state); return self.snapshot()
    def resume(self,task_id:str)->TaskSnapshot:
        with self._lock:
            s=self.store.load(task_id,self._fingerprint); persisted=TaskBudget(s.max_executions,s.max_failures)
            if persisted!=self._configured_budget: raise ValueError("runtime budget does not match authenticated checkpoint")
            plan_ids={n.node_id for n in self.plan.nodes}
            if set(s.node_status)!=plan_ids or set(s.attempts)!=plan_ids: raise ValueError("checkpoint nodes do not match task plan")
            actions={n.node_id:n for n in self.plan.nodes}
            if any(s.attempts[n.node_id]>n.max_attempts for n in self.plan.nodes): raise ValueError("checkpoint exceeds node attempt budget")
            if s.status in {TaskStatus.SUCCEEDED,TaskStatus.FAILED,TaskStatus.CANCELLED}:
                self._state=s; return self.snapshot()
            interrupted=False
            for node_id,status in tuple(s.node_status.items()):
                if status is NodeStatus.RUNNING:
                    node=actions[node_id]
                    if node.action is ActionKind.MODEL_PROMPT and s.attempts[node_id]<node.max_attempts: s.node_status[node_id]=NodeStatus.PENDING
                    else: s.node_status[node_id]=NodeStatus.INTERRUPTED; interrupted=True
            if interrupted: s.status=TaskStatus.PAUSED
            elif s.status is TaskStatus.RUNNING: s.status=TaskStatus.PENDING
            self._state=s; self._event("task_resumed",code="recovery_required" if interrupted else "ok"); self.store.save(s); return self.snapshot()
    def continue_task(self)->TaskSnapshot:
        with self._lock:
            s=self._require_state()
            if s.status is not TaskStatus.PAUSED: raise ValueError("task is not paused")
            if any(v is NodeStatus.INTERRUPTED for v in s.node_status.values()): raise ValueError("interrupted nodes require recovery disposition")
            if s.executions>=s.max_executions or s.failures>s.max_failures: raise ValueError("budget extension required")
            s.status=TaskStatus.PENDING; self._event("task_continued"); self.store.save(s); return self.snapshot()
    def extend_budget(self,new_budget:TaskBudget)->TaskSnapshot:
        new_budget.validate()
        with self._lock:
            s=self._require_state(); current=TaskBudget(s.max_executions,s.max_failures)
            if s.status is not TaskStatus.PAUSED: raise ValueError("budget may only be extended while task is paused")
            if any(v is NodeStatus.INTERRUPTED for v in s.node_status.values()): raise ValueError("resolve interrupted nodes before budget extension")
            if new_budget.max_executions<current.max_executions or new_budget.max_failures<current.max_failures or new_budget==current: raise ValueError("budget extension must be monotonic and explicit")
            s.max_executions=new_budget.max_executions; s.max_failures=new_budget.max_failures; self._configured_budget=new_budget
            self._event("budget_extended",code=f"exec:{new_budget.max_executions}")
            self.store.save(s); return self.snapshot()
    def recover_interrupted(self,node_id:str,disposition:RecoveryDisposition)->TaskSnapshot:
        with self._lock:
            s=self._require_state()
            if s.node_status.get(node_id) is not NodeStatus.INTERRUPTED: raise ValueError("node is not interrupted")
            if disposition is RecoveryDisposition.RETRY:
                node=next(n for n in self.plan.nodes if n.node_id==node_id)
                if s.attempts[node_id]>=node.max_attempts: raise ValueError("retry budget for node exhausted")
                s.node_status[node_id]=NodeStatus.PENDING; self._event("interrupted_recovery",node_id,"retry")
            elif disposition is RecoveryDisposition.FAIL:
                s.node_status[node_id]=NodeStatus.FAILED; s.failures+=1; s.status=TaskStatus.FAILED; self._event("interrupted_recovery",node_id,"fail")
            else: raise ValueError("unsupported recovery disposition")
            if not any(v is NodeStatus.INTERRUPTED for v in s.node_status.values()) and s.status is TaskStatus.PAUSED: s.status=TaskStatus.PENDING
            self.store.save(s); return self.snapshot()
    def pause(self)->TaskSnapshot:
        with self._lock:
            s=self._require_state()
            if s.status not in {TaskStatus.SUCCEEDED,TaskStatus.FAILED,TaskStatus.CANCELLED}:
                s.status=TaskStatus.PAUSED; self._event("task_paused"); self.store.save(s)
            return self.snapshot()
    def cancel(self)->TaskSnapshot:
        self.cancellation.cancel()
        with self._lock:
            s=self._require_state()
            if s.status not in {TaskStatus.SUCCEEDED,TaskStatus.FAILED,TaskStatus.CANCELLED}:
                s.status=TaskStatus.CANCELLED
                for node_id,status in tuple(s.node_status.items()):
                    if status is NodeStatus.RUNNING: s.node_status[node_id]=NodeStatus.INTERRUPTED
                self._event("task_cancelled"); self.store.save(s)
            return self.snapshot()
    def run_until_blocked(self)->TaskSnapshot:
        while True:
            with self._lock:
                s=self._require_state()
                if s.status in {TaskStatus.SUCCEEDED,TaskStatus.FAILED,TaskStatus.CANCELLED,TaskStatus.PAUSED}: return self.snapshot()
                if self.cancellation.cancelled(): s.status=TaskStatus.CANCELLED; self._event("task_cancelled"); self.store.save(s); return self.snapshot()
                if s.executions>=s.max_executions or s.failures>s.max_failures:
                    s.status=TaskStatus.PAUSED; self._event("budget_exhausted"); self.store.save(s); return self.snapshot()
                node=self._next_runnable()
                if node is None:
                    if all(v is NodeStatus.SUCCEEDED for v in s.node_status.values()): s.status=TaskStatus.SUCCEEDED; self._event("task_succeeded")
                    elif any(v is NodeStatus.INTERRUPTED for v in s.node_status.values()): s.status=TaskStatus.PAUSED; self._event("recovery_required")
                    else: s.status=TaskStatus.FAILED; self._event("task_failed",code="dependency_block")
                    self.store.save(s); return self.snapshot()
                if s.attempts[node.node_id]>=node.max_attempts:
                    s.node_status[node.node_id]=NodeStatus.FAILED; s.status=TaskStatus.FAILED; self._event("node_failed",node.node_id,"attempt_budget"); self.store.save(s); return self.snapshot()
                s.status=TaskStatus.RUNNING; s.node_status[node.node_id]=NodeStatus.RUNNING; s.attempts[node.node_id]+=1; s.executions+=1
                self._event("node_started",node.node_id); self.store.save(s)
            result=self._execute(node)
            with self._lock:
                s=self._require_state()
                if s.status is TaskStatus.CANCELLED:
                    if s.node_status.get(node.node_id) is NodeStatus.RUNNING: s.node_status[node.node_id]=NodeStatus.INTERRUPTED
                    self._event("node_cancelled",node.node_id); self.store.save(s); return self.snapshot()
                paused=s.status is TaskStatus.PAUSED; code=result.normalized_code()
                if result.success:
                    s.node_status[node.node_id]=NodeStatus.SUCCEEDED; s.status=TaskStatus.PAUSED if paused else TaskStatus.PENDING; self._event("node_succeeded",node.node_id,code)
                else:
                    s.failures+=1; retry=result.retryable and s.attempts[node.node_id]<node.max_attempts and s.failures<=s.max_failures
                    s.node_status[node.node_id]=NodeStatus.PENDING if retry else NodeStatus.FAILED
                    s.status=(TaskStatus.PAUSED if paused else TaskStatus.PENDING) if retry else TaskStatus.FAILED
                    self._event("node_retry" if retry else "node_failed",node.node_id,code)
                self.store.save(s)
                if s.status in {TaskStatus.FAILED,TaskStatus.PAUSED}: return self.snapshot()
    def _execute(self,node:TaskNode)->StepResult:
        try:
            if node.action is ActionKind.MODEL_PROMPT:
                model=self.model_router.select(CapabilityRequest(node.required_model_capabilities),provider=node.provider)
                result=self.prompt_port(model,node.node_id,node.prompt or "",self.cancellation)
            else: result=self.skill_port(node.skill_id or "",node.skill_version or "",node.node_id,self.cancellation)
            return result if isinstance(result,StepResult) else StepResult(False,"invalid_port_result",False)
        except Exception as exc:
            code=f"exception:{type(exc).__name__}"; return StepResult(False,code if _SAFE_CODE.fullmatch(code) else "execution_exception",False)
    def _next_runnable(self)->TaskNode|None:
        s=self._require_state()
        for node in self.plan.nodes:
            if s.node_status[node.node_id] is not NodeStatus.PENDING: continue
            deps=[s.node_status[d] for d in node.depends_on]
            if any(v is NodeStatus.FAILED for v in deps): return None
            if all(v is NodeStatus.SUCCEEDED for v in deps): return node
        return None
    def _event(self,kind:str,node_id:str|None=None,code:str="ok")->None:
        s=self._require_state(); kind=kind if _SAFE_CODE.fullmatch(kind) else "invalid_event_kind"; code=code if _SAFE_CODE.fullmatch(code) else "invalid_event_code"
        s.sequence+=1; s.events.append(TaskEvent(s.sequence,kind,node_id,code))
    def _require_state(self)->_TaskState:
        if self._state is None: raise RuntimeError("task runtime has no loaded state")
        return self._state
