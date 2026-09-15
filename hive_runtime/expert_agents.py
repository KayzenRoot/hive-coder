"""Measured specialist-agent intelligence for Hive Coder.

Expertise is descriptive and benchmarked. It never grants execution authority,
permissions, credentials, desktop capabilities, or evidence trust.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Mapping, Protocol

from .orchestration import (
    AgentRole,
    FindingSeverity,
    MasterPlan,
    PlanApprovalAuthority,
    ProjectDigitalTwin,
)

_SAFE_ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,128}$")
_SAFE_TOKEN = re.compile(r"^[a-zA-Z0-9_.:/+-]{1,160}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _validate_texts(values: Iterable[str], *, field: str) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{field} must contain non-empty text")
    return result


class ContextKind(str, Enum):
    SOURCE = "source"
    TEST = "test"
    ARCHITECTURE = "architecture"
    REQUIREMENT = "requirement"
    DECISION = "decision"
    RUNTIME = "runtime"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DOCUMENTATION = "documentation"
    HISTORY = "history"
    EXTERNAL = "external"


class BenchmarkDimension(str, Enum):
    REPOSITORY_REASONING = "repository_reasoning"
    DEBUGGING = "debugging"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    CODE_REVIEW = "code_review"
    LONG_HORIZON = "long_horizon"
    TOOL_RELIABILITY = "tool_reliability"
    TAMPER_RESISTANCE = "tamper_resistance"


class CompetenceLevel(str, Enum):
    QUALIFIED = "qualified"
    SENIOR = "senior"
    PRINCIPAL = "principal"
    DISTINGUISHED = "distinguished"


class ChallengeKind(str, Enum):
    COUNTERPLAN = "counterplan"
    FAILURE_ORACLE = "failure_oracle"


@dataclass(frozen=True)
class ExpertiseCapsule:
    capsule_id: str
    version: str
    role: AgentRole
    domains: tuple[str, ...]
    principles: tuple[str, ...]
    anti_patterns: tuple[str, ...]
    review_lenses: tuple[str, ...]
    required_model_capabilities: frozenset[str]
    allowed_tool_kinds: frozenset[str]
    benchmark_dimensions: frozenset[BenchmarkDimension]
    provenance_digest: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.capsule_id) or not _SAFE_TOKEN.fullmatch(self.version):
            raise ValueError("invalid expertise capsule identity")
        _validate_texts(self.domains, field="domains")
        _validate_texts(self.principles, field="principles")
        _validate_texts(self.anti_patterns, field="anti_patterns")
        _validate_texts(self.review_lenses, field="review_lenses")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.required_model_capabilities):
            raise ValueError("invalid capsule model capability")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.allowed_tool_kinds):
            raise ValueError("invalid capsule tool kind")
        if not self.benchmark_dimensions:
            raise ValueError("capsule requires benchmark dimensions")
        if not _SHA256.fullmatch(self.provenance_digest):
            raise ValueError("capsule provenance must be sha256")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "id": self.capsule_id,
            "version": self.version,
            "role": self.role.value,
            "domains": list(self.domains),
            "principles": list(self.principles),
            "anti_patterns": list(self.anti_patterns),
            "review_lenses": list(self.review_lenses),
            "model_capabilities": sorted(self.required_model_capabilities),
            "tool_kinds": sorted(self.allowed_tool_kinds),
            "benchmarks": sorted(item.value for item in self.benchmark_dimensions),
            "provenance": self.provenance_digest,
        })


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    role: AgentRole
    capsule_fingerprint: str
    required_model_capabilities: frozenset[str]
    max_context_tokens: int
    independence_key: str
    profile_tag: str = ""

    def validate_unsigned(self) -> None:
        if not _SAFE_ID.fullmatch(self.agent_id) or not _SAFE_ID.fullmatch(self.independence_key):
            raise ValueError("invalid agent profile identity")
        if not _SHA256.fullmatch(self.capsule_fingerprint):
            raise ValueError("invalid capsule fingerprint")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.required_model_capabilities):
            raise ValueError("invalid profile capability")
        if not 512 <= self.max_context_tokens <= 2_000_000:
            raise ValueError("invalid context token budget")

    def fingerprint(self) -> str:
        self.validate_unsigned()
        return _sha({
            "agent_id": self.agent_id,
            "role": self.role.value,
            "capsule": self.capsule_fingerprint,
            "model_capabilities": sorted(self.required_model_capabilities),
            "max_context_tokens": self.max_context_tokens,
            "independence_key": self.independence_key,
        })


class AgentProfileAuthority:
    """Trusted-host seal. It proves profile provenance, not execution authority."""

    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("agent profile authority key must contain at least 32 bytes")
        self._key = bytes(key)

    def seal(self, profile: AgentProfile) -> AgentProfile:
        unsigned = replace(profile, profile_tag="")
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, profile_tag=tag)

    def verify(self, profile: AgentProfile) -> bool:
        if not _SHA256.fullmatch(profile.profile_tag):
            return False
        unsigned = replace(profile, profile_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(profile.profile_tag, expected)


class ContextTrustVerifier(Protocol):
    def __call__(self, item: "ContextItem") -> bool: ...


@dataclass(frozen=True)
class ContextItem:
    item_id: str
    kind: ContextKind
    source: str
    tags: frozenset[str]
    digest: str
    token_cost: int
    priority: int = 50

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.item_id) or not self.source.strip():
            raise ValueError("invalid context item")
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in self.tags):
            raise ValueError("invalid context tag")
        if not _SHA256.fullmatch(self.digest):
            raise ValueError("context digest must be sha256")
        if not 1 <= self.token_cost <= 2_000_000 or not 0 <= self.priority <= 100:
            raise ValueError("invalid context cost/priority")


@dataclass(frozen=True)
class ContextRequest:
    role: AgentRole
    required_tags: frozenset[str]
    preferred_tags: frozenset[str] = frozenset()
    mandatory_ids: frozenset[str] = frozenset()
    token_budget: int = 32_000
    allow_untrusted_data: bool = True

    def validate(self) -> None:
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in self.required_tags | self.preferred_tags):
            raise ValueError("invalid requested context tag")
        if any(not _SAFE_ID.fullmatch(item) for item in self.mandatory_ids):
            raise ValueError("invalid mandatory context id")
        if not 512 <= self.token_budget <= 2_000_000:
            raise ValueError("invalid context request budget")


@dataclass(frozen=True)
class ContextBinding:
    item_id: str
    digest: str
    trusted: bool
    mode: str
    score: int


@dataclass(frozen=True)
class ContextPack:
    role: AgentRole
    bindings: tuple[ContextBinding, ...]
    total_tokens: int
    required_tags: frozenset[str]

    def fingerprint(self) -> str:
        return _sha({
            "role": self.role.value,
            "bindings": [
                {"id": item.item_id, "digest": item.digest, "trusted": item.trusted,
                 "mode": item.mode, "score": item.score}
                for item in self.bindings
            ],
            "tokens": self.total_tokens,
            "required_tags": sorted(self.required_tags),
        })


class ContextLens:
    """Greedy minimum-sufficient context selector with explicit trust labels."""

    def __init__(self, trust_verifier: ContextTrustVerifier) -> None:
        self._verifier = trust_verifier

    def _score(self, item: ContextItem, request: ContextRequest) -> int:
        role_tag = f"role:{request.role.value}"
        return (
            item.priority
            + (120 if role_tag in item.tags else 0)
            + 60 * len(item.tags & request.required_tags)
            + 15 * len(item.tags & request.preferred_tags)
        )

    def select(self, items: Iterable[ContextItem], request: ContextRequest) -> ContextPack:
        request.validate()
        by_id: dict[str, ContextItem] = {}
        trusted: dict[str, bool] = {}
        for item in items:
            item.validate()
            if item.item_id in by_id:
                raise ValueError("duplicate context item")
            by_id[item.item_id] = item
            trusted[item.item_id] = self._verifier(item) is True
        if not request.mandatory_ids.issubset(by_id):
            raise ValueError("mandatory context item missing")

        selected: dict[str, ContextBinding] = {}
        total = 0

        def add(item: ContextItem) -> None:
            nonlocal total
            if item.item_id in selected:
                return
            is_trusted = trusted[item.item_id]
            if not is_trusted and not request.allow_untrusted_data:
                raise PermissionError("untrusted context is not allowed for this request")
            if total + item.token_cost > request.token_budget:
                raise RuntimeError("context budget cannot satisfy required context")
            selected[item.item_id] = ContextBinding(
                item.item_id,
                item.digest,
                is_trusted,
                "trusted_context" if is_trusted else "untrusted_data",
                self._score(item, request),
            )
            total += item.token_cost

        for item_id in sorted(request.mandatory_ids):
            add(by_id[item_id])

        def covered_required() -> frozenset[str]:
            covered: set[str] = set()
            for item_id, binding in selected.items():
                if binding.trusted:
                    covered.update(by_id[item_id].tags & request.required_tags)
            return frozenset(covered)

        while covered_required() != request.required_tags:
            missing = request.required_tags - covered_required()
            candidates = [
                item for item in by_id.values()
                if item.item_id not in selected and trusted[item.item_id] and item.tags & missing
                and total + item.token_cost <= request.token_budget
            ]
            if not candidates:
                raise RuntimeError("trusted context cannot satisfy all required tags within budget")
            candidates.sort(
                key=lambda item: (
                    -len(item.tags & missing),
                    -(self._score(item, request)),
                    item.token_cost,
                    item.item_id,
                )
            )
            add(candidates[0])

        # Fill only with positively relevant context. Untrusted data can inform, never satisfy trust gates.
        remaining = [item for item in by_id.values() if item.item_id not in selected]
        remaining.sort(key=lambda item: (-self._score(item, request), item.token_cost, item.item_id))
        for item in remaining:
            score = self._score(item, request)
            relevant = bool(item.tags & (request.required_tags | request.preferred_tags)) or f"role:{request.role.value}" in item.tags
            if not relevant or score <= item.priority:
                continue
            if not trusted[item.item_id] and not request.allow_untrusted_data:
                continue
            if total + item.token_cost <= request.token_budget:
                add(item)

        bindings = tuple(sorted(selected.values(), key=lambda item: (-item.score, item.item_id)))
        return ContextPack(request.role, bindings, total, request.required_tags)


class TruthFactVerifier(Protocol):
    def __call__(self, fact: "TruthFact") -> bool: ...


@dataclass(frozen=True)
class TruthFact:
    fact_id: str
    subject: str
    predicate: str
    object_digest: str
    provenance_digest: str
    tags: frozenset[str] = frozenset()

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.fact_id) or not self.subject.strip() or not self.predicate.strip():
            raise ValueError("invalid truth fact")
        if not _SHA256.fullmatch(self.object_digest) or not _SHA256.fullmatch(self.provenance_digest):
            raise ValueError("truth fact digests must be sha256")
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in self.tags):
            raise ValueError("invalid truth fact tag")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "id": self.fact_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object_digest,
            "provenance": self.provenance_digest,
            "tags": sorted(self.tags),
        })


class CodeTruthMap:
    """Provenance-backed fact index. Only host-verified facts are authoritative."""

    def __init__(self, facts: Iterable[TruthFact], verifier: TruthFactVerifier) -> None:
        self._facts: dict[str, TruthFact] = {}
        self._verified: set[str] = set()
        for fact in facts:
            fact.validate()
            if fact.fact_id in self._facts:
                raise ValueError("duplicate truth fact")
            self._facts[fact.fact_id] = fact
            if verifier(fact) is True:
                self._verified.add(fact.fact_id)

    def is_verified(self, fact_id: str) -> bool:
        return fact_id in self._verified

    def fact_fingerprint(self, fact_id: str) -> str:
        if fact_id not in self._verified:
            raise PermissionError("truth fact is not host verified")
        return self._facts[fact_id].fingerprint()

    def query(self, tags: Iterable[str], *, verified_only: bool = True) -> tuple[TruthFact, ...]:
        wanted = frozenset(tags)
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in wanted):
            raise ValueError("invalid truth query tag")
        facts = [fact for fact in self._facts.values() if wanted.issubset(fact.tags)]
        if verified_only:
            facts = [fact for fact in facts if fact.fact_id in self._verified]
        return tuple(sorted(facts, key=lambda fact: fact.fact_id))

    def fingerprint(self) -> str:
        return _sha([self._facts[item].fingerprint() for item in sorted(self._verified)])


@dataclass(frozen=True)
class ArchitecturalInvariant:
    invariant_id: str
    statement_digest: str
    node_ids: frozenset[str]
    fact_ids: frozenset[str]
    critical: bool = False

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.invariant_id) or not _SHA256.fullmatch(self.statement_digest):
            raise ValueError("invalid architectural invariant")
        if not self.node_ids or any(not _SAFE_ID.fullmatch(item) for item in self.node_ids):
            raise ValueError("architectural invariant requires valid nodes")
        if not self.fact_ids or any(not _SAFE_ID.fullmatch(item) for item in self.fact_ids):
            raise ValueError("architectural invariant requires provenance facts")


class ArchitecturalGenome:
    """Evidence-bound architectural invariants with deterministic drift checks."""

    def __init__(self, twin: ProjectDigitalTwin, truth: CodeTruthMap,
                 invariants: Iterable[ArchitecturalInvariant]) -> None:
        self.twin_fingerprint = twin.fingerprint()
        self.truth_fingerprint = truth.fingerprint()
        self._invariants: dict[str, ArchitecturalInvariant] = {}
        self._fact_fingerprints: dict[str, dict[str, str]] = {}
        for invariant in invariants:
            invariant.validate()
            if invariant.invariant_id in self._invariants:
                raise ValueError("duplicate architectural invariant")
            twin.validate_targets(invariant.node_ids)
            fact_fingerprints = {fact_id: truth.fact_fingerprint(fact_id) for fact_id in invariant.fact_ids}
            self._invariants[invariant.invariant_id] = invariant
            self._fact_fingerprints[invariant.invariant_id] = fact_fingerprints
        if not self._invariants:
            raise ValueError("architectural genome requires invariants")

    def fingerprint(self) -> str:
        return _sha({
            "twin": self.twin_fingerprint,
            "truth": self.truth_fingerprint,
            "invariants": [
                {
                    "id": item.invariant_id,
                    "statement": item.statement_digest,
                    "nodes": sorted(item.node_ids),
                    "facts": self._fact_fingerprints[item.invariant_id],
                    "critical": item.critical,
                }
                for item in sorted(self._invariants.values(), key=lambda inv: inv.invariant_id)
            ],
        })

    def detect_drift(self, current_twin: ProjectDigitalTwin, current_truth: CodeTruthMap) -> tuple[str, ...]:
        drifted: list[str] = []
        twin_changed = current_twin.fingerprint() != self.twin_fingerprint
        for invariant_id, invariant in sorted(self._invariants.items()):
            fact_changed = False
            for fact_id, old_fingerprint in self._fact_fingerprints[invariant_id].items():
                try:
                    fact_changed = fact_changed or current_truth.fact_fingerprint(fact_id) != old_fingerprint
                except (KeyError, PermissionError):
                    fact_changed = True
            if twin_changed or fact_changed:
                drifted.append(invariant_id)
        return tuple(drifted)


class BenchmarkTrustVerifier(Protocol):
    def __call__(self, result: "BenchmarkResult") -> bool: ...


@dataclass(frozen=True)
class BenchmarkResult:
    result_id: str
    agent_id: str
    dimension: BenchmarkDimension
    suite: str
    suite_version: str
    successes: int
    total: int
    critical_failures: int
    policy_violations: int
    tamper_events: int
    evidence_digest: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.result_id) or not _SAFE_ID.fullmatch(self.agent_id):
            raise ValueError("invalid benchmark result identity")
        if not _SAFE_TOKEN.fullmatch(self.suite) or not _SAFE_TOKEN.fullmatch(self.suite_version):
            raise ValueError("invalid benchmark suite identity")
        if not 0 <= self.successes <= self.total or self.total <= 0:
            raise ValueError("invalid benchmark counts")
        if min(self.critical_failures, self.policy_violations, self.tamper_events) < 0:
            raise ValueError("invalid benchmark incident counts")
        if not _SHA256.fullmatch(self.evidence_digest):
            raise ValueError("benchmark evidence must be sha256")


@dataclass(frozen=True)
class DimensionScore:
    dimension: BenchmarkDimension
    successes: int
    samples: int
    pass_rate: float
    lower_bound: float
    critical_failures: int
    policy_violations: int
    tamper_events: int
    evidence_ids: tuple[str, ...]
    suites: tuple[str, ...]


class ExperienceLedger:
    """Stores benchmark claims but aggregates only trusted-host verified evidence."""

    def __init__(self, verifier: BenchmarkTrustVerifier) -> None:
        self._verifier = verifier
        self._results: dict[str, BenchmarkResult] = {}
        self._trusted: set[str] = set()

    def add(self, result: BenchmarkResult) -> None:
        result.validate()
        if result.result_id in self._results:
            raise ValueError("duplicate benchmark result")
        self._results[result.result_id] = result
        if self._verifier(result) is True:
            self._trusted.add(result.result_id)

    @staticmethod
    def wilson_lower_bound(successes: int, total: int, z: float = 1.96) -> float:
        if total <= 0 or successes < 0 or successes > total or z <= 0:
            raise ValueError("invalid Wilson score inputs")
        p = successes / total
        z2 = z * z
        denominator = 1.0 + z2 / total
        centre = p + z2 / (2.0 * total)
        margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
        return max(0.0, (centre - margin) / denominator)

    def score(self, agent_id: str, dimension: BenchmarkDimension) -> DimensionScore:
        results = [
            result for result_id, result in self._results.items()
            if result_id in self._trusted and result.agent_id == agent_id and result.dimension is dimension
        ]
        successes = sum(item.successes for item in results)
        samples = sum(item.total for item in results)
        lower = self.wilson_lower_bound(successes, samples) if samples else 0.0
        return DimensionScore(
            dimension, successes, samples, round(successes / samples, 6) if samples else 0.0,
            round(lower, 6),
            sum(item.critical_failures for item in results),
            sum(item.policy_violations for item in results),
            sum(item.tamper_events for item in results),
            tuple(sorted(item.result_id for item in results)),
            tuple(sorted({f"{item.suite}@{item.suite_version}" for item in results})),
        )


@dataclass(frozen=True)
class CompetenceStandard:
    level: CompetenceLevel
    required_dimensions: frozenset[BenchmarkDimension]
    min_samples_per_dimension: int
    min_lower_bound: float
    min_independent_suites: int = 2

    def validate(self) -> None:
        if not self.required_dimensions:
            raise ValueError("competence standard requires dimensions")
        if not 5 <= self.min_samples_per_dimension <= 100_000:
            raise ValueError("invalid competence sample floor")
        if not 0.0 < self.min_lower_bound <= 1.0:
            raise ValueError("invalid competence lower bound")
        if not 1 <= self.min_independent_suites <= 20:
            raise ValueError("invalid independent-suite floor")


@dataclass(frozen=True)
class CompetenceReport:
    agent_id: str
    level: CompetenceLevel
    scores: tuple[DimensionScore, ...]
    passed: bool
    blocking_codes: tuple[str, ...]

    def fingerprint(self) -> str:
        return _sha({
            "agent": self.agent_id,
            "level": self.level.value,
            "passed": self.passed,
            "blocking": list(self.blocking_codes),
            "scores": [
                {
                    "dimension": score.dimension.value,
                    "successes": score.successes,
                    "samples": score.samples,
                    "lower": score.lower_bound,
                    "critical": score.critical_failures,
                    "policy": score.policy_violations,
                    "tamper": score.tamper_events,
                    "evidence": list(score.evidence_ids),
                    "suites": list(score.suites),
                }
                for score in self.scores
            ],
        })


class ExperienceRouter:
    """Routes on verified measured competence, never model names or self-description."""

    def __init__(self, profile_authority: AgentProfileAuthority, ledger: ExperienceLedger) -> None:
        self.profile_authority = profile_authority
        self.ledger = ledger

    def evaluate(self, profile: AgentProfile, capsule: ExpertiseCapsule,
                 standard: CompetenceStandard) -> CompetenceReport:
        standard.validate(); capsule.validate()
        if not self.profile_authority.verify(profile):
            raise PermissionError("agent profile seal invalid")
        if profile.role is not capsule.role or profile.capsule_fingerprint != capsule.fingerprint():
            raise ValueError("agent profile/capsule mismatch")
        if not standard.required_dimensions.issubset(capsule.benchmark_dimensions):
            raise ValueError("capsule does not cover required competence dimensions")
        scores = tuple(self.ledger.score(profile.agent_id, dim) for dim in sorted(standard.required_dimensions, key=lambda d: d.value))
        blocking: list[str] = []
        for score in scores:
            prefix = score.dimension.value
            if score.samples < standard.min_samples_per_dimension:
                blocking.append(f"{prefix}:insufficient_samples")
            if score.lower_bound < standard.min_lower_bound:
                blocking.append(f"{prefix}:confidence_below_threshold")
            if len(score.suites) < standard.min_independent_suites:
                blocking.append(f"{prefix}:insufficient_suite_diversity")
            if score.critical_failures:
                blocking.append(f"{prefix}:critical_failure")
            if score.policy_violations:
                blocking.append(f"{prefix}:policy_violation")
            if score.tamper_events:
                blocking.append(f"{prefix}:tamper_event")
        return CompetenceReport(profile.agent_id, standard.level, scores, not blocking, tuple(blocking))

    def route(self, profiles: Iterable[AgentProfile], capsules: Mapping[str, ExpertiseCapsule],
              role: AgentRole, standard: CompetenceStandard) -> tuple[AgentProfile, CompetenceReport]:
        candidates: list[tuple[AgentProfile, CompetenceReport]] = []
        for profile in profiles:
            if profile.role is not role:
                continue
            capsule = capsules.get(profile.capsule_fingerprint)
            if capsule is None:
                continue
            report = self.evaluate(profile, capsule, standard)
            if report.passed:
                candidates.append((profile, report))
        if not candidates:
            raise LookupError(f"no measured agent satisfies {role.value} competence standard")

        def route_key(item: tuple[AgentProfile, CompetenceReport]) -> tuple[float, float, int, str]:
            profile, report = item
            lowers = [score.lower_bound for score in report.scores]
            total_samples = sum(score.samples for score in report.scores)
            return (min(lowers), sum(lowers) / len(lowers), total_samples, profile.agent_id)

        candidates.sort(key=route_key, reverse=True)
        return candidates[0]


class ExpertAgentRegistry:
    def __init__(self, profile_authority: AgentProfileAuthority) -> None:
        self.profile_authority = profile_authority
        self._capsules: dict[str, ExpertiseCapsule] = {}
        self._profiles: dict[str, AgentProfile] = {}

    def add_capsule(self, capsule: ExpertiseCapsule) -> str:
        fingerprint = capsule.fingerprint()
        if fingerprint in self._capsules:
            raise ValueError("duplicate expertise capsule")
        self._capsules[fingerprint] = capsule
        return fingerprint

    def add_profile(self, profile: AgentProfile) -> None:
        if not self.profile_authority.verify(profile):
            raise PermissionError("unsealed agent profile")
        if profile.agent_id in self._profiles:
            raise ValueError("duplicate agent profile")
        capsule = self._capsules.get(profile.capsule_fingerprint)
        if capsule is None or capsule.role is not profile.role:
            raise ValueError("profile references missing or wrong-role capsule")
        if not capsule.required_model_capabilities.issubset(profile.required_model_capabilities):
            raise ValueError("profile lacks capsule-required model capabilities")
        self._profiles[profile.agent_id] = profile

    def profiles_for(self, role: AgentRole) -> tuple[AgentProfile, ...]:
        return tuple(sorted((p for p in self._profiles.values() if p.role is role), key=lambda p: p.agent_id))

    def capsules(self) -> Mapping[str, ExpertiseCapsule]:
        return dict(self._capsules)


@dataclass(frozen=True)
class AgentAssignment:
    step_id: str
    agent_id: str
    profile_fingerprint: str
    capsule_fingerprint: str
    competence_fingerprint: str
    independence_key: str


class AgentMesh:
    """Binds sealed MasterPlan steps to measured specialist profiles."""

    OVERSIGHT_ROLES = frozenset({AgentRole.SECURITY, AgentRole.QA, AgentRole.REVIEWER})

    def __init__(self, approval_authority: PlanApprovalAuthority, twin: ProjectDigitalTwin,
                 registry: ExpertAgentRegistry, router: ExperienceRouter,
                 standards: Mapping[AgentRole, CompetenceStandard]) -> None:
        self.approval_authority = approval_authority
        self.twin = twin
        self.registry = registry
        self.router = router
        self.standards = dict(standards)

    def assign(self, master: MasterPlan) -> tuple[AgentAssignment, ...]:
        if not self.approval_authority.verify(master):
            raise PermissionError("master plan approval seal invalid")
        if master.twin_fingerprint != self.twin.fingerprint():
            raise ValueError("project digital twin changed after master plan approval")
        assignments: list[AgentAssignment] = []
        implementation_lineages: set[str] = set()
        capsules = self.registry.capsules()
        for step in master.steps:
            standard = self.standards.get(step.role)
            if standard is None:
                raise LookupError(f"no competence standard configured for role {step.role.value}")
            profile, report = self.router.route(self.registry.profiles_for(step.role), capsules, step.role, standard)
            if step.role in self.OVERSIGHT_ROLES and profile.independence_key in implementation_lineages:
                raise PermissionError("oversight agent is not independent from implementation lineage")
            if step.role not in self.OVERSIGHT_ROLES:
                implementation_lineages.add(profile.independence_key)
            assignments.append(AgentAssignment(
                step.step_id,
                profile.agent_id,
                profile.fingerprint(),
                profile.capsule_fingerprint,
                report.fingerprint(),
                profile.independence_key,
            ))
        return tuple(assignments)


@dataclass(frozen=True)
class ChallengeAssessment:
    severity: FindingSeverity
    code: str
    target_step: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not _SAFE_TOKEN.fullmatch(self.code):
            raise ValueError("invalid challenge code")
        if self.target_step is not None and not _SAFE_ID.fullmatch(self.target_step):
            raise ValueError("invalid challenge target")
        if any(not _SAFE_ID.fullmatch(ref) for ref in self.evidence_refs):
            raise ValueError("invalid challenge evidence reference")


@dataclass(frozen=True)
class ChallengeFinding:
    kind: ChallengeKind
    challenger_agent_id: str
    severity: FindingSeverity
    code: str
    target_step: str | None
    evidence_refs: tuple[str, ...]


class ChallengePort(Protocol):
    def __call__(self, master: MasterPlan) -> Iterable[ChallengeAssessment]: ...


@dataclass(frozen=True)
class ChallengeReport:
    findings: tuple[ChallengeFinding, ...]
    blocked: bool
    blocking_codes: tuple[str, ...]


@dataclass(frozen=True)
class ChallengePolicy:
    required_kinds: frozenset[ChallengeKind] = frozenset({ChallengeKind.COUNTERPLAN, ChallengeKind.FAILURE_ORACLE})
    blocking_severities: frozenset[FindingSeverity] = frozenset({FindingSeverity.MEDIUM, FindingSeverity.HIGH, FindingSeverity.CRITICAL})


class AdversarialChallengeEngine:
    """Runs bounded host-identified challengers. Findings advise/block; they grant nothing."""

    def __init__(self, profile_authority: AgentProfileAuthority,
                 policy: ChallengePolicy = ChallengePolicy()) -> None:
        self.profile_authority = profile_authority
        self.policy = policy

    def run(self, master: MasterPlan,
            challengers: Mapping[ChallengeKind, tuple[AgentProfile, ChallengePort]]) -> ChallengeReport:
        if not self.policy.required_kinds.issubset(challengers):
            raise ValueError("required adversarial challenge kind missing")
        known_steps = {step.step_id for step in master.steps}
        findings: list[ChallengeFinding] = []
        lineages: set[str] = set()
        for kind in sorted(self.policy.required_kinds, key=lambda item: item.value):
            profile, port = challengers[kind]
            if not self.profile_authority.verify(profile):
                raise PermissionError("challenger profile seal invalid")
            if profile.independence_key in lineages:
                raise PermissionError("adversarial challengers must be independence-separated")
            lineages.add(profile.independence_key)
            assessments = tuple(port(master))
            if not assessments:
                raise ValueError(f"challenge produced no assessment: {kind.value}")
            for assessment in assessments:
                if not isinstance(assessment, ChallengeAssessment):
                    raise TypeError("challenge port returned invalid assessment")
                assessment.validate()
                if assessment.target_step is not None and assessment.target_step not in known_steps:
                    raise ValueError("challenge references unknown step")
                findings.append(ChallengeFinding(
                    kind, profile.agent_id, assessment.severity, assessment.code,
                    assessment.target_step, assessment.evidence_refs,
                ))
        blocking = tuple(sorted({item.code for item in findings if item.severity in self.policy.blocking_severities}))
        return ChallengeReport(tuple(findings), bool(blocking), blocking)


def required_dimensions_for_role(role: AgentRole) -> frozenset[BenchmarkDimension]:
    common = {BenchmarkDimension.REPOSITORY_REASONING, BenchmarkDimension.TOOL_RELIABILITY,
              BenchmarkDimension.TAMPER_RESISTANCE}
    role_specific: dict[AgentRole, set[BenchmarkDimension]] = {
        AgentRole.PLANNER: {BenchmarkDimension.ARCHITECTURE, BenchmarkDimension.LONG_HORIZON, BenchmarkDimension.CODE_REVIEW},
        AgentRole.ARCHITECT: {BenchmarkDimension.ARCHITECTURE, BenchmarkDimension.MAINTAINABILITY, BenchmarkDimension.SECURITY, BenchmarkDimension.LONG_HORIZON},
        AgentRole.BACKEND: {BenchmarkDimension.DEBUGGING, BenchmarkDimension.TESTING, BenchmarkDimension.SECURITY, BenchmarkDimension.PERFORMANCE, BenchmarkDimension.MAINTAINABILITY},
        AgentRole.FRONTEND: {BenchmarkDimension.DEBUGGING, BenchmarkDimension.TESTING, BenchmarkDimension.PERFORMANCE, BenchmarkDimension.MAINTAINABILITY},
        AgentRole.DATA: {BenchmarkDimension.DEBUGGING, BenchmarkDimension.TESTING, BenchmarkDimension.PERFORMANCE, BenchmarkDimension.SECURITY},
        AgentRole.SECURITY: {BenchmarkDimension.SECURITY, BenchmarkDimension.CODE_REVIEW, BenchmarkDimension.TESTING, BenchmarkDimension.DEBUGGING},
        AgentRole.QA: {BenchmarkDimension.TESTING, BenchmarkDimension.DEBUGGING, BenchmarkDimension.CODE_REVIEW, BenchmarkDimension.LONG_HORIZON},
        AgentRole.PERFORMANCE: {BenchmarkDimension.PERFORMANCE, BenchmarkDimension.DEBUGGING, BenchmarkDimension.TESTING, BenchmarkDimension.ARCHITECTURE},
        AgentRole.DEVOPS: {BenchmarkDimension.LONG_HORIZON, BenchmarkDimension.SECURITY, BenchmarkDimension.TESTING, BenchmarkDimension.DEBUGGING},
        AgentRole.REVIEWER: {BenchmarkDimension.CODE_REVIEW, BenchmarkDimension.DEBUGGING, BenchmarkDimension.SECURITY, BenchmarkDimension.MAINTAINABILITY},
        AgentRole.DOCUMENTATION: {BenchmarkDimension.REPOSITORY_REASONING, BenchmarkDimension.MAINTAINABILITY, BenchmarkDimension.CODE_REVIEW},
    }
    return frozenset(common | role_specific[role])


def distinguished_standard_for(role: AgentRole) -> CompetenceStandard:
    return CompetenceStandard(
        CompetenceLevel.DISTINGUISHED,
        required_dimensions_for_role(role),
        min_samples_per_dimension=40,
        min_lower_bound=0.80,
        min_independent_suites=2,
    )


def build_default_expertise_capsules(provenance_digest: str) -> tuple[ExpertiseCapsule, ...]:
    if not _SHA256.fullmatch(provenance_digest):
        raise ValueError("default capsule provenance must be sha256")

    doctrine: dict[AgentRole, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
        AgentRole.PLANNER: (
            ("problem-framing", "decomposition", "risk", "evidence"),
            ("prove the problem before optimizing the solution", "separate facts from assumptions", "make acceptance and STOP conditions executable", "minimize change radius and preserve reversibility", "prefer plans that expose uncertainty early"),
            ("solution-first planning", "hidden assumptions", "unbounded work graphs", "model prose as completion evidence"),
            ("goal coverage", "dependency ordering", "rollback path", "verification strategy", "unknowns and decision points"),
        ),
        AgentRole.ARCHITECT: (
            ("boundaries", "evolvability", "resilience", "data-ownership"),
            ("preserve invariants before abstractions", "optimize coupling and cohesion", "design failure modes explicitly", "make ownership and contracts unambiguous", "prefer the simplest architecture that survives expected change"),
            ("distributed monolith", "premature abstraction", "shared mutable ownership", "hidden cross-layer coupling"),
            ("invariants", "dependency direction", "operational failure", "migration path", "long-term change cost"),
        ),
        AgentRole.BACKEND: (
            ("correctness", "api-contracts", "concurrency", "observability"),
            ("make contracts explicit", "design idempotency and retries together", "treat concurrency as a first-class failure source", "keep transactions and side effects bounded", "instrument behavior that operators must diagnose"),
            ("silent partial failure", "retry without idempotency", "exception swallowing", "implicit schema contract"),
            ("edge cases", "transaction boundaries", "concurrency", "error semantics", "backward compatibility"),
        ),
        AgentRole.FRONTEND: (
            ("state", "accessibility", "performance", "ux-correctness"),
            ("make state ownership explicit", "design loading empty error and recovery states", "preserve keyboard and accessibility semantics", "measure rendering and network cost", "keep UI behavior deterministic under latency"),
            ("global state by convenience", "happy-path-only UI", "layout thrash", "inaccessible interaction"),
            ("state transitions", "accessibility", "responsive behavior", "failure UX", "rendering cost"),
        ),
        AgentRole.DATA: (
            ("schema", "migrations", "integrity", "query-plans"),
            ("protect data invariants at the strongest practical layer", "make migrations backward-compatible and resumable", "profile query plans before indexing", "model isolation and concurrency explicitly", "design recovery before destructive change"),
            ("irreversible migration", "application-only integrity", "index cargo cult", "unbounded query"),
            ("integrity", "migration safety", "isolation", "query plan", "backup and restore"),
        ),
        AgentRole.SECURITY: (
            ("threat-modeling", "trust-boundaries", "least-privilege", "secrets"),
            ("treat every boundary crossing as hostile until proven otherwise", "least privilege is the default", "bind authorization to exact subject action and scope", "never trust producer-declared trust", "design revocation and audit with authorization"),
            ("ambient authority", "string-based authorization", "secret logging", "fail-open security", "self-attested trust"),
            ("attack surface", "identity binding", "injection", "secret lifecycle", "revocation and audit"),
        ),
        AgentRole.QA: (
            ("behavioral-testing", "adversarial-testing", "reproducibility", "diagnostics"),
            ("test contracts rather than implementation trivia", "seek counterexamples and boundary cases", "make failures reproducible", "prefer deterministic or property-based evidence where possible", "verify negative paths and recovery"),
            ("snapshot-only confidence", "flaky test acceptance", "mocking the behavior under test", "coverage percentage as quality"),
            ("contract coverage", "negative paths", "race and recovery", "test independence", "diagnostic quality"),
        ),
        AgentRole.PERFORMANCE: (
            ("profiling", "complexity", "latency", "resource-budgets"),
            ("measure before optimizing", "optimize p95 and p99 where users feel them", "track algorithmic and allocation complexity", "treat caches as correctness systems", "budget CPU memory IO and network explicitly"),
            ("microbenchmark theater", "cache without invalidation", "average-only latency", "optimization without profile"),
            ("hot path", "tail latency", "allocation", "contention", "performance regression evidence"),
        ),
        AgentRole.DEVOPS: (
            ("reproducibility", "delivery", "rollback", "operability"),
            ("make builds reproducible", "promote immutable artifacts", "automate rollback and health verification", "separate deploy from release", "make operational state observable"),
            ("mutable production server", "manual-only recovery", "latest-tag dependency", "deployment without rollback"),
            ("artifact provenance", "rollout safety", "health gates", "secret boundary", "disaster recovery"),
        ),
        AgentRole.REVIEWER: (
            ("semantic-diff", "defect-detection", "maintainability", "risk"),
            ("review behavior and invariants before style", "trace changed assumptions through dependencies", "look for missing negative cases", "challenge concurrency security and migration edges", "demand evidence proportional to risk"),
            ("style-only review", "rubber stamp", "diff-local tunnel vision", "test presence as proof"),
            ("semantic regression", "scope creep", "edge cases", "evidence quality", "future maintenance cost"),
        ),
        AgentRole.DOCUMENTATION: (
            ("source-of-truth", "runbooks", "contracts", "migration-guides"),
            ("document the current verified system", "make examples executable where practical", "state ownership version and prerequisites", "record failure and recovery paths", "keep decisions linked to evidence"),
            ("aspirational docs presented as current", "stale copy-paste", "undocumented breaking change", "example without validation"),
            ("version alignment", "operational clarity", "contract precision", "migration completeness", "evidence links"),
        ),
    }

    capsules: list[ExpertiseCapsule] = []
    for role in AgentRole:
        domains, principles, anti_patterns, review_lenses = doctrine[role]
        capsules.append(ExpertiseCapsule(
            capsule_id=f"hive.{role.value}.elite-core",
            version="1.0.0",
            role=role,
            domains=domains,
            principles=principles,
            anti_patterns=anti_patterns,
            review_lenses=review_lenses,
            required_model_capabilities=frozenset({"tool_calling", "structured_output"}),
            allowed_tool_kinds=frozenset({"repository.read", "repository.search", "tests.run", "analysis.static"}),
            benchmark_dimensions=required_dimensions_for_role(role),
            provenance_digest=provenance_digest,
        ))
    return tuple(capsules)
