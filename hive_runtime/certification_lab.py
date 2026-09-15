"""Hive Provider Certification Lab.

Exact-stack trials separate runner, blind grader and host authorities. Evidence is bound to
its exact StackGenome, repository snapshot, Semantic Twin and SuiteLineage.
"""
from __future__ import annotations
import hashlib, hmac, json, os, threading
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Mapping, Protocol
from .certification_contracts import EvaluationSuite, ExecutionStackDescriptor, StackGenomeAuthority, SuiteLineageAuthority
from .evaluation_runtime import CertificationAuthority, CertificationEvidence, ShadowBenchCase
from .expert_common import BenchmarkDimension, CompetenceLevel, _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha
from .expert_evaluation import BenchmarkResult, CompetenceReport, CompetenceStandard, ExperienceLedger, ExperienceRouter
from .expert_identity import AgentProfile, AgentProfileAuthority, ExpertiseCapsule
from .semantic_twin import SemanticRepositoryTwin

class LabActorRole(str, Enum): RUNNER="runner"; GRADER="grader"

@dataclass(frozen=True)
class LabActor:
    actor_id: str; role: LabActorRole; independence_lineage: str; endpoint_digest: str; authority_tag: str=""
    def fingerprint(self)->str:
        if not _SAFE_ID.fullmatch(self.actor_id) or not _SAFE_TOKEN.fullmatch(self.independence_lineage): raise ValueError("invalid lab actor identity")
        if not _SHA256.fullmatch(self.endpoint_digest): raise ValueError("lab actor endpoint digest must be sha256")
        return _sha({"id":self.actor_id,"role":self.role.value,"lineage":self.independence_lineage,"endpoint":self.endpoint_digest})

class LabIdentityAuthority:
    def __init__(self,key:bytes)->None:
        if not isinstance(key,bytes) or len(key)<32: raise ValueError("lab identity key must contain at least 32 bytes")
        self._key=bytes(key)
    def seal(self,actor:LabActor)->LabActor:
        u=replace(actor,authority_tag=""); return replace(u,authority_tag=hmac.new(self._key,u.fingerprint().encode(),hashlib.sha256).hexdigest())
    def verify(self,actor:LabActor)->bool:
        if not _SHA256.fullmatch(actor.authority_tag): return False
        u=replace(actor,authority_tag="")
        try: fp=u.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(actor.authority_tag,hmac.new(self._key,fp.encode(),hashlib.sha256).hexdigest())

class MonotonicAnchor(Protocol):
    def floor(self)->int: ...
    def advance(self,sequence:int)->None: ...

@dataclass(frozen=True)
class AttestationEntry:
    sequence:int; epoch:int; kind:str; subject_digest:str; previous_digest:str; entry_digest:str

