from __future__ import annotations

import unittest
from dataclasses import replace

from hive_runtime.evaluation_runtime import (
    BenchmarkNoveltyLedger,
    CertificationAuthority,
    ChronoSealClock,
    CompetenceHalfLifePolicy,
    CounterfactualForge,
    OutcomeAuthority,
    OutcomeEchoLedger,
    RecertificationClock,
    RecertificationStatus,
    ShadowBenchFactory,
)
from hive_runtime.expert_common import BenchmarkDimension, CompetenceLevel
from hive_runtime.expert_context import ArchitecturalGenome, ArchitecturalInvariant, CodeTruthMap, TruthFact
from hive_runtime.expert_evaluation import ExperienceRouter
from hive_runtime.orchestration import AgentRole, DigitalTwinNode, ProjectDigitalTwin
from hive_runtime.repository_intelligence import GenomePulseResult, RepositoryFileRecord, RepositorySnapshot
from tests.runtime.expert_agent_fixture import ExpertAgentFixture, sha


def snapshot() -> RepositorySnapshot:
    return RepositorySnapshot(
        "demo",
        (
            RepositoryFileRecord("src/api.py", sha("api"), 3, "python", "source"),
            RepositoryFileRecord("tests/test_api.py", sha("test"), 4, "python", "test"),
        ),
    )


def truth() -> CodeTruthMap:
    facts = (
        TruthFact("fact.api", "src/api.py", "file_content", sha("api"), sha("prov-api"), frozenset({"repository"})),
        TruthFact("fact.test", "tests/test_api.py", "file_content", sha("test"), sha("prov-test"), frozenset({"repository"})),
    )
    return CodeTruthMap(facts, lambda _fact: True)


class ShadowBenchTests(unittest.TestCase):
    def setUp(self):
        self.factory = ShadowBenchFactory(b"shadowbench-host-key-at-least-32-bytes!!")
        self.snapshot = snapshot()
        self.truth = truth()

    def test_same_host_inputs_are_deterministic_and_oracle_is_digest_only(self):
        first = self.factory.generate(
            self.snapshot, self.truth, BenchmarkDimension.DEBUGGING,
            epoch_label="epoch-001", count=2,
        )
        second = self.factory.generate(
            self.snapshot, self.truth, BenchmarkDimension.DEBUGGING,
            epoch_label="epoch-001", count=2,
        )
        self.assertEqual(first, second)
        self.assertTrue(all(self.factory.verify_case(case, self.truth) for case in first))
        self.assertTrue(all(len(case.oracle_digest) == 64 for case in first))
        self.assertFalse(any(hasattr(case, "oracle_text") for case in first))

    def test_tampered_hidden_case_or_identity_fails_verification(self):
        case = self.factory.generate(
            self.snapshot, self.truth, BenchmarkDimension.SECURITY,
            epoch_label="epoch-001",
        )[0]
        mutation = "authority-confusion" if case.mutation_kind != "authority-confusion" else "trust-boundary"
        self.assertFalse(self.factory.verify_case(replace(case, mutation_kind=mutation), self.truth))
        self.assertFalse(self.factory.verify_case(replace(case, case_id="shadow." + "a" * 28), self.truth))
        self.assertFalse(self.factory.verify_case(replace(case, hidden_nonce_digest="b" * 64), self.truth))

    def test_novelty_ledger_rejects_epoch_replay_and_trivial_lineage_variation(self):
        ledger = BenchmarkNoveltyLedger()
        first = self.factory.generate(
            self.snapshot, self.truth, BenchmarkDimension.CODE_REVIEW,
            epoch_label="epoch-001",
        )[0]
        later = self.factory.generate(
            self.snapshot, self.truth, BenchmarkDimension.CODE_REVIEW,
            epoch_label="epoch-002",
        )[0]
        self.assertEqual(first.lineage_root, later.lineage_root)
        ledger.add(first)
        with self.assertRaises(ValueError):
            ledger.add(later)
        forged_id = replace(first, case_id="shadow." + "a" * 28)
        with self.assertRaises(ValueError):
            ledger.add(forged_id)

    def test_different_source_lineages_can_coexist(self):
        cases = self.factory.generate(
            self.snapshot, self.truth, BenchmarkDimension.REPOSITORY_REASONING,
            epoch_label="epoch-001", count=2,
        )
        ledger = BenchmarkNoveltyLedger()
        for case in cases:
            ledger.add(case)
        self.assertEqual(len(ledger), 2)


