"""Trusted benchmark evidence, confidence-adjusted competence, and routing."""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Protocol, Iterable, Mapping
from .orchestration import AgentRole
from .expert_common import _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha, BenchmarkDimension, CompetenceLevel
from .expert_identity import AgentProfile, AgentProfileAuthority, ExpertiseCapsule

class BenchmarkTrustVerifier(Protocol):
    def __call__(self, result: "BenchmarkResult") -> bool: ...


@dataclass(frozen=True)
class BenchmarkResult:
    result_id: str
    agent_id: str
    profile_fingerprint: str
    dimension: BenchmarkDimension
    suite_family: str
    suite: str
    suite_version: str
    sample_set_digest: str
    successes: int
    total: int
    critical_failures: int
    policy_violations: int
    tamper_events: int
    evidence_digest: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.result_id) or not _SAFE_ID.fullmatch(self.agent_id):
            raise ValueError("invalid benchmark result identity")
        if not _SHA256.fullmatch(self.profile_fingerprint):
            raise ValueError("benchmark result must bind an exact agent profile")
        if not _SAFE_TOKEN.fullmatch(self.suite_family) or not _SAFE_TOKEN.fullmatch(self.suite) or not _SAFE_TOKEN.fullmatch(self.suite_version):
            raise ValueError("invalid benchmark suite identity")
        if not _SHA256.fullmatch(self.sample_set_digest):
            raise ValueError("benchmark sample set must be sha256")
        if not 0 <= self.successes <= self.total or self.total <= 0:
            raise ValueError("invalid benchmark counts")
        if min(self.critical_failures, self.policy_violations, self.tamper_events) < 0:
            raise ValueError("invalid benchmark incident counts")
        if not _SHA256.fullmatch(self.evidence_digest):
            raise ValueError("benchmark evidence must be sha256")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "result_id": self.result_id,
            "agent_id": self.agent_id,
            "profile": self.profile_fingerprint,
            "dimension": self.dimension.value,
            "suite_family": self.suite_family,
            "suite": self.suite,
            "suite_version": self.suite_version,
            "sample_set": self.sample_set_digest,
            "successes": self.successes,
            "total": self.total,
            "critical_failures": self.critical_failures,
            "policy_violations": self.policy_violations,
            "tamper_events": self.tamper_events,
            "evidence": self.evidence_digest,
        })


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
    result_fingerprints: tuple[str, ...]
    suites: tuple[str, ...]
    suite_families: tuple[str, ...]


class ExperienceLedger:
    """Stores benchmark claims but aggregates only trusted-host verified evidence."""

    def __init__(self, verifier: BenchmarkTrustVerifier) -> None:
        self._verifier = verifier
        self._results: dict[str, BenchmarkResult] = {}
        self._trusted: set[str] = set()
        self._trusted_sample_sets: set[tuple[str, BenchmarkDimension, str]] = set()

    def add(self, result: BenchmarkResult) -> None:
        result.validate()
        if result.result_id in self._results:
            raise ValueError("duplicate benchmark result")
        trusted = self._verifier(result) is True
        sample_key = (result.profile_fingerprint, result.dimension, result.sample_set_digest)
        if trusted and sample_key in self._trusted_sample_sets:
            raise ValueError("trusted benchmark sample set cannot be counted twice")
        self._results[result.result_id] = result
        if trusted:
            self._trusted.add(result.result_id)
            self._trusted_sample_sets.add(sample_key)

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

    def score(self, profile: AgentProfile, dimension: BenchmarkDimension) -> DimensionScore:
        profile_fingerprint = profile.fingerprint()
        results = [
            result for result_id, result in self._results.items()
            if result_id in self._trusted and result.agent_id == profile.agent_id
            and result.profile_fingerprint == profile_fingerprint and result.dimension is dimension
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
            tuple(sorted(item.fingerprint() for item in results)),
            tuple(sorted({f"{item.suite}@{item.suite_version}" for item in results})),
            tuple(sorted({item.suite_family for item in results})),
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
    profile_fingerprint: str
    level: CompetenceLevel
    scores: tuple[DimensionScore, ...]
    passed: bool
    blocking_codes: tuple[str, ...]

    def fingerprint(self) -> str:
        return _sha({
            "agent": self.agent_id,
            "profile": self.profile_fingerprint,
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
                    "result_fingerprints": list(score.result_fingerprints),
                    "suites": list(score.suites),
                    "suite_families": list(score.suite_families),
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
        scores = tuple(self.ledger.score(profile, dim) for dim in sorted(standard.required_dimensions, key=lambda d: d.value))
        blocking: list[str] = []
        for score in scores:
            prefix = score.dimension.value
            if score.samples < standard.min_samples_per_dimension:
                blocking.append(f"{prefix}:insufficient_samples")
            if score.lower_bound < standard.min_lower_bound:
                blocking.append(f"{prefix}:confidence_below_threshold")
            if len(score.suite_families) < standard.min_independent_suites:
                blocking.append(f"{prefix}:insufficient_suite_diversity")
            if score.critical_failures:
                blocking.append(f"{prefix}:critical_failure")
            if score.policy_violations:
                blocking.append(f"{prefix}:policy_violation")
            if score.tamper_events:
                blocking.append(f"{prefix}:tamper_event")
        return CompetenceReport(profile.agent_id, profile.fingerprint(), standard.level, scores, not blocking, tuple(blocking))

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