class DurableAttestationJournal:
    VERSION="hive-attestation-journal-v1"; MAX_ENTRIES=1_000_000
    def __init__(self,path:str|os.PathLike[str],key:bytes,anchor:MonotonicAnchor)->None:
        if not isinstance(key,bytes) or len(key)<32: raise ValueError("attestation journal key must contain at least 32 bytes")
        self.path=Path(path); self._key=bytes(key); self.anchor=anchor; self._entries:list[AttestationEntry]=[]; self._lock=threading.RLock(); self._load()
    def _payload(self)->dict[str,object]:
        return {"version":self.VERSION,"entries":[{"sequence":e.sequence,"epoch":e.epoch,"kind":e.kind,"subject":e.subject_digest,"previous":e.previous_digest,"digest":e.entry_digest} for e in self._entries]}
    def _tag(self,payload:Mapping[str,object])->str: return hmac.new(self._key,json.dumps(payload,sort_keys=True,separators=(",",":")).encode(),hashlib.sha256).hexdigest()
    def _load(self)->None:
        floor=self.anchor.floor()
        if not isinstance(floor,int) or floor<0: raise PermissionError("invalid monotonic anchor floor")
        if not self.path.exists():
            if floor>0: raise PermissionError("attestation journal missing below trusted rollback floor")
            return
        try: raw=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,UnicodeError,json.JSONDecodeError) as exc: raise PermissionError("attestation journal unreadable") from exc
        if not isinstance(raw,dict) or raw.get("version")!=self.VERSION: raise PermissionError("invalid attestation journal version")
        payload={"version":raw.get("version"),"entries":raw.get("entries")}; tag=raw.get("tag")
        if not isinstance(tag,str) or not hmac.compare_digest(tag,self._tag(payload)): raise PermissionError("attestation journal HMAC invalid")
        entries=raw.get("entries")
        if not isinstance(entries,list) or len(entries)>self.MAX_ENTRIES: raise PermissionError("attestation journal entries invalid")
        previous="0"*64; parsed=[]; last_epoch=0
        for index,item in enumerate(entries,start=1):
            if not isinstance(item,dict): raise PermissionError("attestation entry invalid")
            seq=item.get("sequence"); epoch=item.get("epoch"); kind=item.get("kind"); subject=item.get("subject"); prev=item.get("previous"); digest=item.get("digest")
            if seq!=index or not isinstance(epoch,int) or epoch<last_epoch: raise PermissionError("attestation sequence/epoch invalid")
            if not isinstance(kind,str) or not _SAFE_TOKEN.fullmatch(kind): raise PermissionError("attestation kind invalid")
            if not isinstance(subject,str) or not _SHA256.fullmatch(subject): raise PermissionError("attestation subject invalid")
            if prev!=previous or not isinstance(digest,str) or not _SHA256.fullmatch(digest): raise PermissionError("attestation chain invalid")
            expected=_sha({"sequence":seq,"epoch":epoch,"kind":kind,"subject":subject,"previous":previous})
            if not hmac.compare_digest(digest,expected): raise PermissionError("attestation entry digest invalid")
            parsed.append(AttestationEntry(seq,epoch,kind,subject,previous,digest)); previous=digest; last_epoch=epoch
        if len(parsed)<floor: raise PermissionError("attestation journal rollback detected")
        self._entries=parsed
    def _persist_locked(self)->None:
        self.path.parent.mkdir(parents=True,exist_ok=True); payload=self._payload(); doc=dict(payload); doc["tag"]=self._tag(payload); temp=self.path.with_name(self.path.name+".tmp")
        temp.write_text(json.dumps(doc,sort_keys=True,separators=(",",":")),encoding="utf-8"); os.replace(temp,self.path); self.anchor.advance(len(self._entries))
    def sequence(self)->int:
        with self._lock: return len(self._entries)
    def epoch(self)->int:
        with self._lock: return self._entries[-1].epoch if self._entries else 0
    def _append_locked(self,*,epoch:int,kind:str,subject_digest:str)->AttestationEntry:
        current=self._entries[-1].epoch if self._entries else 0
        if not isinstance(epoch,int) or epoch<current: raise ValueError("attestation epoch cannot move backwards")
        if not _SAFE_TOKEN.fullmatch(kind) or not _SHA256.fullmatch(subject_digest): raise ValueError("invalid attestation append")
        if len(self._entries)>=self.MAX_ENTRIES: raise RuntimeError("attestation journal entry ceiling exceeded")
        seq=len(self._entries)+1; prev=self._entries[-1].entry_digest if self._entries else "0"*64; digest=_sha({"sequence":seq,"epoch":epoch,"kind":kind,"subject":subject_digest,"previous":prev}); entry=AttestationEntry(seq,epoch,kind,subject_digest,prev,digest); self._entries.append(entry)
        try: self._persist_locked()
        except BaseException: self._entries.pop(); raise
        return entry
    def append(self,*,epoch:int,kind:str,subject_digest:str)->AttestationEntry:
        with self._lock: return self._append_locked(epoch=epoch,kind=kind,subject_digest=subject_digest)
    def reserve_once(self,*,epoch:int,kind:str,subject_digest:str)->AttestationEntry:
        with self._lock:
            if any(e.kind==kind and e.subject_digest==subject_digest for e in self._entries): raise ValueError("attestation subject already reserved")
            return self._append_locked(epoch=epoch,kind=kind,subject_digest=subject_digest)
    def seen(self,*,kind:str,subject_digest:str)->bool:
        with self._lock: return any(e.kind==kind and e.subject_digest==subject_digest for e in self._entries)

