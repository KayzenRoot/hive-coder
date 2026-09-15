"""Fresh evaluation, novelty, recertification and outcome-feedback primitives.

ShadowBench cases are host-generated proposals, not trusted benchmark results. Outcome Echo
is advisory-only and may force re-certification but can never promote competence.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Mapping

from .expert_common import BenchmarkDimension, CompetenceLevel, _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha
from .expert_context import CodeTruthMap
from .expert_evaluation import CompetenceReport, CompetenceStandard
from .expert_identity import AgentProfile, AgentProfileAuthority
from .repository_intelligence import GenomePulseResult, RepositorySnapshot


class RecertificationStatus(str, Enum):
    CURRENT = "current"
    DUE = "due"
    EXPIRED = "expired"


class ChronoSealClock:
    """Trusted-host logical epoch that can only move forward inside a runtime instance."""

    def __init__(self, start_epoch: int = 0) -> None:
        if not isinstance(start_epoch, int) or start_epoch < 0:
            raise ValueError("invalid ChronoSeal start epoch")
        self._epoch = start_epoch

    def now(self) -> int:
        return self._epoch

    def advance(self, to_epoch: int) -> int:
        if not isinstance(to_epoch, int) or to_epoch < self._epoch:
            raise ValueError("ChronoSeal epoch cannot move backwards")
        self._epoch = to_epoch
        return self._epoch


@dataclass(frozen=True)
class ShadowBenchCase:
    case_id: str
    lineage_id: str
    lineage_root: str
    factory_version: str
    epoch_label: str
    repository_snapshot_digest: str
    dimension: BenchmarkDimension
    mutation_kind: str
    source_fact_ids: tuple[str, ...]
    prompt_digest: str
    oracle_digest: str
    hidden_nonce_digest: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.case_id) or not _SAFE_ID.fullmatch(self.lineage_id):
            raise ValueError("invalid ShadowBench case identity")
        if not _SAFE_TOKEN.fullmatch(self.factory_version) or not _SAFE_TOKEN.fullmatch(self.epoch_label):
            raise ValueError("invalid ShadowBench version/epoch")
        if not _SHA256.fullmatch(self.lineage_root) or not _SHA256.fullmatch(self.repository_snapshot_digest):
            raise ValueError("invalid ShadowBench lineage/snapshot digest")
        if not _SAFE_TOKEN.fullmatch(self.mutation_kind):
            raise ValueError("invalid ShadowBench mutation kind")
        if not self.source_fact_ids or any(not _SAFE_ID.fullmatch(item) for item in self.source_fact_ids):
            raise ValueError("ShadowBench case requires source facts")
        if len(self.source_fact_ids) != len(set(self.source_fact_ids)):
            raise ValueError("duplicate ShadowBench source fact")
        for digest in (self.prompt_digest, self.oracle_digest, self.hidden_nonce_digest):
            if not _SHA256.fullmatch(digest):
                raise ValueError("ShadowBench digests must be sha256")

    def semantic_fingerprint(self) -> str:
        self.validate()
        return _sha({
            "factory": self.factory_version,
            "snapshot": self.repository_snapshot_digest,
            "dimension": self.dimension.value,
            "mutation": self.mutation_kind,
            "facts": list(self.source_fact_ids),
            "prompt": self.prompt_digest,
        })


class ShadowBenchFactory:
    """Host-keyed hidden evaluation-case factory with no model-visible oracle material."""

    VERSION = "shadowbench-v1"
    _MUTATIONS: Mapping[BenchmarkDimension, tuple[str, ...]] = {
        BenchmarkDimension.REPOSITORY_REASONING: ("dependency-impact", "ownership-boundary", "change-radius"),
        BenchmarkDimension.DEBUGGING: ("fault-localization", "regression-cause", "state-divergence"),
        BenchmarkDimension.ARCHITECTURE: ("invariant-break", "boundary-erosion", "migration-choice"),
        BenchmarkDimension.TESTING: ("missing-negative-path", "oracle-gap", "flaky-assumption"),
        BenchmarkDimension.SECURITY: ("trust-boundary", "authority-confusion", "injection-path"),
        BenchmarkDimension.PERFORMANCE: ("hot-path", "complexity-regression", "contention-risk"),
        BenchmarkDimension.MAINTAINABILITY: ("coupling-growth", "duplication-risk", "contract-drift"),
        BenchmarkDimension.CODE_REVIEW: ("semantic-regression", "scope-creep", "evidence-gap"),
        BenchmarkDimension.LONG_HORIZON: ("staged-migration", "rollback-plan", "multi-step-repair"),
        BenchmarkDimension.TOOL_RELIABILITY: ("tool-failure", "partial-result", "stale-observation"),
        BenchmarkDimension.TAMPER_RESISTANCE: ("forged-evidence", "prompt-injection", "identity-spoof"),
    }

    def __init__(self, host_key: bytes) -> None:
        if not isinstance(host_key, bytes) or len(host_key) < 32:
            raise ValueError("ShadowBench host key must contain at least 32 bytes")
        self._key = bytes(host_key)

    def _hmac(self, text: str) -> str:
        return hmac.new(self._key, text.encode(), hashlib.sha256).hexdigest()

    def generate(self, snapshot: RepositorySnapshot, truth: CodeTruthMap,
                 dimension: BenchmarkDimension, *, epoch_label: str, count: int = 1) -> tuple[ShadowBenchCase, ...]:
        snapshot.validate()
        if not _SAFE_TOKEN.fullmatch(epoch_label):
            raise ValueError("invalid ShadowBench epoch label")
        if not 1 <= count <= 100:
            raise ValueError("invalid ShadowBench case count")
        facts = truth.query((), verified_only=True)
        if not facts:
            raise ValueError("ShadowBench requires verified repository facts")
        if count > len(facts):
            raise ValueError("ShadowBench count exceeds available independent source facts")
        snapshot_digest = snapshot.fingerprint()
        ranked = sorted(
            facts,
            key=lambda fact: self._hmac(
                f"rank|{self.VERSION}|{epoch_label}|{snapshot_digest}|{dimension.value}|{fact.fingerprint()}"
            ),
        )
        mutation_options = self._MUTATIONS[dimension]
        cases: list[ShadowBenchCase] = []
        for fact in ranked[:count]:
            mutation_selector = int(self._hmac(
                f"mutation|{epoch_label}|{snapshot_digest}|{dimension.value}|{fact.fact_id}"
            )[:8], 16)
            mutation = mutation_options[mutation_selector % len(mutation_options)]
            lineage_root = _sha({
                "factory": self.VERSION,
                "snapshot": snapshot_digest,
                "dimension": dimension.value,
                "source_fact": fact.fact_id,
            })
            lineage_id = f"sb.{lineage_root[:28]}"
            nonce = self._hmac(f"nonce|{epoch_label}|{lineage_root}")
            prompt_digest = _sha({
                "technology": self.VERSION,
                "snapshot": snapshot_digest,
                "dimension": dimension.value,
                "mutation": mutation,
                "source_fact": fact.fact_id,
                "source_fingerprint": fact.fingerprint(),
            })
            oracle_digest = self._hmac(
                f"oracle|{self.VERSION}|{epoch_label}|{snapshot_digest}|{dimension.value}|{mutation}|{fact.fingerprint()}|{nonce}"
            )
            case_digest = self._hmac(f"case|{epoch_label}|{lineage_root}|{mutation}|{prompt_digest}|{oracle_digest}|{nonce}")
            case = ShadowBenchCase(
                case_id=f"shadow.{case_digest[:28]}", lineage_id=lineage_id,
                lineage_root=lineage_root, factory_version=self.VERSION, epoch_label=epoch_label,
                repository_snapshot_digest=snapshot_digest, dimension=dimension,
                mutation_kind=mutation, source_fact_ids=(fact.fact_id,), prompt_digest=prompt_digest,
                oracle_digest=oracle_digest, hidden_nonce_digest=nonce,
            )
            case.validate()
            cases.append(case)
        return tuple(cases)

    def verify_case(self, case: ShadowBenchCase, truth: CodeTruthMap) -> bool:
        try:
            case.validate()
        except ValueError:
            return False
        if case.factory_version != self.VERSION or len(case.source_fact_ids) != 1:
            return False
        fact_id = case.source_fact_ids[0]
        try:
            fact = next(item for item in truth.query((), verified_only=True) if item.fact_id == fact_id)
        except StopIteration:
            return False
        expected_root = _sha({
            "factory": self.VERSION, "snapshot": case.repository_snapshot_digest,
            "dimension": case.dimension.value, "source_fact": fact.fact_id,
        })
        if not hmac.compare_digest(case.lineage_root, expected_root):
            return False
        if case.lineage_id != f"sb.{expected_root[:28]}":
            return False
        expected_nonce = self._hmac(f"nonce|{case.epoch_label}|{expected_root}")
        if not hmac.compare_digest(case.hidden_nonce_digest, expected_nonce):
            return False
        expected_prompt = _sha({
            "technology": self.VERSION, "snapshot": case.repository_snapshot_digest,
            "dimension": case.dimension.value, "mutation": case.mutation_kind,
            "source_fact": fact.fact_id, "source_fingerprint": fact.fingerprint(),
        })
        if not hmac.compare_digest(case.prompt_digest, expected_prompt):
            return False
        expected_oracle = self._hmac(
            f"oracle|{self.VERSION}|{case.epoch_label}|{case.repository_snapshot_digest}|{case.dimension.value}|{case.mutation_kind}|{fact.fingerprint()}|{expected_nonce}"
        )
        if not hmac.compare_digest(case.oracle_digest, expected_oracle):
            return False
        expected_case = self._hmac(
            f"case|{case.epoch_label}|{expected_root}|{case.mutation_kind}|{expected_prompt}|{expected_oracle}|{expected_nonce}"
        )
        return case.case_id == f"shadow.{expected_case[:28]}"


class BenchmarkNoveltyLedger:
    """Rejects ID churn, replay and trivial variants over the same source lineage."""

    def __init__(self) -> None:
        self._case_ids: set[str] = set()
        self._semantic: set[str] = set()
        self._lineage_roots: set[str] = set()

    def add(self, case: ShadowBenchCase) -> None:
        case.validate()
        semantic = case.semantic_fingerprint()
        if case.case_id in self._case_ids:
            raise ValueError("duplicate ShadowBench case id")
        if semantic in self._semantic:
            raise ValueError("ShadowBench semantic replay rejected")
        if case.lineage_root in self._lineage_roots:
            raise ValueError("ShadowBench trivial lineage mutation rejected")
        self._case_ids.add(case.case_id)
        self._semantic.add(semantic)
        self._lineage_roots.add(case.lineage_root)

    def __len__(self) -> int:
        return len(self._case_ids)


@dataclass(frozen=True)
class CounterfactualProbe:
    probe_id: str
    repository_snapshot_digest: str
    changed_fact_id: str
    replacement_object_digest: str
    expected_drift_invariants: tuple[str, ...]
    probe_digest: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.probe_id) or not _SAFE_ID.fullmatch(self.changed_fact_id):
            raise ValueError("invalid counterfactual probe identity")
        if not self.expected_drift_invariants or any(not _SAFE_ID.fullmatch(item) for item in self.expected_drift_invariants):
            raise ValueError("counterfactual probe requires expected invariants")
        for digest in (self.repository_snapshot_digest, self.replacement_object_digest, self.probe_digest):
            if not _SHA256.fullmatch(digest):
                raise ValueError("counterfactual probe digests must be sha256")


class CounterfactualForge:
    """Creates structural what-if probes without mutating repository source."""

    VERSION = "counterfactual-forge-v1"

    def create(self, pulse: GenomePulseResult, *, repository_snapshot_digest: str,
               fact_id: str, replacement_object_digest: str) -> CounterfactualProbe:
        if not _SHA256.fullmatch(repository_snapshot_digest) or not _SHA256.fullmatch(replacement_object_digest):
            raise ValueError("invalid counterfactual digest")
        invariants = pulse.fact_to_invariants.get(fact_id)
        if not invariants:
            raise ValueError("counterfactual fact is not bound to a mined invariant")
        payload = {
            "technology": self.VERSION, "snapshot": repository_snapshot_digest,
            "fact": fact_id, "replacement": replacement_object_digest,
            "expected_drift": list(invariants),
        }
        digest = _sha(payload)
        probe = CounterfactualProbe(
            f"cf.{digest[:28]}", repository_snapshot_digest, fact_id,
            replacement_object_digest, tuple(invariants), digest,
        )
        probe.validate()
        return probe


@dataclass(frozen=True)
class CertificationEvidence:
    evidence_id: str
    profile_fingerprint: str
    standard_fingerprint: str
    competence_report_fingerprint: str
    repository_snapshot_digest: str
    observed_epoch: int
    benchmark_families: tuple[str, ...]
    passed: bool
    authority_tag: str = ""

    def validate_unsigned(self) -> None:
        if not _SAFE_ID.fullmatch(self.evidence_id):
            raise ValueError("invalid certification evidence id")
        for digest in (
            self.profile_fingerprint, self.standard_fingerprint,
            self.competence_report_fingerprint, self.repository_snapshot_digest,
        ):
            if not _SHA256.fullmatch(digest):
                raise ValueError("certification evidence digests must be sha256")
        if self.observed_epoch < 0:
            raise ValueError("invalid certification epoch")
        if not self.benchmark_families or any(not _SAFE_TOKEN.fullmatch(item) for item in self.benchmark_families):
            raise ValueError("certification evidence requires benchmark families")
        if len(self.benchmark_families) != len(set(self.benchmark_families)):
            raise ValueError("duplicate certification benchmark family")

    def fingerprint(self) -> str:
        self.validate_unsigned()
        return _sha({
            "id": self.evidence_id, "profile": self.profile_fingerprint,
            "standard": self.standard_fingerprint, "report": self.competence_report_fingerprint,
            "snapshot": self.repository_snapshot_digest, "epoch": self.observed_epoch,
            "families": list(self.benchmark_families), "passed": self.passed,
        })


class CertificationAuthority:
    """Trusted-host seal for recertification evidence. Callers cannot self-issue freshness."""

    def __init__(self, key: bytes, clock: ChronoSealClock,
                 profile_authority: AgentProfileAuthority) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("certification authority key must contain at least 32 bytes")
        self._key = bytes(key)
        self.clock = clock
        self.profile_authority = profile_authority

    def issue(self, evidence_id: str, profile: AgentProfile, standard: CompetenceStandard,
              report: CompetenceReport, *, repository_snapshot_digest: str) -> CertificationEvidence:
        if not self.profile_authority.verify(profile):
            raise PermissionError("certification profile seal invalid")
        standard.validate()
        if standard.level is not CompetenceLevel.DISTINGUISHED or report.level is not CompetenceLevel.DISTINGUISHED:
            raise ValueError("production certification requires DISTINGUISHED level")
        if not report.passed:
            raise ValueError("failed competence report cannot become certification evidence")
        if report.profile_fingerprint != profile.fingerprint() or report.standard_fingerprint != standard.fingerprint():
            raise ValueError("competence report does not match certification subject")
        if not _SHA256.fullmatch(repository_snapshot_digest):
            raise ValueError("invalid certification repository snapshot")
        families = tuple(sorted({family for score in report.scores for family in score.suite_families}))
        if len(families) < standard.min_independent_suites:
            raise ValueError("competence report lacks required benchmark-family diversity")
        unsigned = CertificationEvidence(
            evidence_id, profile.fingerprint(), standard.fingerprint(), report.fingerprint(),
            repository_snapshot_digest, self.clock.now(), families, True, "",
        )
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, authority_tag=tag)

    def verify(self, evidence: CertificationEvidence) -> bool:
        if not _SHA256.fullmatch(evidence.authority_tag):
            return False
        unsigned = replace(evidence, authority_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(evidence.authority_tag, expected)


@dataclass(frozen=True)
class CompetenceHalfLifePolicy:
    warning_age_epochs: int = 30
    max_age_epochs: int = 90
    min_recent_reports: int = 1
    min_independent_families: int = 2
    require_snapshot_match: bool = True
    force_due_on_regression: bool = True

    def validate(self) -> None:
        if not 1 <= self.warning_age_epochs < self.max_age_epochs <= 100_000:
            raise ValueError("invalid competence half-life ages")
        if not 1 <= self.min_recent_reports <= 100:
            raise ValueError("invalid recent certification report floor")
        if not 1 <= self.min_independent_families <= 20:
            raise ValueError("invalid certification family floor")


@dataclass(frozen=True)
class OutcomeSignal:
    profile_fingerprint: str
    samples: int
    successes: int
    regressions: int
    rollbacks: int
    quality_score: float
    advisory_only: bool = True


@dataclass(frozen=True)
class RecertificationReport:
    profile_fingerprint: str
    standard_fingerprint: str
    repository_snapshot_digest: str
    status: RecertificationStatus
    newest_evidence_age: int | None
    recent_reports: int
    independent_families: tuple[str, ...]
    blocking_codes: tuple[str, ...]


class RecertificationClock:
    """Competence can age out or be forced due; this class never promotes a rank."""

    def __init__(self, certification_authority: CertificationAuthority,
                 policy: CompetenceHalfLifePolicy = CompetenceHalfLifePolicy()) -> None:
        policy.validate()
        self.certification_authority = certification_authority
        self.profile_authority = certification_authority.profile_authority
        self.clock = certification_authority.clock
        self.policy = policy

    def assess(self, profile: AgentProfile, standard: CompetenceStandard,
               *, repository_snapshot_digest: str,
               evidence: Iterable[CertificationEvidence], outcome: OutcomeSignal | None = None) -> RecertificationReport:
        if not self.profile_authority.verify(profile):
            raise PermissionError("recertification profile seal invalid")
        standard.validate()
        if standard.level is not CompetenceLevel.DISTINGUISHED:
            raise ValueError("production recertification requires DISTINGUISHED standard")
        if not _SHA256.fullmatch(repository_snapshot_digest):
            raise ValueError("invalid recertification snapshot")
        current_epoch = self.clock.now()
        profile_fp = profile.fingerprint()
        standard_fp = standard.fingerprint()
        relevant: list[CertificationEvidence] = []
        saw_matching_profile_standard = False
        saw_snapshot_mismatch = False
        for item in evidence:
            if not self.certification_authority.verify(item):
                raise PermissionError("untrusted certification evidence")
            if item.observed_epoch > current_epoch:
                raise ValueError("certification evidence comes from the future")
            if item.profile_fingerprint != profile_fp or item.standard_fingerprint != standard_fp:
                continue
            saw_matching_profile_standard = True
            if self.policy.require_snapshot_match and item.repository_snapshot_digest != repository_snapshot_digest:
                saw_snapshot_mismatch = True
                continue
            if item.passed:
                relevant.append(item)

        if not relevant:
            codes = ["no_current_certification_evidence"]
            if saw_matching_profile_standard and saw_snapshot_mismatch:
                codes.append("repository_snapshot_changed")
            return RecertificationReport(
                profile_fp, standard_fp, repository_snapshot_digest,
                RecertificationStatus.EXPIRED, None, 0, tuple(), tuple(codes),
            )

        newest_age = min(current_epoch - item.observed_epoch for item in relevant)
        recent = [item for item in relevant if current_epoch - item.observed_epoch <= self.policy.max_age_epochs]
        families = tuple(sorted({family for item in recent for family in item.benchmark_families}))
        blocking: list[str] = []
        if newest_age > self.policy.max_age_epochs:
            blocking.append("competence_evidence_expired")
        if len(recent) < self.policy.min_recent_reports:
            blocking.append("insufficient_recent_certification_reports")
        if len(families) < self.policy.min_independent_families:
            blocking.append("insufficient_recent_benchmark_families")
        if blocking:
            status = RecertificationStatus.EXPIRED
        else:
            due_codes: list[str] = []
            if newest_age > self.policy.warning_age_epochs:
                due_codes.append("competence_half_life_warning")
            if outcome is not None:
                if outcome.profile_fingerprint != profile_fp or not outcome.advisory_only:
                    raise ValueError("invalid Outcome Echo signal for recertification")
                if self.policy.force_due_on_regression and (outcome.regressions or outcome.rollbacks):
                    due_codes.append("negative_outcome_feedback")
            if due_codes:
                status = RecertificationStatus.DUE
                blocking.extend(due_codes)
            else:
                status = RecertificationStatus.CURRENT
        return RecertificationReport(
            profile_fp, standard_fp, repository_snapshot_digest,
            status, newest_age, len(recent), families, tuple(blocking),
        )


@dataclass(frozen=True)
class OutcomeRecord:
    outcome_id: str
    profile_fingerprint: str
    master_plan_fingerprint: str
    repository_snapshot_digest: str
    observed_epoch: int
    success: bool
    regressions: int
    rollbacks: int
    evidence_digest: str
    authority_tag: str = ""

    def validate_unsigned(self) -> None:
        if not _SAFE_ID.fullmatch(self.outcome_id):
            raise ValueError("invalid outcome identity")
        for digest in (
            self.profile_fingerprint, self.master_plan_fingerprint,
            self.repository_snapshot_digest, self.evidence_digest,
        ):
            if not _SHA256.fullmatch(digest):
                raise ValueError("outcome digests must be sha256")
        if self.observed_epoch < 0 or self.regressions < 0 or self.rollbacks < 0:
            raise ValueError("invalid outcome counters")

    def fingerprint(self) -> str:
        self.validate_unsigned()
        return _sha({
            "id": self.outcome_id, "profile": self.profile_fingerprint,
            "plan": self.master_plan_fingerprint, "snapshot": self.repository_snapshot_digest,
            "epoch": self.observed_epoch, "success": self.success,
            "regressions": self.regressions, "rollbacks": self.rollbacks,
            "evidence": self.evidence_digest,
        })


class OutcomeAuthority:
    """Trusted-host outcome seal using the same monotonic ChronoSeal epoch."""

    def __init__(self, key: bytes, clock: ChronoSealClock) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("outcome authority key must contain at least 32 bytes")
        self._key = bytes(key)
        self.clock = clock

    def issue(self, outcome_id: str, *, profile_fingerprint: str,
              master_plan_fingerprint: str, repository_snapshot_digest: str,
              success: bool, regressions: int, rollbacks: int,
              evidence_digest: str) -> OutcomeRecord:
        unsigned = OutcomeRecord(
            outcome_id, profile_fingerprint, master_plan_fingerprint,
            repository_snapshot_digest, self.clock.now(), success,
            regressions, rollbacks, evidence_digest, "",
        )
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, authority_tag=tag)

    def verify(self, record: OutcomeRecord) -> bool:
        if not _SHA256.fullmatch(record.authority_tag):
            return False
        unsigned = replace(record, authority_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(record.authority_tag, expected)


class OutcomeEchoLedger:
    """Operational feedback surface. Signals are explicitly advisory and promotion-ineligible."""

    def __init__(self, authority: OutcomeAuthority) -> None:
        self.authority = authority
        self._records: dict[str, OutcomeRecord] = {}

    def add(self, record: OutcomeRecord) -> None:
        if not self.authority.verify(record):
            raise PermissionError("untrusted outcome record")
        if record.outcome_id in self._records:
            raise ValueError("duplicate outcome record")
        self._records[record.outcome_id] = record

    def signal(self, profile_fingerprint: str, *, max_age_epochs: int = 90) -> OutcomeSignal:
        current_epoch = self.authority.clock.now()
        if not _SHA256.fullmatch(profile_fingerprint) or max_age_epochs < 1:
            raise ValueError("invalid Outcome Echo query")
        records = [
            item for item in self._records.values()
            if item.profile_fingerprint == profile_fingerprint
            and 0 <= current_epoch - item.observed_epoch <= max_age_epochs
        ]
        successes = sum(1 for item in records if item.success)
        regressions = sum(item.regressions for item in records)
        rollbacks = sum(item.rollbacks for item in records)
        samples = len(records)
        raw = (successes - regressions - rollbacks) / samples if samples else 0.0
        quality = round(max(0.0, min(1.0, raw)), 6)
        return OutcomeSignal(profile_fingerprint, samples, successes, regressions, rollbacks, quality, True)
