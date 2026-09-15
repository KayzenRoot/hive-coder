"""Hive Elite Specialist Forge and Autonomous Engineering Arena.

This layer ranks already-certified exact-stack specialists. It never grants execution
authority and never lets speed/cost compensate for safety or quality floors.
"""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Iterable

from .certification_contracts import (
    EvaluationSuite,
    ExecutionStackDescriptor,
    StackGenomeAuthority,
    SuiteLineageAuthority,
)
from .evaluation_runtime import ShadowBenchCase
from .expert_common import BenchmarkDimension, _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha
from .expert_evaluation import ExperienceLedger
from .expert_identity import AgentProfile, AgentProfileAuthority
from .orchestration import AgentRole


@dataclass(frozen=True)
class SpecializationPack:
    """Descriptive language/framework/domain doctrine. It carries no permission fields."""

    pack_id: str
    version: str
    role: AgentRole
    language: str
    framework: str
    domains: tuple[str, ...]
    benchmark_dimensions: frozenset[BenchmarkDimension]
    base_capsule_fingerprint: str
    doctrine_digest: str
    provenance_digest: str
    authority_tag: str = ""

    def validate_unsigned(self) -> None:
        for token in (self.pack_id, self.version, self.language, self.framework):
            if not _SAFE_TOKEN.fullmatch(token):
                raise ValueError("invalid specialization pack token")
        if not self.domains or any(not _SAFE_TOKEN.fullmatch(item) for item in self.domains):
            raise ValueError("specialization pack requires safe domains")
        if len(self.domains) != len(set(self.domains)):
            raise ValueError("duplicate specialization domain")
        if not self.benchmark_dimensions:
            raise ValueError("specialization pack requires benchmark dimensions")
        for digest in (self.base_capsule_fingerprint, self.doctrine_digest, self.provenance_digest):
            if not _SHA256.fullmatch(digest):
                raise ValueError("specialization pack digests must be sha256")

    def fingerprint(self) -> str:
        self.validate_unsigned()
        return _sha({
            "id": self.pack_id,
            "version": self.version,
            "role": self.role.value,
            "language": self.language,
            "framework": self.framework,
            "domains": sorted(self.domains),
            "dimensions": sorted(item.value for item in self.benchmark_dimensions),
            "capsule": self.base_capsule_fingerprint,
            "doctrine": self.doctrine_digest,
            "provenance": self.provenance_digest,
        })


class SpecializationPackAuthority:
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("specialization authority key must contain at least 32 bytes")
        self._key = bytes(key)

    def seal(self, pack: SpecializationPack) -> SpecializationPack:
        unsigned = replace(pack, authority_tag="")
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, authority_tag=tag)

    def verify(self, pack: SpecializationPack) -> bool:
        if not _SHA256.fullmatch(pack.authority_tag):
            return False
        unsigned = replace(pack, authority_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(pack.authority_tag, expected)


@dataclass(frozen=True)
class SkillGenome:
    """Exact skill composition descriptor. Descriptive only, never activation authority."""

    skill_ids: tuple[str, ...]
    skill_digests: tuple[str, ...]
    protocol_version: str = "skill-genome-v1"

    def fingerprint(self) -> str:
        if not _SAFE_TOKEN.fullmatch(self.protocol_version):
            raise ValueError("invalid SkillGenome protocol")
        if len(self.skill_ids) != len(self.skill_digests):
            raise ValueError("SkillGenome ids/digests length mismatch")
        if len(self.skill_ids) != len(set(self.skill_ids)):
            raise ValueError("duplicate SkillGenome skill")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.skill_ids):
            raise ValueError("invalid SkillGenome skill id")
        if any(not _SHA256.fullmatch(item) for item in self.skill_digests):
            raise ValueError("invalid SkillGenome skill digest")
        pairs = sorted(zip(self.skill_ids, self.skill_digests))
        return _sha({"protocol": self.protocol_version, "skills": pairs})