class DurableChronoSealClock:
    def __init__(self,journal:DurableAttestationJournal)->None: self.journal=journal
    def now(self)->int: return self.journal.epoch()
    def advance(self,to_epoch:int)->int:
        if not isinstance(to_epoch,int) or to_epoch<self.now(): raise ValueError("ChronoSeal epoch cannot move backwards")
        if to_epoch>self.now(): self.journal.append(epoch=to_epoch,kind="chrono",subject_digest=_sha({"epoch":to_epoch}))
        return self.now()

@dataclass(frozen=True)
class TrialSpec:
    trial_id:str; profile_fingerprint:str; stack_fingerprint:str; provider_id:str; model_id:str; repository_snapshot_digest:str; semantic_twin_fingerprint:str; dimension:BenchmarkDimension; suite_fingerprint:str; case_fingerprint:str; runner_actor_fingerprint:str; grader_actor_fingerprint:str; protocol_version:str="provider-cert-lab-v1"; stack_tag:str=""
    def fingerprint(self)->str:
        if not _SAFE_ID.fullmatch(self.trial_id): raise ValueError("invalid trial id")
        for d in (self.profile_fingerprint,self.stack_fingerprint,self.repository_snapshot_digest,self.semantic_twin_fingerprint,self.suite_fingerprint,self.case_fingerprint,self.runner_actor_fingerprint,self.grader_actor_fingerprint):
            if not _SHA256.fullmatch(d): raise ValueError("trial digest must be sha256")
        for t in (self.provider_id,self.model_id,self.protocol_version):
            if not _SAFE_TOKEN.fullmatch(t): raise ValueError("invalid trial token")
        return _sha({"id":self.trial_id,"profile":self.profile_fingerprint,"stack":self.stack_fingerprint,"provider":self.provider_id,"model":self.model_id,"repository":self.repository_snapshot_digest,"semantic_twin":self.semantic_twin_fingerprint,"dimension":self.dimension.value,"suite":self.suite_fingerprint,"case":self.case_fingerprint,"runner":self.runner_actor_fingerprint,"grader":self.grader_actor_fingerprint,"protocol":self.protocol_version})

class StackSealAuthority:
    def __init__(self,key:bytes,profile_authority:AgentProfileAuthority,identity_authority:LabIdentityAuthority,suite_authority:SuiteLineageAuthority)->None:
        if not isinstance(key,bytes) or len(key)<32: raise ValueError("StackSeal key must contain at least 32 bytes")
        self._key=bytes(key); self.profile_authority=profile_authority; self.identity_authority=identity_authority; self.suite_authority=suite_authority; self.stack_genome=StackGenomeAuthority(profile_authority)
    def seal(self,spec:TrialSpec,profile:AgentProfile,descriptor:ExecutionStackDescriptor,suite:EvaluationSuite,runner:LabActor,grader:LabActor)->TrialSpec:
        if not self.stack_genome.verify_binding(profile,descriptor): raise PermissionError("StackGenome/profile binding invalid")
        if not self.suite_authority.verify(suite): raise PermissionError("SuiteLineage seal invalid")
        if not self.identity_authority.verify(runner) or not self.identity_authority.verify(grader): raise PermissionError("StackSeal actor identity invalid")
        if runner.role is not LabActorRole.RUNNER or grader.role is not LabActorRole.GRADER: raise ValueError("StackSeal actor roles invalid")
        if runner.independence_lineage==grader.independence_lineage or runner.endpoint_digest==grader.endpoint_digest: raise ValueError("runner and grader must be lineage/endpoint independent")
        if spec.profile_fingerprint!=profile.fingerprint() or spec.stack_fingerprint!=descriptor.fingerprint(): raise ValueError("trial does not bind exact sealed profile/StackGenome")
        if spec.provider_id!=descriptor.provider_id or spec.model_id!=descriptor.model_id: raise ValueError("trial provider/model differs from StackGenome")
        if spec.suite_fingerprint!=suite.fingerprint(): raise ValueError("trial suite differs from sealed SuiteLineage")
        if spec.runner_actor_fingerprint!=runner.fingerprint() or spec.grader_actor_fingerprint!=grader.fingerprint(): raise ValueError("trial actor fingerprints mismatch")
        u=replace(spec,stack_tag=""); return replace(u,stack_tag=hmac.new(self._key,u.fingerprint().encode(),hashlib.sha256).hexdigest())
    def verify(self,spec:TrialSpec)->bool:
        if not _SHA256.fullmatch(spec.stack_tag): return False
        u=replace(spec,stack_tag="")
        try: fp=u.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(spec.stack_tag,hmac.new(self._key,fp.encode(),hashlib.sha256).hexdigest())

