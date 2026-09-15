"""Hive Provider Certification Lab.

Exact-stack provider trials are separated into runner, blind grader and host authorities.
The lab certifies evidence, never permissions. No provider secret belongs in these records.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
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


class LabActorRole(str, Enum):
    RUNNER = "runner"
    GRADER = "grader"


@dataclass(frozen=True)
class LabActor:
    actor_id: str
    role: LabActorRole
    independence_lineage: str
    authority_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.actor_id) or not _SAFE_TOKEN.fullmatch(self.independence_lineage):
            raise ValueError("invalid lab actor identity")
        return _sha({"id": self.actor_id, "role": self.role.value, "lineage": self.independence_lineage})


class LabIdentityAuthority:
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("lab identity key must contain at least 32 bytes")
        self._key = bytes(key)

    def seal(self, actor: LabActor) -> LabActor:
        unsigned = replace(actor, authority_tag="")
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, authority_tag=tag)

    def verify(self, actor: LabActor) -> bool:
        if not _SHA256.fullmatch(actor.authority_tag):
            return False
        unsigned = replace(actor, authority_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(actor.authority_tag, expected)


class MonotonicAnchor(Protocol):
    """External trusted rollback floor. Production implementation is host/platform specific."""
    def floor(self) -> int: ...
    def advance(self, sequence: int) -> None: ...


@dataclass(frozen=True)
class AttestationEntry:
    sequence: int
    epoch: int
    kind: str
    subject_digest: str
    previous_digest: str
    entry_digest: str


class DurableAttestationJournal:
    VERSION = "hive-attestation-journal-v1"

    def __init__(self, path: str | os.PathLike[str], key: bytes, anchor: MonotonicAnchor) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("attestation journal key must contain at least 32 bytes")
        self.path = Path(path); self._key = bytes(key); self.anchor = anchor; self._entries: list[AttestationEntry] = []
        self._load()

    def _payload(self) -> dict[str, object]:
        return {"version": self.VERSION, "entries": [
            {"sequence": e.sequence, "epoch": e.epoch, "kind": e.kind,
             "subject": e.subject_digest, "previous": e.previous_digest, "digest": e.entry_digest}
            for e in self._entries
        ]}

    def _tag(self, payload: Mapping[str, object]) -> str:
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(self._key, raw, hashlib.sha256).hexdigest()

    def _load(self) -> None:
        floor = self.anchor.floor()
        if not isinstance(floor, int) or floor < 0:
            raise PermissionError("invalid monotonic anchor floor")
        if not self.path.exists():
            if floor > 0:
                raise PermissionError("attestation journal missing below trusted rollback floor")
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise PermissionError("attestation journal unreadable") from exc
        if not isinstance(raw, dict) or raw.get("version") != self.VERSION:
            raise PermissionError("invalid attestation journal version")
        tag = raw.get("tag"); payload = {"version": raw.get("version"), "entries": raw.get("entries")}
        if not isinstance(tag, str) or not hmac.compare_digest(tag, self._tag(payload)):
            raise PermissionError("attestation journal HMAC invalid")
        entries = raw.get("entries")
        if not isinstance(entries, list):
            raise PermissionError("attestation journal entries invalid")
        previous = "0" * 64; parsed: list[AttestationEntry] = []; last_epoch = 0
        for index, item in enumerate(entries, start=1):
            if not isinstance(item, dict): raise PermissionError("attestation entry invalid")
            sequence = item.get("sequence"); epoch = item.get("epoch"); kind = item.get("kind")
            subject = item.get("subject"); prev = item.get("previous"); digest = item.get("digest")
            if sequence != index or not isinstance(epoch, int) or epoch < last_epoch:
                raise PermissionError("attestation sequence/epoch invalid")
            if not isinstance(kind, str) or not _SAFE_TOKEN.fullmatch(kind): raise PermissionError("attestation kind invalid")
            if not isinstance(subject, str) or not _SHA256.fullmatch(subject): raise PermissionError("attestation subject invalid")
            if prev != previous or not isinstance(digest, str) or not _SHA256.fullmatch(digest): raise PermissionError("attestation chain invalid")
            expected = _sha({"sequence": sequence, "epoch": epoch, "kind": kind, "subject": subject, "previous": previous})
            if not hmac.compare_digest(digest, expected): raise PermissionError("attestation entry digest invalid")
            parsed.append(AttestationEntry(sequence, epoch, kind, subject, previous, digest))
            previous = digest; last_epoch = epoch
        if len(parsed) < floor: raise PermissionError("attestation journal rollback detected")
        self._entries = parsed

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self._payload(); document = dict(payload); document["tag"] = self._tag(payload)
        temp = self.path.with_name(self.path.name + ".tmp")
        temp.write_text(json.dumps(document, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        os.replace(temp, self.path)
        self.anchor.advance(len(self._entries))

    def sequence(self) -> int: return len(self._entries)
    def epoch(self) -> int: return self._entries[-1].epoch if self._entries else 0

    def append(self, *, epoch: int, kind: str, subject_digest: str) -> AttestationEntry:
        if not isinstance(epoch, int) or epoch < self.epoch(): raise ValueError("attestation epoch cannot move backwards")
        if not _SAFE_TOKEN.fullmatch(kind) or not _SHA256.fullmatch(subject_digest): raise ValueError("invalid attestation append")
        sequence = len(self._entries) + 1; previous = self._entries[-1].entry_digest if self._entries else "0" * 64
        digest = _sha({"sequence": sequence, "epoch": epoch, "kind": kind, "subject": subject_digest, "previous": previous})
        entry = AttestationEntry(sequence, epoch, kind, subject_digest, previous, digest)
        self._entries.append(entry)
        try: self._persist()
        except BaseException:
            self._entries.pop(); raise
        return entry

    def seen(self, *, kind: str, subject_digest: str) -> bool:
        return any(item.kind == kind and item.subject_digest == subject_digest for item in self._entries)


class DurableChronoSealClock:
    def __init__(self, journal: DurableAttestationJournal) -> None: self.journal = journal
    def now(self) -> int: return self.journal.epoch()
    def advance(self, to_epoch: int) -> int:
        if not isinstance(to_epoch, int) or to_epoch < self.now(): raise ValueError("ChronoSeal epoch cannot move backwards")
        if to_epoch > self.now(): self.journal.append(epoch=to_epoch, kind="chrono", subject_digest=_sha({"epoch": to_epoch}))
        return self.now()


@dataclass(frozen=True)
class TrialSpec:
    trial_id: str
    profile_fingerprint: str
    stack_fingerprint: str
    provider_id: str
    model_id: str
    repository_snapshot_digest: str
    semantic_twin_fingerprint: str
    dimension: BenchmarkDimension
    suite_fingerprint: str
    case_fingerprint: str
    runner_actor_fingerprint: str
    grader_actor_fingerprint: str
    protocol_version: str = "provider-cert-lab-v1"
    stack_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.trial_id): raise ValueError("invalid trial id")
        for digest in (self.profile_fingerprint, self.stack_fingerprint, self.repository_snapshot_digest,
                       self.semantic_twin_fingerprint, self.suite_fingerprint, self.case_fingerprint,
                       self.runner_actor_fingerprint, self.grader_actor_fingerprint):
            if not _SHA256.fullmatch(digest): raise ValueError("trial digest must be sha256")
        for token in (self.provider_id, self.model_id, self.protocol_version):
            if not _SAFE_TOKEN.fullmatch(token): raise ValueError("invalid trial token")
        return _sha({"id": self.trial_id, "profile": self.profile_fingerprint, "stack": self.stack_fingerprint,
                     "provider": self.provider_id, "model": self.model_id, "repository": self.repository_snapshot_digest,
                     "semantic_twin": self.semantic_twin_fingerprint, "dimension": self.dimension.value,
                     "suite": self.suite_fingerprint, "case": self.case_fingerprint,
                     "runner": self.runner_actor_fingerprint, "grader": self.grader_actor_fingerprint,
                     "protocol": self.protocol_version})


class StackSealAuthority:
    def __init__(self, key: bytes, profile_authority: AgentProfileAuthority,
                 identity_authority: LabIdentityAuthority, suite_authority: SuiteLineageAuthority) -> None:
        if not isinstance(key, bytes) or len(key) < 32: raise ValueError("StackSeal key must contain at least 32 bytes")
        self._key = bytes(key); self.profile_authority = profile_authority; self.identity_authority = identity_authority
        self.suite_authority = suite_authority; self.stack_genome = StackGenomeAuthority(profile_authority)

    def seal(self, spec: TrialSpec, profile: AgentProfile, descriptor: ExecutionStackDescriptor,
             suite: EvaluationSuite, runner: LabActor, grader: LabActor) -> TrialSpec:
        if not self.stack_genome.verify_binding(profile, descriptor): raise PermissionError("StackGenome/profile binding invalid")
        if not self.suite_authority.verify(suite): raise PermissionError("SuiteLineage seal invalid")
        if not self.identity_authority.verify(runner) or not self.identity_authority.verify(grader): raise PermissionError("StackSeal actor identity invalid")
        if runner.role is not LabActorRole.RUNNER or grader.role is not LabActorRole.GRADER: raise ValueError("StackSeal actor roles invalid")
        if runner.independence_lineage == grader.independence_lineage: raise ValueError("runner and grader must be independence-separated")
        if spec.profile_fingerprint != profile.fingerprint() or spec.stack_fingerprint != descriptor.fingerprint(): raise ValueError("trial does not bind exact sealed profile/StackGenome")
        if spec.provider_id != descriptor.provider_id or spec.model_id != descriptor.model_id: raise ValueError("trial provider/model differs from StackGenome")
        if spec.suite_fingerprint != suite.fingerprint(): raise ValueError("trial suite differs from sealed SuiteLineage")
        if spec.runner_actor_fingerprint != runner.fingerprint() or spec.grader_actor_fingerprint != grader.fingerprint(): raise ValueError("trial actor fingerprints mismatch")
        unsigned = replace(spec, stack_tag=""); tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, stack_tag=tag)

    def verify(self, spec: TrialSpec) -> bool:
        if not _SHA256.fullmatch(spec.stack_tag): return False
        unsigned = replace(spec, stack_tag="")
        try: fingerprint = unsigned.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(spec.stack_tag, hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest())


@dataclass(frozen=True)
class TrialMaterial:
    trial_fingerprint: str
    prompt: str
    prompt_digest: str


class TrialForge:
    VERSION = "trialforge-v2"
    def __init__(self, case_verifier: Callable[[ShadowBenchCase], bool]) -> None: self.case_verifier = case_verifier
    def materialize(self, spec: TrialSpec, case: ShadowBenchCase, twin: SemanticRepositoryTwin) -> TrialMaterial:
        if not self.case_verifier(case): raise PermissionError("untrusted ShadowBench case")
        if spec.case_fingerprint != case.semantic_fingerprint(): raise ValueError("trial/case fingerprint mismatch")
        if spec.repository_snapshot_digest != case.repository_snapshot_digest or spec.repository_snapshot_digest != twin.repository_snapshot_digest: raise ValueError("trial repository binding mismatch")
        if spec.semantic_twin_fingerprint != twin.fingerprint(): raise ValueError("trial semantic twin mismatch")
        prompt = (f"Hive hidden engineering trial. Dimension={case.dimension.value}; mutation={case.mutation_kind}; "
                  f"repository={case.repository_snapshot_digest}; semantic_twin={twin.fingerprint()}; "
                  f"source_facts={','.join(case.source_fact_ids)}. Analyze the bounded scenario and return evidence-backed conclusions.")
        return TrialMaterial(spec.fingerprint(), prompt, _sha({"technology": self.VERSION, "prompt": prompt}))


@dataclass(frozen=True)
class TrialResponse:
    text: str
    tool_incidents: int = 0
    policy_violations: int = 0


class ProviderTrialRunner(Protocol):
    def run(self, material: TrialMaterial, *, provider_id: str, model_id: str) -> TrialResponse: ...


@dataclass(frozen=True)
class BlindGradePacket:
    trial_fingerprint: str
    response_text: str
    response_digest: str
    oracle_digest: str


@dataclass(frozen=True)
class GradeDecision:
    passed: bool
    critical_failure: bool = False
    policy_violation: bool = False
    tamper_event: bool = False
    rationale_digest: str = ""


class IndependentTrialGrader(Protocol):
    def grade(self, packet: BlindGradePacket) -> GradeDecision: ...


@dataclass(frozen=True)
class ContaminationAssessment:
    blocked: bool
    codes: tuple[str, ...]


class ContaminationRadar:
    def __init__(self, exposed_fingerprints: Iterable[str] = ()) -> None:
        exposed = frozenset(exposed_fingerprints)
        if any(not _SHA256.fullmatch(item) for item in exposed): raise ValueError("Contamination Radar fingerprints must be sha256")
        self._exposed = exposed
    def assess(self, case: ShadowBenchCase) -> ContaminationAssessment:
        keys = {case.semantic_fingerprint(), case.prompt_digest, case.lineage_root}
        codes = ("known_exposure",) if any(item in self._exposed for item in keys) else tuple()
        return ContaminationAssessment(bool(codes), codes)


@dataclass(frozen=True)
class TrialReceipt:
    receipt_id: str
    trial_fingerprint: str
    profile_fingerprint: str
    suite_fingerprint: str
    dimension: BenchmarkDimension
    response_digest: str
    passed: bool
    critical_failure: bool
    policy_violation: bool
    tamper_event: bool
    journal_sequence: int
    observed_epoch: int
    evidence_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.receipt_id): raise ValueError("invalid trial receipt identity")
        for digest in (self.trial_fingerprint, self.profile_fingerprint, self.suite_fingerprint, self.response_digest):
            if not _SHA256.fullmatch(digest): raise ValueError("trial receipt digest invalid")
        if self.journal_sequence < 1 or self.observed_epoch < 0: raise ValueError("trial receipt chronology invalid")
        return _sha({"id": self.receipt_id, "trial": self.trial_fingerprint, "profile": self.profile_fingerprint,
                     "suite": self.suite_fingerprint, "dimension": self.dimension.value, "response": self.response_digest,
                     "passed": self.passed, "critical": self.critical_failure, "policy": self.policy_violation,
                     "tamper": self.tamper_event, "sequence": self.journal_sequence, "epoch": self.observed_epoch})


class TrialEvidenceAuthority:
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32: raise ValueError("trial evidence key must contain at least 32 bytes")
        self._key = bytes(key)
    def seal(self, receipt: TrialReceipt) -> TrialReceipt:
        unsigned = replace(receipt, evidence_tag=""); tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, evidence_tag=tag)
    def verify(self, receipt: TrialReceipt) -> bool:
        if not _SHA256.fullmatch(receipt.evidence_tag): return False
        unsigned = replace(receipt, evidence_tag="")
        try: fingerprint = unsigned.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(receipt.evidence_tag, hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest())


class BenchmarkAttestationAuthority:
    def __init__(self, key: bytes, receipt_authority: TrialEvidenceAuthority,
                 suite_authority: SuiteLineageAuthority) -> None:
        if not isinstance(key, bytes) or len(key) < 32: raise ValueError("benchmark attestation key must contain at least 32 bytes")
        self._key = bytes(key); self.receipt_authority = receipt_authority; self.suite_authority = suite_authority

    @staticmethod
    def _claim_payload(result: BenchmarkResult) -> dict[str, object]:
        return {"result_id": result.result_id, "agent_id": result.agent_id, "profile": result.profile_fingerprint,
                "dimension": result.dimension.value, "suite_family": result.suite_family, "suite": result.suite,
                "suite_version": result.suite_version, "sample_set": result.sample_set_digest,
                "successes": result.successes, "total": result.total, "critical_failures": result.critical_failures,
                "policy_violations": result.policy_violations, "tamper_events": result.tamper_events}

    def issue(self, result_id: str, agent_id: str, profile_fingerprint: str,
              dimension: BenchmarkDimension, suite: EvaluationSuite, receipts: Iterable[TrialReceipt]) -> BenchmarkResult:
        if not self.suite_authority.verify(suite): raise PermissionError("untrusted evaluation suite")
        items = tuple(receipts)
        if not items: raise ValueError("benchmark attestation requires receipts")
        if any(not self.receipt_authority.verify(item) for item in items): raise PermissionError("untrusted trial receipt")
        if len({item.trial_fingerprint for item in items}) != len(items): raise ValueError("duplicate trial receipt")
        suite_fp = suite.fingerprint()
        if any(item.profile_fingerprint != profile_fingerprint or item.dimension is not dimension or item.suite_fingerprint != suite_fp for item in items): raise ValueError("trial receipt aggregate mismatch")
        sample_set = _sha({"suite": suite_fp, "trials": sorted(item.trial_fingerprint for item in items)})
        unsigned = BenchmarkResult(result_id, agent_id, profile_fingerprint, dimension, suite.diversity_family(),
                                   suite.suite_id, suite.suite_version, sample_set,
                                   sum(1 for item in items if item.passed), len(items),
                                   sum(1 for item in items if item.critical_failure),
                                   sum(1 for item in items if item.policy_violation),
                                   sum(1 for item in items if item.tamper_event), "0" * 64)
        evidence = hmac.new(self._key, _sha(self._claim_payload(unsigned)).encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, evidence_digest=evidence)

    def verify(self, result: BenchmarkResult) -> bool:
        try: result.validate()
        except ValueError: return False
        expected = hmac.new(self._key, _sha(self._claim_payload(result)).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(result.evidence_digest, expected)


@dataclass(frozen=True)
class AuditableCertificationReport:
    report_id: str
    profile_fingerprint: str
    competence_report_fingerprint: str
    certification_evidence_fingerprint: str
    repository_snapshot_digest: str
    semantic_twin_fingerprint: str
    benchmark_result_fingerprints: tuple[str, ...]
    observed_epoch: int
    report_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.report_id): raise ValueError("invalid certification report id")
        for digest in (self.profile_fingerprint, self.competence_report_fingerprint,
                       self.certification_evidence_fingerprint, self.repository_snapshot_digest,
                       self.semantic_twin_fingerprint):
            if not _SHA256.fullmatch(digest): raise ValueError("certification report digest invalid")
        if not self.benchmark_result_fingerprints or any(not _SHA256.fullmatch(item) for item in self.benchmark_result_fingerprints): raise ValueError("certification report requires benchmark fingerprints")
        if self.observed_epoch < 0: raise ValueError("certification report epoch invalid")
        return _sha({"id": self.report_id, "profile": self.profile_fingerprint,
                     "competence": self.competence_report_fingerprint, "certification": self.certification_evidence_fingerprint,
                     "repository": self.repository_snapshot_digest, "semantic_twin": self.semantic_twin_fingerprint,
                     "benchmarks": list(self.benchmark_result_fingerprints), "epoch": self.observed_epoch})


class CertificationReportAuthority:
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32: raise ValueError("certification report key must contain at least 32 bytes")
        self._key = bytes(key)
    def seal(self, report: AuditableCertificationReport) -> AuditableCertificationReport:
        unsigned = replace(report, report_tag=""); tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, report_tag=tag)
    def verify(self, report: AuditableCertificationReport) -> bool:
        if not _SHA256.fullmatch(report.report_tag): return False
        unsigned = replace(report, report_tag="")
        try: fingerprint = unsigned.fingerprint()
        except ValueError: return False
        return hmac.compare_digest(report.report_tag, hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest())


class ProviderCertificationLab:
    def __init__(self, *, profile_authority: AgentProfileAuthority, stack_authority: StackSealAuthority,
                 identity_authority: LabIdentityAuthority, suite_authority: SuiteLineageAuthority,
                 trial_authority: TrialEvidenceAuthority, benchmark_authority: BenchmarkAttestationAuthority,
                 certification_authority: CertificationAuthority, report_authority: CertificationReportAuthority,
                 journal: DurableAttestationJournal, clock: DurableChronoSealClock,
                 trial_forge: TrialForge, contamination_radar: ContaminationRadar | None = None) -> None:
        self.profile_authority = profile_authority; self.stack_authority = stack_authority
        self.identity_authority = identity_authority; self.suite_authority = suite_authority
        self.trial_authority = trial_authority; self.benchmark_authority = benchmark_authority
        self.certification_authority = certification_authority; self.report_authority = report_authority
        self.journal = journal; self.clock = clock; self.trial_forge = trial_forge
        self.contamination_radar = contamination_radar or ContaminationRadar()

    def run_trial(self, *, spec: TrialSpec, profile: AgentProfile, descriptor: ExecutionStackDescriptor,
                  suite: EvaluationSuite, runner_actor: LabActor, grader_actor: LabActor,
                  case: ShadowBenchCase, twin: SemanticRepositoryTwin,
                  runner: ProviderTrialRunner, grader: IndependentTrialGrader) -> TrialReceipt:
        if runner is grader: raise ValueError("runner and grader runtime endpoints must be distinct objects")
        if not self.profile_authority.verify(profile) or not self.stack_authority.verify(spec): raise PermissionError("trial exact-stack authority invalid")
        if not self.stack_authority.stack_genome.verify_binding(profile, descriptor): raise PermissionError("trial StackGenome/profile binding invalid")
        if descriptor.provider_id != spec.provider_id or descriptor.model_id != spec.model_id or descriptor.fingerprint() != spec.stack_fingerprint: raise ValueError("trial descriptor drift")
        if not self.suite_authority.verify(suite) or suite.fingerprint() != spec.suite_fingerprint: raise PermissionError("trial SuiteLineage invalid")
        if not self.identity_authority.verify(runner_actor) or not self.identity_authority.verify(grader_actor): raise PermissionError("trial actor seal invalid")
        if runner_actor.fingerprint() != spec.runner_actor_fingerprint or grader_actor.fingerprint() != spec.grader_actor_fingerprint: raise ValueError("trial actor mismatch")
        if runner_actor.independence_lineage == grader_actor.independence_lineage: raise ValueError("runner and grader are not independent")
        if self.contamination_radar.assess(case).blocked: raise PermissionError("Contamination Radar blocked exposed trial")
        lineage_key = _sha({"profile": profile.fingerprint(), "stack": descriptor.fingerprint(), "lineage": case.lineage_root})
        if self.journal.seen(kind="trial-lineage", subject_digest=lineage_key): raise ValueError("trial lineage replay rejected")
        material = self.trial_forge.materialize(spec, case, twin)
        # One-Shot Trial Law: consume lineage before provider execution so repeated attempts cannot fish for a favorable answer.
        lineage_entry = self.journal.append(epoch=self.clock.now(), kind="trial-lineage", subject_digest=lineage_key)
        response = runner.run(material, provider_id=spec.provider_id, model_id=spec.model_id)
        if not isinstance(response, TrialResponse) or not isinstance(response.text, str): raise TypeError("provider runner returned invalid response")
        if response.tool_incidents < 0 or response.policy_violations < 0: raise ValueError("provider response incident counters invalid")
        response_digest = _sha({"text": response.text})
        packet = BlindGradePacket(material.trial_fingerprint, response.text, response_digest, case.oracle_digest)
        decision = grader.grade(packet)
        if not isinstance(decision, GradeDecision): raise TypeError("independent grader returned invalid decision")
        if decision.rationale_digest and not _SHA256.fullmatch(decision.rationale_digest): raise ValueError("grader rationale digest invalid")
        receipt_id = f"receipt.{_sha({'trial': spec.fingerprint(), 'sequence': lineage_entry.sequence})[:28]}"
        receipt = TrialReceipt(receipt_id, spec.fingerprint(), profile.fingerprint(), suite.fingerprint(), spec.dimension,
                               response_digest, decision.passed, decision.critical_failure,
                               decision.policy_violation or response.policy_violations > 0,
                               decision.tamper_event or response.tool_incidents > 0,
                               lineage_entry.sequence, self.clock.now(), "")
        return self.trial_authority.seal(receipt)

    def evaluate_and_certify(self, *, report_id: str, profile: AgentProfile, capsule: ExpertiseCapsule,
                             standard: CompetenceStandard, benchmark_results: Iterable[BenchmarkResult],
                             repository_snapshot_digest: str, semantic_twin: SemanticRepositoryTwin) -> tuple[CompetenceReport, CertificationEvidence, AuditableCertificationReport]:
        if standard.level is not CompetenceLevel.DISTINGUISHED: raise ValueError("production lab certification requires DISTINGUISHED standard")
        if repository_snapshot_digest != semantic_twin.repository_snapshot_digest: raise ValueError("certification repository/Semantic Twin mismatch")
        ledger = ExperienceLedger(self.benchmark_authority.verify); results = tuple(benchmark_results)
        if not results: raise ValueError("certification requires benchmark results")
        for result in results: ledger.add(result)
        competence = ExperienceRouter(self.profile_authority, ledger).evaluate(profile, capsule, standard)
        if not competence.passed: raise ValueError("exact stack did not satisfy DISTINGUISHED competence standard")
        evidence_id = f"cert.{_sha({'report': report_id, 'profile': profile.fingerprint(), 'epoch': self.clock.now()})[:28]}"
        certification = self.certification_authority.issue(evidence_id, profile, standard, competence,
                                                            repository_snapshot_digest=repository_snapshot_digest)
        report = AuditableCertificationReport(report_id, profile.fingerprint(), competence.fingerprint(),
                                               certification.fingerprint(), repository_snapshot_digest,
                                               semantic_twin.fingerprint(),
                                               tuple(sorted(result.fingerprint() for result in results)), self.clock.now(), "")
        sealed = self.report_authority.seal(report)
        self.journal.append(epoch=self.clock.now(), kind="certification", subject_digest=sealed.fingerprint())
        return competence, certification, sealed
