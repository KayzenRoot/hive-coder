from __future__ import annotations

import unittest
from dataclasses import replace

from hive_runtime.certification_contracts import EvaluationSuite, ExecutionStackDescriptor, SuiteLineageAuthority
from hive_runtime.evaluation_runtime import ShadowBenchCase
from hive_runtime.expert_common import BenchmarkDimension, _sha
from hive_runtime.expert_identity import AgentProfile, AgentProfileAuthority
from hive_runtime.orchestration import AgentRole
from hive_runtime.specialist_forge import (
    AntiOverfitHorizon,
    ArenaEvidenceAuthority,
    ArenaSelectionPolicy,
    ArenaTelemetry,
    ChallengeMorph,
    MasteryLattice,
    ParetoCrown,
    RegressionAuthority,
    RegressionEvent,
    RegressionKind,
    ReliabilityShadow,
    SkillGenome,
    SpecializationPack,
    SpecializationPackAuthority,
    SpecialistForge,
)


D = lambda text: _sha({"v": text})
REPO = D("repo")
TWIN = D("twin")
CERT = D("cert")
CAPSULE = D("capsule")
GRADE = D("grade")


class ForgeFixture:
    def __init__(self) -> None:
        self.profile_authority = AgentProfileAuthority(b"p" * 32)
        self.pack_authority = SpecializationPackAuthority(b"s" * 32)
        self.suite_authority = SuiteLineageAuthority(b"u" * 32)
        self.certifier = lambda profile, evidence, repository: evidence == CERT and repository == REPO
        self.forge = SpecialistForge(b"f" * 32, self.profile_authority, self.pack_authority, self.certifier)
        self.skill_genome = SkillGenome(("python-debugger",), (D("skill"),))
        self.pack = self.pack_authority.seal(SpecializationPack(
            "python.backend", "v1", AgentRole.BACKEND, "python", "fastapi",
            ("api", "services"), frozenset({BenchmarkDimension.DEBUGGING}),
            CAPSULE, D("doctrine"), D("provenance"),
        ))
        self.descriptor = ExecutionStackDescriptor(
            "mock-provider", "mock-model", D("model"), D("tools"), CAPSULE,
            self.skill_genome.fingerprint(), D("runtime"),
        )
        self.profile = self.profile_authority.seal(AgentProfile(
            "backend.python.1", AgentRole.BACKEND, CAPSULE, frozenset(), 8192,
            "lineage.backend.1", self.descriptor.fingerprint(),
        ))
        self.blueprint = self.forge.forge(
            "forge.python.backend.1", self.profile, self.descriptor, self.pack, self.skill_genome,
            repository_snapshot_digest=REPO, semantic_twin_fingerprint=TWIN,
            certification_evidence_fingerprint=CERT,
        )
        self.suite_a = self.suite_authority.seal(EvaluationSuite(
            "arena-a", "v1", "family-a", "independent-a", "morph", "v1", D("protocol-a")
        ))
        self.suite_b = self.suite_authority.seal(EvaluationSuite(
            "arena-b", "v1", "family-b", "independent-b", "morph", "v1", D("protocol-b")
        ))
        self.valid_case_ids: set[str] = set()
        self.morph = ChallengeMorph(
            b"m" * 32, lambda case: case.case_id in self.valid_case_ids,
            self.suite_authority, self.forge,
        )
        self.evidence_authority = ArenaEvidenceAuthority(
            b"e" * 32, self.forge.verify, self.morph.verify,
            lambda telemetry: telemetry.latency_ms >= 0 and telemetry.cost_microunits >= 0,
        )

    def case(self, i: int) -> ShadowBenchCase:
        root = D(f"root-{i}")
        case = ShadowBenchCase(
            f"case.{i}", f"lineage.{i}", root, "shadowbench-v1", "epoch-1", REPO,
            BenchmarkDimension.DEBUGGING, "fault-localization", (f"fact.{i}",),
            D(f"prompt-{i}"), D(f"oracle-{i}"), D(f"nonce-{i}"),
        )
        self.valid_case_ids.add(case.case_id)
        return case

    def challenge(self, i: int, blueprint=None):
        blueprint = blueprint or self.blueprint
        suite = self.suite_a if i % 2 == 0 else self.suite_b
        return self.morph.create(blueprint, self.pack, self.case(i), suite, morph_index=i % 4)


class SpecialistForgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = ForgeFixture()

    def test_forgeseal_binds_exact_profile_stack_repository_pack_and_certification(self):
        self.assertTrue(self.fx.forge.verify(self.fx.blueprint))
        self.assertEqual(self.fx.blueprint.repository_snapshot_digest, REPO)
        self.assertEqual(self.fx.blueprint.semantic_twin_fingerprint, TWIN)
        tampered = replace(self.fx.blueprint, repository_snapshot_digest=D("other"))
        self.assertFalse(self.fx.forge.verify(tampered))

    def test_forge_rejects_untrusted_pack_and_wrong_certification(self):
        raw = replace(self.fx.pack, authority_tag="")
        with self.assertRaises(PermissionError):
            self.fx.forge.forge(
                "bad.pack", self.fx.profile, self.fx.descriptor, raw, self.fx.skill_genome,
                repository_snapshot_digest=REPO, semantic_twin_fingerprint=TWIN,
                certification_evidence_fingerprint=CERT,
            )
        with self.assertRaises(PermissionError):
            self.fx.forge.forge(
                "bad.cert", self.fx.profile, self.fx.descriptor, self.fx.pack, self.fx.skill_genome,
                repository_snapshot_digest=REPO, semantic_twin_fingerprint=TWIN,
                certification_evidence_fingerprint=D("fake-cert"),
            )

    def test_skill_genome_must_match_stack_genome_skillset(self):
        other = SkillGenome(("other-skill",), (D("other-skill"),))
        with self.assertRaises(ValueError):
            self.fx.forge.forge(
                "bad.skills", self.fx.profile, self.fx.descriptor, self.fx.pack, other,
                repository_snapshot_digest=REPO, semantic_twin_fingerprint=TWIN,
                certification_evidence_fingerprint=CERT,
            )

    def test_challenge_morph_is_host_sealed_and_context_bound(self):
        challenge = self.fx.challenge(1)
        self.assertTrue(self.fx.morph.verify(challenge))
        self.assertEqual(challenge.blueprint_fingerprint, self.fx.blueprint.fingerprint())
        self.assertFalse(self.fx.morph.verify(replace(challenge, morph_kind="constraint-shift" if challenge.morph_kind != "constraint-shift" else "failure-inversion")))

    def test_anti_overfit_horizon_rejects_exact_and_lineage_replay(self):
        horizon = AntiOverfitHorizon(self.fx.morph.verify)
        challenge = self.fx.challenge(2)
        horizon.admit(challenge)
        with self.assertRaises(ValueError):
            horizon.admit(challenge)
        # A different morph over the same source lineage is still not fresh mastery evidence.
        suite = self.fx.suite_a
        same_case = self.fx.case(2)
        variant = self.fx.morph.create(self.fx.blueprint, self.fx.pack, same_case, suite, morph_index=3)
        with self.assertRaises(ValueError):
            horizon.admit(variant)

    def test_evidence_seal_covers_telemetry_grade_and_outcome(self):
        challenge = self.fx.challenge(3)
        telemetry = ArenaTelemetry(1200, 5000)
        evidence = self.fx.evidence_authority.issue(
            "ev.3", self.fx.blueprint, challenge, passed=True, critical_failure=False,
            policy_violation=False, tamper_event=False, telemetry=telemetry,
            grade_proof_digest=GRADE,
        )
        self.assertTrue(self.fx.evidence_authority.verify(evidence))
        self.assertFalse(self.fx.evidence_authority.verify(replace(evidence, telemetry=ArenaTelemetry(1, 1))))

    def test_mastery_lattice_rejects_duplicate_challenge_evidence(self):
        lattice = MasteryLattice(self.fx.evidence_authority)
        challenge = self.fx.challenge(4)
        one = self.fx.evidence_authority.issue(
            "ev.one", self.fx.blueprint, challenge, passed=True, critical_failure=False,
            policy_violation=False, tamper_event=False, telemetry=ArenaTelemetry(10, 10), grade_proof_digest=GRADE,
        )
        two = self.fx.evidence_authority.issue(
            "ev.two", self.fx.blueprint, challenge, passed=True, critical_failure=False,
            policy_violation=False, tamper_event=False, telemetry=ArenaTelemetry(10, 10), grade_proof_digest=GRADE,
        )
        lattice.add(one)
        with self.assertRaises(ValueError):
            lattice.add(two)

    def test_policy_floors_cannot_be_weakened(self):
        with self.assertRaises(ValueError):
            ArenaSelectionPolicy(min_trials_per_dimension=19).validate()
        with self.assertRaises(ValueError):
            ArenaSelectionPolicy(min_quality_lower_bound=0.79).validate()
        with self.assertRaises(ValueError):
            ArenaSelectionPolicy(min_reliability_lower_bound=0.69).validate()
        with self.assertRaises(ValueError):
            ArenaSelectionPolicy(min_independent_families=1).validate()

    def _populate(self, lattice: MasteryLattice, blueprint, start: int, *, latency: int, cost: int, passed: bool = True, retries: int = 0):
        for offset in range(40):
            i = start + offset
            challenge = self.fx.challenge(i, blueprint=blueprint)
            evidence = self.fx.evidence_authority.issue(
                f"ev.{blueprint.blueprint_id}.{i}", blueprint, challenge,
                passed=passed, critical_failure=False, policy_violation=False, tamper_event=False,
                telemetry=ArenaTelemetry(latency, cost, retries=retries), grade_proof_digest=GRADE,
            )
            lattice.add(evidence)

    def test_pareto_crown_prefers_quality_then_reliability_before_cost(self):
        lattice = MasteryLattice(self.fx.evidence_authority)
        shadow = ReliabilityShadow(RegressionAuthority(b"r" * 32))
        # Same certified exact stack, different ForgeSeal identity. The second is cheaper but unreliable.
        better = self.fx.blueprint
        cheaper = self.fx.forge.forge(
            "forge.python.backend.cheap", self.fx.profile, self.fx.descriptor, self.fx.pack, self.fx.skill_genome,
            repository_snapshot_digest=REPO, semantic_twin_fingerprint=TWIN,
            certification_evidence_fingerprint=CERT,
        )
        self._populate(lattice, better, 100, latency=200, cost=1000)
        self._populate(lattice, cheaper, 200, latency=50, cost=10, retries=1)
        crown = ParetoCrown(self.fx.forge, lattice, shadow, self.fx.certifier)
        selection = crown.select(
            ((cheaper, self.fx.profile), (better, self.fx.profile)),
            frozenset({BenchmarkDimension.DEBUGGING}),
        )
        self.assertEqual(selection.selected_blueprint_fingerprint, better.fingerprint())

    def test_regression_memory_is_negative_only_and_can_block_selection(self):
        lattice = MasteryLattice(self.fx.evidence_authority)
        reg_auth = RegressionAuthority(b"r" * 32)
        shadow = ReliabilityShadow(reg_auth)
        self._populate(lattice, self.fx.blueprint, 300, latency=100, cost=100)
        shadow.add(reg_auth.seal(RegressionEvent(
            "reg.1", self.fx.blueprint.fingerprint(), RegressionKind.REGRESSION, "prod-regression", 4
        )))
        crown = ParetoCrown(self.fx.forge, lattice, shadow, self.fx.certifier)
        with self.assertRaises(LookupError):
            crown.select(((self.fx.blueprint, self.fx.profile),), frozenset({BenchmarkDimension.DEBUGGING}))

    def test_tamper_or_policy_incident_blocks_even_when_fast_and_cheap(self):
        lattice = MasteryLattice(self.fx.evidence_authority)
        for i in range(400, 440):
            challenge = self.fx.challenge(i)
            evidence = self.fx.evidence_authority.issue(
                f"ev.bad.{i}", self.fx.blueprint, challenge, passed=True,
                critical_failure=False, policy_violation=(i == 439), tamper_event=False,
                telemetry=ArenaTelemetry(1, 1), grade_proof_digest=GRADE,
            )
            lattice.add(evidence)
        crown = ParetoCrown(
            self.fx.forge, lattice, ReliabilityShadow(RegressionAuthority(b"r" * 32)), self.fx.certifier
        )
        with self.assertRaises(LookupError):
            crown.select(((self.fx.blueprint, self.fx.profile),), frozenset({BenchmarkDimension.DEBUGGING}))

    def test_selector_revalidates_certification_at_selection_time(self):
        lattice = MasteryLattice(self.fx.evidence_authority)
        self._populate(lattice, self.fx.blueprint, 500, latency=100, cost=100)
        revoked = ParetoCrown(
            self.fx.forge, lattice, ReliabilityShadow(RegressionAuthority(b"r" * 32)),
            lambda profile, evidence, repository: False,
        )
        with self.assertRaises(LookupError):
            revoked.select(((self.fx.blueprint, self.fx.profile),), frozenset({BenchmarkDimension.DEBUGGING}))


if __name__ == "__main__":
    unittest.main()