@dataclass(frozen=True)
class TrialMaterial: trial_fingerprint:str; prompt:str; prompt_digest:str
class TrialForge:
    VERSION="trialforge-v2"
    def __init__(self,case_verifier:Callable[[ShadowBenchCase],bool])->None: self.case_verifier=case_verifier
    def materialize(self,spec:TrialSpec,case:ShadowBenchCase,twin:SemanticRepositoryTwin)->TrialMaterial:
        if not self.case_verifier(case): raise PermissionError("untrusted ShadowBench case")
        if spec.case_fingerprint!=case.semantic_fingerprint(): raise ValueError("trial/case fingerprint mismatch")
        if spec.repository_snapshot_digest!=case.repository_snapshot_digest or spec.repository_snapshot_digest!=twin.repository_snapshot_digest: raise ValueError("trial repository binding mismatch")
        if spec.semantic_twin_fingerprint!=twin.fingerprint(): raise ValueError("trial semantic twin mismatch")
        prompt=f"Hive hidden engineering trial. Dimension={case.dimension.value}; mutation={case.mutation_kind}; repository={case.repository_snapshot_digest}; semantic_twin={twin.fingerprint()}; source_facts={','.join(case.source_fact_ids)}. Analyze the bounded scenario and return evidence-backed conclusions."
        return TrialMaterial(spec.fingerprint(),prompt,_sha({"technology":self.VERSION,"prompt":prompt}))

@dataclass(frozen=True)
class TrialResponse: text:str; tool_incidents:int=0; policy_violations:int=0
class ProviderTrialRunner(Protocol):
    def run(self,material:TrialMaterial,*,provider_id:str,model_id:str)->TrialResponse: ...
@dataclass(frozen=True)
class BlindGradePacket: trial_fingerprint:str; response_text:str; response_digest:str; oracle_digest:str
@dataclass(frozen=True)
class GradeDecision:
    passed:bool; critical_failure:bool=False; policy_violation:bool=False; tamper_event:bool=False; rationale_digest:str=""
    def validate(self)->None:
        if not _SHA256.fullmatch(self.rationale_digest): raise ValueError("GradeProof rationale digest is required")
class IndependentTrialGrader(Protocol):
    def grade(self,packet:BlindGradePacket)->GradeDecision: ...
@dataclass(frozen=True)
class ContaminationAssessment: blocked:bool; codes:tuple[str,...]
class ContaminationRadar:
    def __init__(self,exposed_fingerprints:Iterable[str]=())->None:
        self._exposed=frozenset(exposed_fingerprints)
        if any(not _SHA256.fullmatch(x) for x in self._exposed): raise ValueError("Contamination Radar fingerprints must be sha256")
    def assess(self,case:ShadowBenchCase)->ContaminationAssessment:
        keys={case.semantic_fingerprint(),case.prompt_digest,case.lineage_root}; codes=("known_exposure",) if any(x in self._exposed for x in keys) else tuple(); return ContaminationAssessment(bool(codes),codes)