class CounterfactualForgeTests(unittest.TestCase):
    def test_probe_is_bound_to_mined_fact_invariant_relationship(self):
        current_truth = truth()
        twin = ProjectDigitalTwin((DigitalTwinNode("api", "service"),))
        invariant = ArchitecturalInvariant(
            "genome.api", sha("statement"), frozenset({"api"}), frozenset({"fact.api"}), True,
        )
        genome = ArchitecturalGenome(twin, current_truth, (invariant,))
        pulse = GenomePulseResult(genome, {"fact.api": ("genome.api",)}, ("api",))
        probe = CounterfactualForge().create(
            pulse,
            repository_snapshot_digest=snapshot().fingerprint(),
            fact_id="fact.api",
            replacement_object_digest=sha("changed-api"),
        )
        self.assertEqual(probe.expected_drift_invariants, ("genome.api",))
        with self.assertRaises(ValueError):
            CounterfactualForge().create(
                pulse,
                repository_snapshot_digest=snapshot().fingerprint(),
                fact_id="fact.test",
                replacement_object_digest=sha("changed-test"),
            )


class ChronoSealTests(unittest.TestCase):
    def test_logical_time_is_monotonic(self):
        clock = ChronoSealClock(10)
        self.assertEqual(clock.advance(11), 11)
        self.assertEqual(clock.advance(11), 11)
        with self.assertRaises(ValueError):
            clock.advance(10)