@dataclass(frozen=True)
class SpecialistBlueprint:
    blueprint_id: str
    profile_fingerprint: str
    stack_fingerprint: str
    repository_snapshot_digest: str
    semantic_twin_fingerprint: str
    specialization_pack_fingerprint: str
    skill_genome_fingerprint: str
    certification_evidence_fingerprint: str
    forge_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.blueprint_id):
            raise ValueError("invalid specialist blueprint id")
        for digest in (
            self.profile_fingerprint,
            self.stack_fingerprint,
            self.repository_snapshot_digest,
            self.semantic_twin_fingerprint,
            self.specialization_pack_fingerprint,
            self.skill_genome_fingerprint,
            self.certification_evidence_fingerprint,
        ):
            if not _SHA256.fullmatch(digest):
                raise ValueError("specialist blueprint digest must be sha256")
        return _sha({
            "id": self.blueprint_id,
            "profile": self.profile_fingerprint,
            "stack": self.stack_fingerprint,
            "repository": self.repository_snapshot_digest,
            "twin": self.semantic_twin_fingerprint,
            "pack": self.specialization_pack_fingerprint,
            "skills": self.skill_genome_fingerprint,
            "certification": self.certification_evidence_fingerprint,
        })


CertificationVerifier = Callable[[AgentProfile, str, str], bool]


class SpecialistForge:
    """ForgeSeal authority for exact-stack specialists that already hold valid certification."""

    def __init__(
        self,
        key: bytes,
        profile_authority: AgentProfileAuthority,
        pack_authority: SpecializationPackAuthority,
        certification_verifier: CertificationVerifier,
    ) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("ForgeSeal key must contain at least 32 bytes")
        if not callable(certification_verifier):
            raise TypeError("ForgeSeal requires trusted certification verifier")
        self._key = bytes(key)
        self.profile_authority = profile_authority
        self.pack_authority = pack_authority
        self.certification_verifier = certification_verifier
        self.stack_genome = StackGenomeAuthority(profile_authority)

    def forge(
        self,
        blueprint_id: str,
        profile: AgentProfile,
        descriptor: ExecutionStackDescriptor,
        pack: SpecializationPack,
        skill_genome: SkillGenome,
        *,
        repository_snapshot_digest: str,
        semantic_twin_fingerprint: str,
        certification_evidence_fingerprint: str,
    ) -> SpecialistBlueprint:
        if not self.stack_genome.verify_binding(profile, descriptor):
            raise PermissionError("ForgeSeal profile/StackGenome binding invalid")
        if not self.pack_authority.verify(pack):
            raise PermissionError("untrusted specialization pack")
        if pack.role is not profile.role or pack.base_capsule_fingerprint != profile.capsule_fingerprint:
            raise ValueError("specialization pack does not match profile role/capsule")
        if not pack.benchmark_dimensions:
            raise ValueError("specialization pack has no mastery dimensions")
        if not _SHA256.fullmatch(repository_snapshot_digest) or not _SHA256.fullmatch(semantic_twin_fingerprint):
            raise ValueError("invalid repository/twin binding")
        if not _SHA256.fullmatch(certification_evidence_fingerprint):
            raise ValueError("invalid certification evidence fingerprint")
        if self.certification_verifier(profile, certification_evidence_fingerprint, repository_snapshot_digest) is not True:
            raise PermissionError("specialist lacks trusted exact-repository certification")
        unsigned = SpecialistBlueprint(
            blueprint_id,
            profile.fingerprint(),
            descriptor.fingerprint(),
            repository_snapshot_digest,
            semantic_twin_fingerprint,
            pack.fingerprint(),
            skill_genome.fingerprint(),
            certification_evidence_fingerprint,
            "",
        )
        return replace(
            unsigned,
            forge_tag=hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest(),
        )

    def verify(self, blueprint: SpecialistBlueprint) -> bool:
        if not _SHA256.fullmatch(blueprint.forge_tag):
            return False
        unsigned = replace(blueprint, forge_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(blueprint.forge_tag, expected)


@dataclass(frozen=True)
class ArenaChallenge:
    challenge_id: str
    blueprint_fingerprint: str
    base_case_fingerprint: str
    base_lineage_root: str
    repository_snapshot_digest: str
    semantic_twin_fingerprint: str
    specialization_pack_fingerprint: str
    dimension: BenchmarkDimension
    suite_fingerprint: str
    diversity_family: str
    morph_kind: str
    prompt_digest: str
    hidden_nonce_digest: str
    challenge_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.challenge_id):
            raise ValueError("invalid arena challenge id")
        for digest in (
            self.blueprint_fingerprint,
            self.base_case_fingerprint,
            self.base_lineage_root,
            self.repository_snapshot_digest,
            self.semantic_twin_fingerprint,
            self.specialization_pack_fingerprint,
            self.suite_fingerprint,
            self.prompt_digest,
            self.hidden_nonce_digest,
        ):
            if not _SHA256.fullmatch(digest):
                raise ValueError("arena challenge digest must be sha256")
        for token in (self.diversity_family, self.morph_kind):
            if not _SAFE_TOKEN.fullmatch(token):
                raise ValueError("invalid arena challenge token")
        return _sha({
            "id": self.challenge_id,
            "blueprint": self.blueprint_fingerprint,
            "base_case": self.base_case_fingerprint,
            "lineage": self.base_lineage_root,
            "repository": self.repository_snapshot_digest,
            "twin": self.semantic_twin_fingerprint,
            "pack": self.specialization_pack_fingerprint,
            "dimension": self.dimension.value,
            "suite": self.suite_fingerprint,
            "family": self.diversity_family,
            "morph": self.morph_kind,
            "prompt": self.prompt_digest,
            "nonce": self.hidden_nonce_digest,
        })