@dataclass(frozen=True)
class TrialReceipt:
    receipt_id:str; trial_fingerprint:str; profile_fingerprint:str; stack_fingerprint:str; repository_snapshot_digest:str; semantic_twin_fingerprint:str; suite_fingerprint:str; dimension:BenchmarkDimension; response_digest:str; passed:bool; critical_failure:bool; policy_violation:bool; tamper_event:bool; journal_sequence:int; observed_epoch:int; evidence_tag:str=""
    def fingerprint(self)->str:
        if not _SAFE_ID.fullmatch(self.receipt_id): raise ValueError("invalid trial receipt identity")
        for d in (self.trial_fingerprint,self.profile_fingerprint,self.stack_fingerprint,self.repository_snapshot_digest,self.semantic_twin_fingerprint,self.suite_fingerprint,self.response_digest):
            if not _SHA256.fullmatch(d): raise ValueError("trial receipt digest invalid")
        if self.journal_sequence<1 or self.observed_epoch<0: raise ValueError("trial receipt chronology invalid")
        return _sha({"id":self.receipt_id,"trial":self.trial_fingerprint,"profile":self.profile_fingerprint,"stack":self.stack_fingerprint,"repository":self.repository_snapshot_digest,"semantic_twin":self.semantic_twin_fingerprint,"suite":self.suite_fingerprint,"dimension":self.dimension.value,"response":self.response_digest,"passed":self.passed,"critical":self.critical_failure,"policy":self.policy_violation,"tamper":self.tamper_event,"sequence":self.journal_sequence,"epoch":self.observed_epoch})
class TrialEvidenceAuthority:
    def __init__(self,key:bytes)->None:
        if not isinstance(key,bytes) or len(key)<32: raise ValueError("trial evidence key must contain at least 32 bytes")
        self._key=bytes(key)
    def seal(self,r:TrialReceipt)->TrialReceipt:
        u=replace(r,evidence_tag=""); return replace(u,evidence_tag=hmac.new(self._key,u.fingerprint().encode(),hashlib.sha256).hexdigest())
    def verify(self,r:TrialReceipt)->bool:
        if not _SHA256.fullmatch(r.evidence_tag): return False
        u=replace(r,evidence_tag="")
        try: fp=u.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(r.evidence_tag,hmac.new(self._key,fp.encode(),hashlib.sha256).hexdigest())

@dataclass(frozen=True)
class LabBenchmarkEvidence:
    result:BenchmarkResult; stack_fingerprint:str; repository_snapshot_digest:str; semantic_twin_fingerprint:str; suite_fingerprint:str; authority_tag:str=""
    def fingerprint(self)->str:
        self.result.validate()
        for d in (self.stack_fingerprint,self.repository_snapshot_digest,self.semantic_twin_fingerprint,self.suite_fingerprint):
            if not _SHA256.fullmatch(d): raise ValueError("EvidenceDNA digest invalid")
        return _sha({"result":self.result.fingerprint(),"stack":self.stack_fingerprint,"repository":self.repository_snapshot_digest,"semantic_twin":self.semantic_twin_fingerprint,"suite":self.suite_fingerprint})