class RecertificationTests(ExpertAgentFixture):
    def setUp(self):
        super().setUp()
        self.clock = ChronoSealClock(100)
        self.cert_authority = CertificationAuthority(
            b"certification-authority-key-at-least-32-bytes!",
            self.clock,
            self.profile_authority,
        )

    def passing_report(self, profile):
        ledger = self.ledger()
        self.add_results(ledger, profile)
        return ExperienceRouter(self.profile_authority, ledger).evaluate(
            profile, self.by_role[profile.role], self.standard(profile.role),
        )

    def evidence(self, profile, *, snapshot_digest=None):
        standard = self.standard(profile.role)
        report = self.passing_report(profile)
        self.assertTrue(report.passed)
        return self.cert_authority.issue(
            "cert.one", profile, standard, report,
            repository_snapshot_digest=snapshot_digest or snapshot().fingerprint(),
        )

    def test_certification_authority_derives_families_from_measured_report(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        evidence = self.evidence(profile)
        self.assertEqual(evidence.benchmark_families, ("hive-fresh", "terminal-lab"))
        self.assertTrue(self.cert_authority.verify(evidence))

    def test_forged_or_tampered_certification_evidence_is_rejected(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        evidence = self.evidence(profile)
        forged = replace(evidence, observed_epoch=99)
        with self.assertRaises(PermissionError):
            RecertificationClock(self.cert_authority).assess(
                profile, self.standard(AgentRole.BACKEND),
                repository_snapshot_digest=snapshot().fingerprint(),
                evidence=(forged,),
            )

    def test_competence_half_life_moves_current_to_due_to_expired(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        standard = self.standard(AgentRole.BACKEND)
        evidence = self.evidence(profile)
        clock = RecertificationClock(
            self.cert_authority,
            CompetenceHalfLifePolicy(warning_age_epochs=30, max_age_epochs=90),
        )
        self.clock.advance(110)
        current = clock.assess(
            profile, standard, repository_snapshot_digest=snapshot().fingerprint(),
            evidence=(evidence,),
        )
        self.clock.advance(140)
        due = clock.assess(
            profile, standard, repository_snapshot_digest=snapshot().fingerprint(),
            evidence=(evidence,),
        )
        self.clock.advance(191)
        expired = clock.assess(
            profile, standard, repository_snapshot_digest=snapshot().fingerprint(),
            evidence=(evidence,),
        )
        self.assertIs(current.status, RecertificationStatus.CURRENT)
        self.assertIs(due.status, RecertificationStatus.DUE)
        self.assertIn("competence_half_life_warning", due.blocking_codes)
        self.assertIs(expired.status, RecertificationStatus.EXPIRED)

    def test_repository_snapshot_change_expires_previous_certification(self):
        profile = self.profile(AgentRole.SECURITY, "security-a")
        evidence = self.evidence(profile, snapshot_digest=sha("old-snapshot"))
        report = RecertificationClock(self.cert_authority).assess(
            profile, self.standard(AgentRole.SECURITY),
            repository_snapshot_digest=sha("new-snapshot"), evidence=(evidence,),
        )
        self.assertIs(report.status, RecertificationStatus.EXPIRED)
        self.assertIn("repository_snapshot_changed", report.blocking_codes)

    def test_execution_stack_change_cannot_reuse_old_certification(self):
        old = self.profile(AgentRole.BACKEND, "backend-a", stack="stack-v1")
        new = self.profile(AgentRole.BACKEND, "backend-a", stack="stack-v2")
        evidence = self.evidence(old)
        report = RecertificationClock(self.cert_authority).assess(
            new, self.standard(AgentRole.BACKEND),
            repository_snapshot_digest=snapshot().fingerprint(), evidence=(evidence,),
        )
        self.assertIs(report.status, RecertificationStatus.EXPIRED)

    def test_non_distinguished_standard_cannot_be_used_for_production_recertification(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        standard = replace(
            self.standard(AgentRole.BACKEND),
            level=CompetenceLevel.QUALIFIED,
            min_samples_per_dimension=10,
            min_lower_bound=0.50,
            min_independent_suites=1,
        )
        with self.assertRaises(ValueError):
            RecertificationClock(self.cert_authority).assess(
                profile, standard,
                repository_snapshot_digest=snapshot().fingerprint(), evidence=(),
            )

    def test_negative_outcome_can_force_due_but_positive_outcome_cannot_create_certification(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        evidence = self.evidence(profile)
        outcome_authority = OutcomeAuthority(
            b"outcome-authority-key-at-least-32-bytes!", self.clock,
        )
        ledger = OutcomeEchoLedger(outcome_authority)
        self.clock.advance(105)
        record = outcome_authority.issue(
            "outcome.one",
            profile_fingerprint=profile.fingerprint(),
            master_plan_fingerprint=sha("plan"),
            repository_snapshot_digest=snapshot().fingerprint(),
            success=True,
            regressions=1,
            rollbacks=0,
            evidence_digest=sha("evidence"),
        )
        ledger.add(record)
        self.clock.advance(110)
        signal = ledger.signal(profile.fingerprint())
        due = RecertificationClock(self.cert_authority).assess(
            profile, self.standard(AgentRole.BACKEND),
            repository_snapshot_digest=snapshot().fingerprint(),
            evidence=(evidence,), outcome=signal,
        )
        self.assertIs(due.status, RecertificationStatus.DUE)
        self.assertTrue(signal.advisory_only)

        no_evidence = RecertificationClock(self.cert_authority).assess(
            profile, self.standard(AgentRole.BACKEND),
            repository_snapshot_digest=snapshot().fingerprint(),
            evidence=(), outcome=signal,
        )
        self.assertIs(no_evidence.status, RecertificationStatus.EXPIRED)

    def test_outcome_tamper_is_rejected(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        authority = OutcomeAuthority(
            b"outcome-authority-key-at-least-32-bytes!", self.clock,
        )
        ledger = OutcomeEchoLedger(authority)
        record = authority.issue(
            "outcome.one",
            profile_fingerprint=profile.fingerprint(),
            master_plan_fingerprint=sha("plan"),
            repository_snapshot_digest=snapshot().fingerprint(),
            success=True,
            regressions=0,
            rollbacks=0,
            evidence_digest=sha("evidence"),
        )
        with self.assertRaises(PermissionError):
            ledger.add(replace(record, regressions=1))


if __name__ == "__main__":
    unittest.main()