class ChallengeMorph:
    """Creates host-sealed fresh challenge variants without exposing oracle material."""

    VERSION = "challenge-morph-v1"
    MORPHS = ("constraint-shift", "dependency-perturbation", "failure-inversion", "boundary-pressure")

    def __init__(
        self,
        key: bytes,
        case_verifier: Callable[[ShadowBenchCase], bool],
        suite_authority: SuiteLineageAuthority,
        forge: SpecialistForge,
    ) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("ChallengeMorph key must contain at least 32 bytes")
        if not callable(case_verifier):
            raise TypeError("ChallengeMorph requires trusted case verifier")
        self._key = bytes(key)
        self.case_verifier = case_verifier
        self.suite_authority = suite_authority
        self.forge = forge

    def create(
        self,
        blueprint: SpecialistBlueprint,
        pack: SpecializationPack,
        case: ShadowBenchCase,
        suite: EvaluationSuite,
        *,
        morph_index: int,
    ) -> ArenaChallenge:
        if not self.forge.verify(blueprint):
            raise PermissionError("untrusted specialist blueprint")
        if not self.suite_authority.verify(suite):
            raise PermissionError("untrusted arena suite")
        if self.case_verifier(case) is not True:
            raise PermissionError("untrusted ShadowBench source case")
        case.validate(); pack.validate_unsigned()
        if pack.fingerprint() != blueprint.specialization_pack_fingerprint:
            raise ValueError("challenge specialization pack mismatch")
        if case.repository_snapshot_digest != blueprint.repository_snapshot_digest:
            raise ValueError("challenge repository snapshot mismatch")
        if case.dimension not in pack.benchmark_dimensions:
            raise ValueError("challenge dimension outside specialization pack")
        if not isinstance(morph_index, int) or not 0 <= morph_index < len(self.MORPHS):
            raise ValueError("invalid ChallengeMorph index")
        morph = self.MORPHS[morph_index]
        base_case = case.semantic_fingerprint()
        nonce = hmac.new(
            self._key,
            f"nonce|{self.VERSION}|{blueprint.fingerprint()}|{base_case}|{suite.independence_root}|{morph}".encode(),
            hashlib.sha256,
        ).hexdigest()
        prompt_digest = _sha({
            "technology": self.VERSION,
            "blueprint": blueprint.fingerprint(),
            "case": base_case,
            "dimension": case.dimension.value,
            "morph": morph,
            "suite_lineage": suite.independence_root,
            "nonce": nonce,
        })
        challenge_seed = hmac.new(self._key, f"challenge|{prompt_digest}|{nonce}".encode(), hashlib.sha256).hexdigest()
        unsigned = ArenaChallenge(
            f"arena.{challenge_seed[:28]}",
            blueprint.fingerprint(),
            base_case,
            case.lineage_root,
            blueprint.repository_snapshot_digest,
            blueprint.semantic_twin_fingerprint,
            pack.fingerprint(),
            case.dimension,
            suite.fingerprint(),
            suite.diversity_family(),
            morph,
            prompt_digest,
            nonce,
            "",
        )
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, challenge_tag=tag)

    def verify(self, challenge: ArenaChallenge) -> bool:
        if not _SHA256.fullmatch(challenge.challenge_tag):
            return False
        unsigned = replace(challenge, challenge_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(challenge.challenge_tag, expected)


class AntiOverfitHorizon:
    """Rejects exact and lineage-equivalent challenge replay before arena scoring."""

    def __init__(self, challenge_verifier: Callable[[ArenaChallenge], bool]) -> None:
        if not callable(challenge_verifier):
            raise TypeError("Anti-Overfit Horizon requires trusted challenge verifier")
        self.challenge_verifier = challenge_verifier
        self._challenge_fingerprints: set[str] = set()
        self._base_lineages: set[tuple[str, str]] = set()
        self._prompt_digests: set[str] = set()

    def admit(self, challenge: ArenaChallenge) -> None:
        if self.challenge_verifier(challenge) is not True:
            raise PermissionError("unverified challenge cannot enter Anti-Overfit Horizon")
        fingerprint = challenge.fingerprint()
        lineage_key = (challenge.blueprint_fingerprint, challenge.base_lineage_root)
        if fingerprint in self._challenge_fingerprints:
            raise ValueError("arena challenge replay rejected")
        if lineage_key in self._base_lineages:
            raise ValueError("arena lineage replay rejected")
        if challenge.prompt_digest in self._prompt_digests:
            raise ValueError("arena prompt replay rejected")
        self._challenge_fingerprints.add(fingerprint)
        self._base_lineages.add(lineage_key)
        self._prompt_digests.add(challenge.prompt_digest)


@dataclass(frozen=True)
class ArenaTelemetry:
    latency_ms: int
    cost_microunits: int
    retries: int = 0
    tool_errors: int = 0

    def fingerprint(self) -> str:
        if not 0 <= self.latency_ms <= 86_400_000:
            raise ValueError("invalid arena latency")
        if not 0 <= self.cost_microunits <= 10**15:
            raise ValueError("invalid arena cost")
        if not 0 <= self.retries <= 100 or not 0 <= self.tool_errors <= 100:
            raise ValueError("invalid arena reliability telemetry")
        return _sha({
            "latency_ms": self.latency_ms,
            "cost_microunits": self.cost_microunits,
            "retries": self.retries,
            "tool_errors": self.tool_errors,
        })


@dataclass(frozen=True)
class ArenaEvidence:
    evidence_id: str
    blueprint_fingerprint: str
    challenge_fingerprint: str
    repository_snapshot_digest: str
    semantic_twin_fingerprint: str
    dimension: BenchmarkDimension
    diversity_family: str
    passed: bool
    critical_failure: bool
    policy_violation: bool
    tamper_event: bool
    telemetry: ArenaTelemetry
    grade_proof_digest: str
    evidence_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.evidence_id) or not _SAFE_TOKEN.fullmatch(self.diversity_family):
            raise ValueError("invalid arena evidence identity")
        for digest in (
            self.blueprint_fingerprint,
            self.challenge_fingerprint,
            self.repository_snapshot_digest,
            self.semantic_twin_fingerprint,
            self.grade_proof_digest,
        ):
            if not _SHA256.fullmatch(digest):
                raise ValueError("arena evidence digest must be sha256")
        return _sha({
            "id": self.evidence_id,
            "blueprint": self.blueprint_fingerprint,
            "challenge": self.challenge_fingerprint,
            "repository": self.repository_snapshot_digest,
            "twin": self.semantic_twin_fingerprint,
            "dimension": self.dimension.value,
            "family": self.diversity_family,
            "passed": self.passed,
            "critical": self.critical_failure,
            "policy": self.policy_violation,
            "tamper": self.tamper_event,
            "telemetry": self.telemetry.fingerprint(),
            "grade_proof": self.grade_proof_digest,
        })