class BenchmarkAttestationAuthority:
    def __init__(self,key:bytes,receipt_authority:TrialEvidenceAuthority,suite_authority:SuiteLineageAuthority)->None:
        if not isinstance(key,bytes) or len(key)<32: raise ValueError("benchmark attestation key must contain at least 32 bytes")
        self._key=bytes(key); self.receipt_authority=receipt_authority; self.suite_authority=suite_authority
    def issue(self,result_id:str,agent_id:str,profile_fingerprint:str,dimension:BenchmarkDimension,suite:EvaluationSuite,receipts:Iterable[TrialReceipt])->LabBenchmarkEvidence:
        if not self.suite_authority.verify(suite): raise PermissionError("untrusted evaluation suite")
        items=tuple(receipts)
        if not items: raise ValueError("benchmark attestation requires receipts")
        if any(not self.receipt_authority.verify(x) for x in items): raise PermissionError("untrusted trial receipt")
        if len({x.trial_fingerprint for x in items})!=len(items): raise ValueError("duplicate trial receipt")
        first=items[0]; suite_fp=suite.fingerprint()
        if any(x.profile_fingerprint!=profile_fingerprint or x.dimension is not dimension or x.suite_fingerprint!=suite_fp or x.stack_fingerprint!=first.stack_fingerprint or x.repository_snapshot_digest!=first.repository_snapshot_digest or x.semantic_twin_fingerprint!=first.semantic_twin_fingerprint for x in items): raise ValueError("trial receipt EvidenceDNA mismatch")
        sample_set=_sha({"suite":suite_fp,"trials":sorted(x.trial_fingerprint for x in items)})
        result=BenchmarkResult(result_id,agent_id,profile_fingerprint,dimension,suite.diversity_family(),suite.suite_id,suite.suite_version,sample_set,sum(1 for x in items if x.passed),len(items),sum(1 for x in items if x.critical_failure),sum(1 for x in items if x.policy_violation),sum(1 for x in items if x.tamper_event),"0"*64)
        claim=_sha({"result":result.fingerprint(),"stack":first.stack_fingerprint,"repository":first.repository_snapshot_digest,"semantic_twin":first.semantic_twin_fingerprint,"suite":suite_fp})
        # Result evidence is host MAC for CP-0011 compatibility; envelope MAC additionally binds repository/twin/stack.
        result=replace(result,evidence_digest=hmac.new(self._key,claim.encode(),hashlib.sha256).hexdigest())
        u=LabBenchmarkEvidence(result,first.stack_fingerprint,first.repository_snapshot_digest,first.semantic_twin_fingerprint,suite_fp,"")
        return replace(u,authority_tag=hmac.new(self._key,u.fingerprint().encode(),hashlib.sha256).hexdigest())
    def verify(self,e:LabBenchmarkEvidence)->bool:
        if not _SHA256.fullmatch(e.authority_tag): return False
        u=replace(e,authority_tag="")
        try: fp=u.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(e.authority_tag,hmac.new(self._key,fp.encode(),hashlib.sha256).hexdigest())

@dataclass(frozen=True)
class AuditableCertificationReport:
    report_id:str; profile_fingerprint:str; competence_report_fingerprint:str; certification_evidence_fingerprint:str; repository_snapshot_digest:str; semantic_twin_fingerprint:str; benchmark_evidence_fingerprints:tuple[str,...]; observed_epoch:int; report_tag:str=""
    def fingerprint(self)->str:
        if not _SAFE_ID.fullmatch(self.report_id): raise ValueError("invalid certification report id")
        for d in (self.profile_fingerprint,self.competence_report_fingerprint,self.certification_evidence_fingerprint,self.repository_snapshot_digest,self.semantic_twin_fingerprint):
            if not _SHA256.fullmatch(d): raise ValueError("certification report digest invalid")
        if not self.benchmark_evidence_fingerprints or any(not _SHA256.fullmatch(x) for x in self.benchmark_evidence_fingerprints): raise ValueError("certification report requires benchmark evidence fingerprints")
        if self.observed_epoch<0: raise ValueError("certification report epoch invalid")
        return _sha({"id":self.report_id,"profile":self.profile_fingerprint,"competence":self.competence_report_fingerprint,"certification":self.certification_evidence_fingerprint,"repository":self.repository_snapshot_digest,"semantic_twin":self.semantic_twin_fingerprint,"benchmark_evidence":list(self.benchmark_evidence_fingerprints),"epoch":self.observed_epoch})
class CertificationReportAuthority:
    def __init__(self,key:bytes)->None:
        if not isinstance(key,bytes) or len(key)<32: raise ValueError("certification report key must contain at least 32 bytes")
        self._key=bytes(key)
    def seal(self,r:AuditableCertificationReport)->AuditableCertificationReport:
        u=replace(r,report_tag=""); return replace(u,report_tag=hmac.new(self._key,u.fingerprint().encode(),hashlib.sha256).hexdigest())
    def verify(self,r:AuditableCertificationReport)->bool:
        if not _SHA256.fullmatch(r.report_tag): return False
        u=replace(r,report_tag="")
        try: fp=u.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(r.report_tag,hmac.new(self._key,fp.encode(),hashlib.sha256).hexdigest())

class ProviderCertificationLab:
    MAX_RESPONSE_BYTES=4_000_000
    def __init__(self,*,profile_authority:AgentProfileAuthority,stack_authority:StackSealAuthority,identity_authority:LabIdentityAuthority,suite_authority:SuiteLineageAuthority,trial_authority:TrialEvidenceAuthority,benchmark_authority:BenchmarkAttestationAuthority,certification_authority:CertificationAuthority,report_authority:CertificationReportAuthority,journal:DurableAttestationJournal,clock:DurableChronoSealClock,trial_forge:TrialForge,contamination_radar:ContaminationRadar|None=None)->None:
        self.profile_authority=profile_authority; self.stack_authority=stack_authority; self.identity_authority=identity_authority; self.suite_authority=suite_authority; self.trial_authority=trial_authority; self.benchmark_authority=benchmark_authority; self.certification_authority=certification_authority; self.report_authority=report_authority; self.journal=journal; self.clock=clock; self.trial_forge=trial_forge; self.contamination_radar=contamination_radar or ContaminationRadar()
    def run_trial(self,*,spec:TrialSpec,profile:AgentProfile,descriptor:ExecutionStackDescriptor,suite:EvaluationSuite,runner_actor:LabActor,grader_actor:LabActor,case:ShadowBenchCase,twin:SemanticRepositoryTwin,runner:ProviderTrialRunner,grader:IndependentTrialGrader)->TrialReceipt:
        if runner is grader: raise ValueError("runner and grader runtime endpoints must be distinct objects")
        if not self.profile_authority.verify(profile) or not self.stack_authority.verify(spec): raise PermissionError("trial exact-stack authority invalid")
        if not self.stack_authority.stack_genome.verify_binding(profile,descriptor): raise PermissionError("trial StackGenome/profile binding invalid")
        if descriptor.provider_id!=spec.provider_id or descriptor.model_id!=spec.model_id or descriptor.fingerprint()!=spec.stack_fingerprint: raise ValueError("trial descriptor drift")
        if not self.suite_authority.verify(suite) or suite.fingerprint()!=spec.suite_fingerprint: raise PermissionError("trial SuiteLineage invalid")
        if not self.identity_authority.verify(runner_actor) or not self.identity_authority.verify(grader_actor): raise PermissionError("trial actor seal invalid")
        if runner_actor.fingerprint()!=spec.runner_actor_fingerprint or grader_actor.fingerprint()!=spec.grader_actor_fingerprint: raise ValueError("trial actor mismatch")
        if runner_actor.independence_lineage==grader_actor.independence_lineage or runner_actor.endpoint_digest==grader_actor.endpoint_digest: raise ValueError("runner and grader are not lineage/endpoint independent")
        if self.contamination_radar.assess(case).blocked: raise PermissionError("Contamination Radar blocked exposed trial")
        lineage_key=_sha({"profile":profile.fingerprint(),"stack":descriptor.fingerprint(),"lineage":case.lineage_root}); material=self.trial_forge.materialize(spec,case,twin); reservation=self.journal.reserve_once(epoch=self.clock.now(),kind="trial-lineage",subject_digest=lineage_key)
        response=runner.run(material,provider_id=spec.provider_id,model_id=spec.model_id)
        if not isinstance(response,TrialResponse) or not isinstance(response.text,str): raise TypeError("provider runner returned invalid response")
        if response.tool_incidents<0 or response.policy_violations<0: raise ValueError("provider response incident counters invalid")
        if len(response.text.encode("utf-8"))>self.MAX_RESPONSE_BYTES: raise ValueError("provider response exceeds certification bound")
        response_digest=_sha({"text":response.text}); decision=grader.grade(BlindGradePacket(material.trial_fingerprint,response.text,response_digest,case.oracle_digest))
        if not isinstance(decision,GradeDecision): raise TypeError("independent grader returned invalid decision")
        decision.validate(); rid=f"receipt.{_sha({'trial':spec.fingerprint(),'sequence':reservation.sequence})[:28]}"
        receipt=TrialReceipt(rid,spec.fingerprint(),profile.fingerprint(),descriptor.fingerprint(),spec.repository_snapshot_digest,spec.semantic_twin_fingerprint,suite.fingerprint(),spec.dimension,response_digest,decision.passed,decision.critical_failure,decision.policy_violation or response.policy_violations>0,decision.tamper_event or response.tool_incidents>0,reservation.sequence,self.clock.now(),"")
        return self.trial_authority.seal(receipt)
    def evaluate_and_certify(self,*,report_id:str,profile:AgentProfile,capsule:ExpertiseCapsule,standard:CompetenceStandard,benchmark_evidence:Iterable[LabBenchmarkEvidence],descriptor:ExecutionStackDescriptor,repository_snapshot_digest:str,semantic_twin:SemanticRepositoryTwin)->tuple[CompetenceReport,CertificationEvidence,AuditableCertificationReport]:
        if standard.level is not CompetenceLevel.DISTINGUISHED: raise ValueError("production lab certification requires DISTINGUISHED standard")
        if not self.stack_authority.stack_genome.verify_binding(profile,descriptor): raise PermissionError("certification StackGenome/profile binding invalid")
        if repository_snapshot_digest!=semantic_twin.repository_snapshot_digest: raise ValueError("certification repository/Semantic Twin mismatch")
        envelopes=tuple(benchmark_evidence)
        if not envelopes: raise ValueError("certification requires benchmark evidence")
        for e in envelopes:
            if not self.benchmark_authority.verify(e): raise PermissionError("untrusted EvidenceDNA envelope")
            if e.result.profile_fingerprint!=profile.fingerprint() or e.stack_fingerprint!=descriptor.fingerprint() or e.repository_snapshot_digest!=repository_snapshot_digest or e.semantic_twin_fingerprint!=semantic_twin.fingerprint(): raise ValueError("benchmark EvidenceDNA does not match certification context")
        trusted={e.result.fingerprint() for e in envelopes}; ledger=ExperienceLedger(lambda result: result.fingerprint() in trusted)
        for e in envelopes: ledger.add(e.result)
        competence=ExperienceRouter(self.profile_authority,ledger).evaluate(profile,capsule,standard)
        if not competence.passed: raise ValueError("exact stack did not satisfy DISTINGUISHED competence standard")
        evidence_id=f"cert.{_sha({'report':report_id,'profile':profile.fingerprint(),'epoch':self.clock.now()})[:28]}"; certification=self.certification_authority.issue(evidence_id,profile,standard,competence,repository_snapshot_digest=repository_snapshot_digest)
        report=AuditableCertificationReport(report_id,profile.fingerprint(),competence.fingerprint(),certification.fingerprint(),repository_snapshot_digest,semantic_twin.fingerprint(),tuple(sorted(e.fingerprint() for e in envelopes)),self.clock.now(),""); sealed=self.report_authority.seal(report); self.journal.append(epoch=self.clock.now(),kind="certification",subject_digest=sealed.fingerprint()); return competence,certification,sealed