class ArenaEvidenceAuthority:
    """Trusted host seals only verified blueprint/challenge/telemetry/grade evidence."""

    def __init__(
        self,
        key: bytes,
        blueprint_verifier: Callable[[SpecialistBlueprint], bool],
        challenge_verifier: Callable[[ArenaChallenge], bool],
        telemetry_verifier: Callable[[ArenaTelemetry], bool],
    ) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("arena evidence key must contain at least 32 bytes")
        if not all(callable(item) for item in (blueprint_verifier, challenge_verifier, telemetry_verifier)):
            raise TypeError("arena evidence requires trusted verifiers")
        self._key = bytes(key)
        self.blueprint_verifier = blueprint_verifier
        self.challenge_verifier = challenge_verifier
        self.telemetry_verifier = telemetry_verifier

    def issue(
        self,
        evidence_id: str,
        blueprint: SpecialistBlueprint,
        challenge: ArenaChallenge,
        *,
        passed: bool,
        critical_failure: bool,
        policy_violation: bool,
        tamper_event: bool,
        telemetry: ArenaTelemetry,
        grade_proof_digest: str,
    ) -> ArenaEvidence:
        if self.blueprint_verifier(blueprint) is not True:
            raise PermissionError("arena blueprint verification failed")
        if self.challenge_verifier(challenge) is not True:
            raise PermissionError("arena challenge verification failed")
        if self.telemetry_verifier(telemetry) is not True:
            raise PermissionError("arena telemetry verification failed")
        if challenge.blueprint_fingerprint != blueprint.fingerprint():
            raise ValueError("arena challenge/blueprint mismatch")
        if challenge.repository_snapshot_digest != blueprint.repository_snapshot_digest or challenge.semantic_twin_fingerprint != blueprint.semantic_twin_fingerprint:
            raise ValueError("arena evidence context mismatch")
        if not _SHA256.fullmatch(grade_proof_digest):
            raise ValueError("arena GradeProof digest required")
        unsigned = ArenaEvidence(
            evidence_id,
            blueprint.fingerprint(),
            challenge.fingerprint(),
            blueprint.repository_snapshot_digest,
            blueprint.semantic_twin_fingerprint,
            challenge.dimension,
            challenge.diversity_family,
            bool(passed),
            bool(critical_failure),
            bool(policy_violation),
            bool(tamper_event),
            telemetry,
            grade_proof_digest,
            "",
        )
        return replace(
            unsigned,
            evidence_tag=hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest(),
        )

    def verify(self, evidence: ArenaEvidence) -> bool:
        if not _SHA256.fullmatch(evidence.evidence_tag):
            return False
        unsigned = replace(evidence, evidence_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(evidence.evidence_tag, expected)


class RegressionKind(str, Enum):
    REGRESSION = "regression"
    ROLLBACK = "rollback"
    INCIDENT = "incident"


@dataclass(frozen=True)
class RegressionEvent:
    event_id: str
    blueprint_fingerprint: str
    kind: RegressionKind
    code: str
    severity: int
    event_tag: str = ""

    def fingerprint(self) -> str:
        if not _SAFE_ID.fullmatch(self.event_id) or not _SAFE_TOKEN.fullmatch(self.code):
            raise ValueError("invalid regression event")
        if not _SHA256.fullmatch(self.blueprint_fingerprint):
            raise ValueError("regression blueprint must be sha256")
        if not 1 <= self.severity <= 5:
            raise ValueError("invalid regression severity")
        return _sha({"id": self.event_id, "blueprint": self.blueprint_fingerprint, "kind": self.kind.value, "code": self.code, "severity": self.severity})


class RegressionAuthority:
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("regression authority key must contain at least 32 bytes")
        self._key = bytes(key)

    def seal(self, event: RegressionEvent) -> RegressionEvent:
        unsigned = replace(event, event_tag="")
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, event_tag=tag)

    def verify(self, event: RegressionEvent) -> bool:
        if not _SHA256.fullmatch(event.event_tag):
            return False
        unsigned = replace(event, event_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(event.event_tag, expected)


class ReliabilityShadow:
    """Negative-only memory. It can block/demote selection but never promote mastery."""

    def __init__(self, authority: RegressionAuthority) -> None:
        self.authority = authority
        self._events: dict[str, RegressionEvent] = {}

    def add(self, event: RegressionEvent) -> None:
        if not self.authority.verify(event):
            raise PermissionError("untrusted regression event")
        if event.event_id in self._events:
            raise ValueError("duplicate regression event")
        self._events[event.event_id] = event

    def blocked(self, blueprint: SpecialistBlueprint) -> bool:
        relevant = [event for event in self._events.values() if event.blueprint_fingerprint == blueprint.fingerprint()]
        return any(event.severity >= 4 for event in relevant) or sum(event.severity for event in relevant) >= 6


@dataclass(frozen=True)
class MasteryMetric:
    dimension: BenchmarkDimension
    samples: int
    successes: int
    quality_lower_bound: float
    reliability_lower_bound: float
    independent_families: int
    avg_latency_ms: float
    avg_cost_microunits: float
    critical_failures: int
    policy_violations: int
    tamper_events: int


class MasteryLattice:
    """Evidence-only multidimensional mastery map for ForgeSeal blueprints."""

    def __init__(self, authority: ArenaEvidenceAuthority) -> None:
        self.authority = authority
        self._evidence: dict[str, ArenaEvidence] = {}
        self._challenges: set[tuple[str, str]] = set()

    def add(self, evidence: ArenaEvidence) -> None:
        if not self.authority.verify(evidence):
            raise PermissionError("untrusted arena evidence")
        if evidence.evidence_id in self._evidence:
            raise ValueError("duplicate arena evidence")
        replay_key = (evidence.blueprint_fingerprint, evidence.challenge_fingerprint)
        if replay_key in self._challenges:
            raise ValueError("arena challenge evidence cannot be counted twice")
        self._evidence[evidence.evidence_id] = evidence
        self._challenges.add(replay_key)

    def metric(self, blueprint: SpecialistBlueprint, dimension: BenchmarkDimension) -> MasteryMetric:
        rows = [
            item for item in self._evidence.values()
            if item.blueprint_fingerprint == blueprint.fingerprint() and item.dimension is dimension
        ]
        samples = len(rows)
        successes = sum(1 for item in rows if item.passed)
        reliable_successes = sum(
            1 for item in rows
            if item.passed and item.telemetry.retries == 0 and item.telemetry.tool_errors == 0
        )
        quality = ExperienceLedger.wilson_lower_bound(successes, samples) if samples else 0.0
        reliability = ExperienceLedger.wilson_lower_bound(reliable_successes, samples) if samples else 0.0
        return MasteryMetric(
            dimension,
            samples,
            successes,
            round(quality, 6),
            round(reliability, 6),
            len({item.diversity_family for item in rows}),
            round(sum(item.telemetry.latency_ms for item in rows) / samples, 3) if samples else 0.0,
            round(sum(item.telemetry.cost_microunits for item in rows) / samples, 3) if samples else 0.0,
            sum(1 for item in rows if item.critical_failure),
            sum(1 for item in rows if item.policy_violation),
            sum(1 for item in rows if item.tamper_event),
        )


@dataclass(frozen=True)
class ArenaSelectionPolicy:
    min_trials_per_dimension: int = 20
    min_quality_lower_bound: float = 0.80
    min_reliability_lower_bound: float = 0.70
    min_independent_families: int = 2
    max_avg_latency_ms: float = 3_600_000.0
    max_avg_cost_microunits: float = 10**12

    def validate(self) -> None:
        if not 20 <= self.min_trials_per_dimension <= 100_000:
            raise ValueError("arena trial floor cannot be weakened")
        if not 0.80 <= self.min_quality_lower_bound <= 1.0:
            raise ValueError("arena quality floor cannot be weakened")
        if not 0.70 <= self.min_reliability_lower_bound <= 1.0:
            raise ValueError("arena reliability floor cannot be weakened")
        if not 2 <= self.min_independent_families <= 20:
            raise ValueError("arena diversity quorum cannot be weakened")
        if self.max_avg_latency_ms <= 0 or self.max_avg_cost_microunits <= 0:
            raise ValueError("arena telemetry ceilings must be positive")


@dataclass(frozen=True)
class CrownSelection:
    selected_blueprint_fingerprint: str
    frontier_blueprint_fingerprints: tuple[str, ...]
    selection_digest: str


class ParetoCrown:
    """Deterministic selector: safety/quality floors first, Pareto efficiency second."""

    def __init__(
        self,
        forge: SpecialistForge,
        lattice: MasteryLattice,
        reliability_shadow: ReliabilityShadow,
        certification_verifier: CertificationVerifier,
    ) -> None:
        self.forge = forge
        self.lattice = lattice
        self.reliability_shadow = reliability_shadow
        self.certification_verifier = certification_verifier

    def select(
        self,
        candidates: Iterable[tuple[SpecialistBlueprint, AgentProfile]],
        required_dimensions: frozenset[BenchmarkDimension],
        policy: ArenaSelectionPolicy = ArenaSelectionPolicy(),
    ) -> CrownSelection:
        policy.validate()
        if not required_dimensions:
            raise ValueError("Pareto Crown requires mastery dimensions")
        qualified: list[tuple[SpecialistBlueprint, float, float, float, float]] = []
        seen: set[str] = set()
        for blueprint, profile in candidates:
            if not self.forge.verify(blueprint):
                continue
            fingerprint = blueprint.fingerprint()
            if fingerprint in seen:
                raise ValueError("duplicate Pareto Crown candidate")
            seen.add(fingerprint)
            if profile.fingerprint() != blueprint.profile_fingerprint:
                continue
            if self.certification_verifier(profile, blueprint.certification_evidence_fingerprint, blueprint.repository_snapshot_digest) is not True:
                continue
            if self.reliability_shadow.blocked(blueprint):
                continue
            metrics = [self.lattice.metric(blueprint, dimension) for dimension in sorted(required_dimensions, key=lambda item: item.value)]
            if any(metric.samples < policy.min_trials_per_dimension for metric in metrics):
                continue
            if any(metric.quality_lower_bound < policy.min_quality_lower_bound for metric in metrics):
                continue
            if any(metric.reliability_lower_bound < policy.min_reliability_lower_bound for metric in metrics):
                continue
            if any(metric.independent_families < policy.min_independent_families for metric in metrics):
                continue
            if any(metric.critical_failures or metric.policy_violations or metric.tamper_events for metric in metrics):
                continue
            if any(metric.avg_latency_ms > policy.max_avg_latency_ms or metric.avg_cost_microunits > policy.max_avg_cost_microunits for metric in metrics):
                continue
            qualified.append((
                blueprint,
                min(metric.quality_lower_bound for metric in metrics),
                min(metric.reliability_lower_bound for metric in metrics),
                sum(metric.avg_cost_microunits for metric in metrics) / len(metrics),
                sum(metric.avg_latency_ms for metric in metrics) / len(metrics),
            ))
        if not qualified:
            raise LookupError("no certified specialist satisfies arena policy")

        def dominates(a: tuple[SpecialistBlueprint, float, float, float, float], b: tuple[SpecialistBlueprint, float, float, float, float]) -> bool:
            aq, ar, ac, al = a[1:]
            bq, br, bc, bl = b[1:]
            weak = aq >= bq and ar >= br and ac <= bc and al <= bl
            strict = aq > bq or ar > br or ac < bc or al < bl
            return weak and strict

        frontier = [item for item in qualified if not any(dominates(other, item) for other in qualified if other is not item)]
        frontier.sort(key=lambda item: (-item[1], -item[2], item[3], item[4], item[0].blueprint_id))
        selected = frontier[0][0]
        frontier_fps = tuple(item[0].fingerprint() for item in frontier)
        digest = _sha({
            "technology": "pareto-crown-v1",
            "selected": selected.fingerprint(),
            "frontier": list(frontier_fps),
            "dimensions": sorted(item.value for item in required_dimensions),
            "policy": {
                "trials": policy.min_trials_per_dimension,
                "quality": policy.min_quality_lower_bound,
                "reliability": policy.min_reliability_lower_bound,
                "families": policy.min_independent_families,
                "latency": policy.max_avg_latency_ms,
                "cost": policy.max_avg_cost_microunits,
            },
        })
        return CrownSelection(selected.fingerprint(), frontier_fps, digest)
