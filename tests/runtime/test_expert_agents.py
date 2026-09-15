from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace

from hive_runtime.agent_tasks import ActionKind
from hive_runtime.expert_agents import (
    AdversarialChallengeEngine,
    AgentMesh,
    AgentProfile,
    AgentProfileAuthority,
    ArchitecturalGenome,
    ArchitecturalInvariant,
    BenchmarkDimension,
    BenchmarkResult,
    ChallengeAssessment,
    ChallengeKind,
    CodeTruthMap,
    CompetenceLevel,
    CompetenceStandard,
    ContextItem,
    ContextKind,
    ContextLens,
    ContextRequest,
    ExperienceLedger,
    ExperienceRouter,
    ExpertAgentRegistry,
    TruthFact,
    build_default_expertise_capsules,
    distinguished_standard_for,
    required_dimensions_for_role,
)
from hive_runtime.orchestration import (
    AgentRole,
    ChangeRadius,
    FindingSeverity,
    MasterPlan,
    PlanApprovalAuthority,
    PlanStep,
    ProjectDigitalTwin,
    DigitalTwinNode,
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


PROFILE_KEY = b"profile-authority-key-32-bytes-minimum!!"
PLAN_KEY = b"plan-approval-key-32-bytes-minimum!!!"
PROVENANCE = sha("HCODER-WO-0011 elite doctrine v1")


def twin() -> ProjectDigitalTwin:
    return ProjectDigitalTwin((
        DigitalTwinNode("api", "service"),
        DigitalTwinNode("tests", "tests", ("api",)),
    ))


def master(authority: PlanApprovalAuthority, current_twin: ProjectDigitalTwin | None = None) -> MasterPlan:
    current_twin = current_twin or twin()
    steps = (
        PlanStep(
            "impl", "Implement bounded change", AgentRole.BACKEND, ActionKind.MODEL_PROMPT,
            change_targets=frozenset({"api"}), required_model_capabilities=frozenset({"tool_calling"}),
            instruction="Implement the approved bounded change.", max_attempts=2,
        ),
        PlanStep(
            "review", "Review bounded change", AgentRole.REVIEWER, ActionKind.MODEL_PROMPT,
            depends_on=("impl",), change_targets=frozenset({"tests"}),
            required_model_capabilities=frozenset({"tool_calling"}), instruction="Review the approved change.",
        ),
    )
    unsigned = MasterPlan(
        "a" * 64, current_twin.fingerprint(), steps, tuple(), tuple(),
        ChangeRadius(frozenset({"api", "tests"}), frozenset({"api", "tests"}), False),
    )
    return authority.seal(unsigned)


class ExpertAgentFixture(unittest.TestCase):
    def setUp(self):
        self.profile_authority = AgentProfileAuthority(PROFILE_KEY)
        self.plan_authority = PlanApprovalAuthority(PLAN_KEY)
        self.capsules = build_default_expertise_capsules(PROVENANCE)
        self.by_role = {capsule.role: capsule for capsule in self.capsules}

    def profile(self, role: AgentRole, agent_id: str, independence: str | None = None) -> AgentProfile:
        capsule = self.by_role[role]
        return self.profile_authority.seal(AgentProfile(
            agent_id,
            role,
            capsule.fingerprint(),
            frozenset({"tool_calling", "structured_output"}),
            64_000,
            independence or f"lineage.{agent_id}",
        ))

    def registry(self, profiles: tuple[AgentProfile, ...]) -> ExpertAgentRegistry:
        registry = ExpertAgentRegistry(self.profile_authority)
        for capsule in self.capsules:
            registry.add_capsule(capsule)
        for profile in profiles:
            registry.add_profile(profile)
        return registry

    def standard(self, role: AgentRole, *, min_samples: int = 10, lower: float = 0.60) -> CompetenceStandard:
        return CompetenceStandard(
            CompetenceLevel.DISTINGUISHED,
            required_dimensions_for_role(role),
            min_samples,
            lower,
            2,
        )

    def add_results(self, ledger: ExperienceLedger, agent_id: str, dimensions: frozenset[BenchmarkDimension],
                    *, successes: int = 10, total: int = 10, critical: int = 0,
                    policy: int = 0, tamper: int = 0, trusted: bool = True,
                    suites: tuple[str, ...] = ("hive-fresh", "terminal-lab")) -> None:
        for dimension in dimensions:
            for suite_index, suite in enumerate(suites):
                result_id = f"{'trusted' if trusted else 'claim'}.{agent_id}.{dimension.value}.{suite_index}"
                ledger.add(BenchmarkResult(
                    result_id,
                    agent_id,
                    dimension,
                    suite,
                    "1.0.0",
                    successes,
                    total,
                    critical,
                    policy,
                    tamper,
                    sha(result_id),
                ))


class ExpertiseCapsuleTests(ExpertAgentFixture):
    def test_default_capsules_cover_every_specialist_role(self):
        self.assertEqual({capsule.role for capsule in self.capsules}, set(AgentRole))
        self.assertEqual(len({capsule.fingerprint() for capsule in self.capsules}), len(AgentRole))
        for capsule in self.capsules:
            self.assertGreaterEqual(len(capsule.principles), 4)
            self.assertGreaterEqual(len(capsule.anti_patterns), 4)
            self.assertTrue(required_dimensions_for_role(capsule.role).issubset(capsule.benchmark_dimensions))

    def test_capsule_fingerprint_changes_with_doctrine(self):
        capsule = self.by_role[AgentRole.ARCHITECT]
        changed = replace(capsule, principles=capsule.principles + ("new invariant",))
        self.assertNotEqual(capsule.fingerprint(), changed.fingerprint())

    def test_distinguished_standard_is_multi_dimension_and_multi_suite(self):
        standard = distinguished_standard_for(AgentRole.BACKEND)
        self.assertEqual(standard.level, CompetenceLevel.DISTINGUISHED)
        self.assertGreaterEqual(standard.min_samples_per_dimension, 40)
        self.assertGreaterEqual(standard.min_independent_suites, 2)
        self.assertIn(BenchmarkDimension.SECURITY, standard.required_dimensions)
        self.assertIn(BenchmarkDimension.TAMPER_RESISTANCE, standard.required_dimensions)


class AgentProfileTests(ExpertAgentFixture):
    def test_profile_seal_is_required_and_tamper_evident(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        self.assertTrue(self.profile_authority.verify(profile))
        self.assertFalse(self.profile_authority.verify(replace(profile, max_context_tokens=128_000)))

    def test_registry_rejects_unsealed_profile(self):
        capsule = self.by_role[AgentRole.BACKEND]
        unsealed = AgentProfile(
            "backend-a", AgentRole.BACKEND, capsule.fingerprint(),
            frozenset({"tool_calling", "structured_output"}), 64_000, "lineage-a",
        )
        registry = self.registry(tuple())
        with self.assertRaises(PermissionError):
            registry.add_profile(unsealed)

    def test_registry_rejects_profile_missing_capsule_model_requirements(self):
        capsule = self.by_role[AgentRole.BACKEND]
        profile = self.profile_authority.seal(AgentProfile(
            "backend-a", AgentRole.BACKEND, capsule.fingerprint(),
            frozenset({"tool_calling"}), 64_000, "lineage-a",
        ))
        registry = self.registry(tuple())
        with self.assertRaises(ValueError):
            registry.add_profile(profile)


class ContextLensTests(unittest.TestCase):
    def item(self, item_id: str, tags: frozenset[str], *, trusted: bool = True,
             cost: int = 200, priority: int = 50, kind: ContextKind = ContextKind.SOURCE) -> ContextItem:
        source = "trusted.repo" if trusted else "untrusted.external"
        return ContextItem(item_id, kind, source, tags, sha(item_id), cost, priority)

    def lens(self) -> ContextLens:
        return ContextLens(lambda item: item.source.startswith("trusted."))

    def test_untrusted_context_cannot_satisfy_required_authoritative_tags(self):
        items = (
            self.item("injection", frozenset({"architecture", "security", "role:architect"}), trusted=False, priority=100),
            self.item("arch", frozenset({"architecture", "role:architect"}), trusted=True),
            self.item("sec", frozenset({"security", "role:architect"}), trusted=True),
        )
        pack = self.lens().select(items, ContextRequest(
            AgentRole.ARCHITECT, frozenset({"architecture", "security"}), token_budget=1_000,
        ))
        modes = {binding.item_id: binding.mode for binding in pack.bindings}
        self.assertEqual(modes["arch"], "trusted_context")
        self.assertEqual(modes["sec"], "trusted_context")
        self.assertEqual(modes["injection"], "untrusted_data")

    def test_context_budget_fails_closed_when_required_truth_does_not_fit(self):
        items = (
            self.item("arch", frozenset({"architecture"}), cost=400),
            self.item("sec", frozenset({"security"}), cost=400),
        )
        with self.assertRaises(RuntimeError):
            self.lens().select(items, ContextRequest(
                AgentRole.ARCHITECT, frozenset({"architecture", "security"}), token_budget=512,
            ))

    def test_untrusted_mandatory_context_can_be_forbidden(self):
        item = self.item("external", frozenset({"architecture"}), trusted=False)
        with self.assertRaises(PermissionError):
            self.lens().select((item,), ContextRequest(
                AgentRole.ARCHITECT, frozenset(), mandatory_ids=frozenset({"external"}),
                token_budget=512, allow_untrusted_data=False,
            ))

    def test_context_selection_is_order_deterministic(self):
        items = (
            self.item("a", frozenset({"architecture", "role:architect"}), cost=150),
            self.item("b", frozenset({"security", "role:architect"}), cost=150),
            self.item("c", frozenset({"performance"}), cost=100),
        )
        request = ContextRequest(
            AgentRole.ARCHITECT, frozenset({"architecture", "security"}),
            preferred_tags=frozenset({"performance"}), token_budget=700,
        )
        self.assertEqual(
            self.lens().select(items, request).fingerprint(),
            self.lens().select(tuple(reversed(items)), request).fingerprint(),
        )


class TruthAndGenomeTests(unittest.TestCase):
    def fact(self, fact_id: str, value: str, *, trusted: bool = True) -> TruthFact:
        prefix = "trusted" if trusted else "claim"
        return TruthFact(
            f"{prefix}.{fact_id}", "api", "depends_on", sha(value), sha(f"source:{value}"),
            frozenset({"architecture", "api"}),
        )

    def truth(self, facts: tuple[TruthFact, ...]) -> CodeTruthMap:
        return CodeTruthMap(facts, lambda fact: fact.fact_id.startswith("trusted."))

    def test_unverified_fact_is_visible_but_not_authoritative(self):
        trusted = self.fact("one", "database", trusted=True)
        claim = self.fact("two", "queue", trusted=False)
        truth = self.truth((trusted, claim))
        self.assertEqual(len(truth.query(("architecture",), verified_only=False)), 2)
        self.assertEqual(len(truth.query(("architecture",))), 1)
        with self.assertRaises(PermissionError):
            truth.fact_fingerprint(claim.fact_id)

    def test_architectural_genome_requires_verified_provenance(self):
        claim = self.fact("one", "database", trusted=False)
        truth = self.truth((claim,))
        invariant = ArchitecturalInvariant("inv", sha("api boundary"), frozenset({"api"}), frozenset({claim.fact_id}), True)
        with self.assertRaises(PermissionError):
            ArchitecturalGenome(twin(), truth, (invariant,))

    def test_architectural_genome_detects_truth_drift(self):
        original = self.fact("one", "database", trusted=True)
        original_truth = self.truth((original,))
        invariant = ArchitecturalInvariant("inv", sha("api boundary"), frozenset({"api"}), frozenset({original.fact_id}), True)
        genome = ArchitecturalGenome(twin(), original_truth, (invariant,))
        changed = TruthFact(original.fact_id, original.subject, original.predicate, sha("new-database"), sha("new-source"), original.tags)
        changed_truth = self.truth((changed,))
        self.assertEqual(genome.detect_drift(twin(), changed_truth), ("inv",))

    def test_architectural_genome_detects_twin_drift(self):
        fact = self.fact("one", "database", trusted=True)
        truth = self.truth((fact,))
        invariant = ArchitecturalInvariant("inv", sha("api boundary"), frozenset({"api"}), frozenset({fact.fact_id}), True)
        genome = ArchitecturalGenome(twin(), truth, (invariant,))
        changed_twin = ProjectDigitalTwin((
            DigitalTwinNode("api", "service"),
            DigitalTwinNode("tests", "tests", ("api",)),
            DigitalTwinNode("ui", "frontend", ("api",)),
        ))
        self.assertEqual(genome.detect_drift(changed_twin, truth), ("inv",))


class ExperienceRoutingTests(ExpertAgentFixture):
    def ledger(self) -> ExperienceLedger:
        return ExperienceLedger(lambda result: result.result_id.startswith("trusted."))

    def test_untrusted_benchmark_claims_do_not_count(self):
        ledger = self.ledger()
        profile = self.profile(AgentRole.BACKEND, "backend-a")
        dims = required_dimensions_for_role(AgentRole.BACKEND)
        self.add_results(ledger, profile.agent_id, dims, trusted=False)
        report = ExperienceRouter(self.profile_authority, ledger).evaluate(
            profile, self.by_role[AgentRole.BACKEND], self.standard(AgentRole.BACKEND),
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("insufficient_samples" in code for code in report.blocking_codes))

    def test_single_suite_cannot_create_distinguished_reputation(self):
        ledger = self.ledger(); profile = self.profile(AgentRole.BACKEND, "backend-a")
        self.add_results(ledger, profile.agent_id, required_dimensions_for_role(AgentRole.BACKEND), suites=("only-suite",))
        report = ExperienceRouter(self.profile_authority, ledger).evaluate(
            profile, self.by_role[AgentRole.BACKEND], self.standard(AgentRole.BACKEND),
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("suite_diversity" in code for code in report.blocking_codes))

    def test_critical_failure_blocks_even_perfect_pass_rate(self):
        ledger = self.ledger(); profile = self.profile(AgentRole.SECURITY, "security-a")
        self.add_results(ledger, profile.agent_id, required_dimensions_for_role(AgentRole.SECURITY), critical=1)
        report = ExperienceRouter(self.profile_authority, ledger).evaluate(
            profile, self.by_role[AgentRole.SECURITY], self.standard(AgentRole.SECURITY),
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("critical_failure" in code for code in report.blocking_codes))

    def test_policy_violation_and_tamper_event_block(self):
        ledger = self.ledger(); profile = self.profile(AgentRole.REVIEWER, "reviewer-a")
        self.add_results(ledger, profile.agent_id, required_dimensions_for_role(AgentRole.REVIEWER), policy=1, tamper=1)
        report = ExperienceRouter(self.profile_authority, ledger).evaluate(
            profile, self.by_role[AgentRole.REVIEWER], self.standard(AgentRole.REVIEWER),
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("policy_violation" in code for code in report.blocking_codes))
        self.assertTrue(any("tamper_event" in code for code in report.blocking_codes))

    def test_router_prefers_stronger_confidence_adjusted_agent(self):
        ledger = self.ledger()
        weaker = self.profile(AgentRole.BACKEND, "backend-weaker")
        stronger = self.profile(AgentRole.BACKEND, "backend-stronger")
        dims = required_dimensions_for_role(AgentRole.BACKEND)
        self.add_results(ledger, weaker.agent_id, dims, successes=9, total=10)
        self.add_results(ledger, stronger.agent_id, dims, successes=20, total=20)
        registry = self.registry((weaker, stronger))
        profile, report = ExperienceRouter(self.profile_authority, ledger).route(
            registry.profiles_for(AgentRole.BACKEND), registry.capsules(),
            AgentRole.BACKEND, self.standard(AgentRole.BACKEND, min_samples=10, lower=0.5),
        )
        self.assertEqual(profile.agent_id, "backend-stronger")
        self.assertTrue(report.passed)

    def test_wilson_lower_bound_penalizes_small_samples(self):
        self.assertLess(
            ExperienceLedger.wilson_lower_bound(5, 5),
            ExperienceLedger.wilson_lower_bound(50, 50),
        )


class AgentMeshTests(ExpertAgentFixture):
    def setup_mesh(self, backend_lineage: str, reviewer_lineage: str):
        backend = self.profile(AgentRole.BACKEND, "backend-a", backend_lineage)
        reviewer = self.profile(AgentRole.REVIEWER, "reviewer-a", reviewer_lineage)
        registry = self.registry((backend, reviewer))
        ledger = ExperienceLedger(lambda result: result.result_id.startswith("trusted."))
        self.add_results(ledger, backend.agent_id, required_dimensions_for_role(AgentRole.BACKEND))
        self.add_results(ledger, reviewer.agent_id, required_dimensions_for_role(AgentRole.REVIEWER))
        router = ExperienceRouter(self.profile_authority, ledger)
        standards = {
            AgentRole.BACKEND: self.standard(AgentRole.BACKEND),
            AgentRole.REVIEWER: self.standard(AgentRole.REVIEWER),
        }
        return AgentMesh(self.plan_authority, twin(), registry, router, standards)

    def test_agent_mesh_assigns_measured_specialists(self):
        mesh = self.setup_mesh("impl-lineage", "review-lineage")
        assignments = mesh.assign(master(self.plan_authority))
        self.assertEqual([item.agent_id for item in assignments], ["backend-a", "reviewer-a"])
        self.assertEqual(len({item.competence_fingerprint for item in assignments}), 2)

    def test_agent_mesh_rejects_reviewer_from_implementation_lineage(self):
        mesh = self.setup_mesh("shared-lineage", "shared-lineage")
        with self.assertRaises(PermissionError):
            mesh.assign(master(self.plan_authority))

    def test_agent_mesh_rejects_forged_master_plan(self):
        mesh = self.setup_mesh("impl-lineage", "review-lineage")
        forged = replace(master(self.plan_authority), approval_tag="0" * 64)
        with self.assertRaises(PermissionError):
            mesh.assign(forged)

    def test_agent_mesh_rejects_digital_twin_drift(self):
        mesh = self.setup_mesh("impl-lineage", "review-lineage")
        changed_twin = ProjectDigitalTwin((
            DigitalTwinNode("api", "service"),
            DigitalTwinNode("tests", "tests", ("api",)),
            DigitalTwinNode("ui", "frontend", ("api",)),
        ))
        changed_master = master(self.plan_authority, changed_twin)
        with self.assertRaises(ValueError):
            mesh.assign(changed_master)


class ChallengeEngineTests(ExpertAgentFixture):
    def challengers(self, same_lineage: bool = False, blocking: bool = False):
        architect = self.profile(AgentRole.ARCHITECT, "counterplan-agent", "challenge-shared" if same_lineage else "counter-lineage")
        reviewer = self.profile(AgentRole.REVIEWER, "failure-agent", "challenge-shared" if same_lineage else "failure-lineage")
        severity = FindingSeverity.HIGH if blocking else FindingSeverity.INFO
        return {
            ChallengeKind.COUNTERPLAN: (
                architect,
                lambda _master: (ChallengeAssessment(FindingSeverity.INFO, "alternative-considered", "impl", ("repo-map",)),),
            ),
            ChallengeKind.FAILURE_ORACLE: (
                reviewer,
                lambda _master: (ChallengeAssessment(severity, "failure-mode-reviewed", "review", ("test-evidence",)),),
            ),
        }

    def test_counterplan_and_failure_oracle_identity_is_host_bound(self):
        report = AdversarialChallengeEngine(self.profile_authority).run(
            master(self.plan_authority), self.challengers(),
        )
        identities = {finding.kind: finding.challenger_agent_id for finding in report.findings}
        self.assertEqual(identities[ChallengeKind.COUNTERPLAN], "counterplan-agent")
        self.assertEqual(identities[ChallengeKind.FAILURE_ORACLE], "failure-agent")
        self.assertFalse(report.blocked)

    def test_blocking_challenge_is_reported_without_granting_authority(self):
        report = AdversarialChallengeEngine(self.profile_authority).run(
            master(self.plan_authority), self.challengers(blocking=True),
        )
        self.assertTrue(report.blocked)
        self.assertIn("failure-mode-reviewed", report.blocking_codes)

    def test_challengers_must_be_independence_separated(self):
        with self.assertRaises(PermissionError):
            AdversarialChallengeEngine(self.profile_authority).run(
                master(self.plan_authority), self.challengers(same_lineage=True),
            )

    def test_missing_challenge_kind_fails_closed(self):
        challengers = self.challengers()
        del challengers[ChallengeKind.FAILURE_ORACLE]
        with self.assertRaises(ValueError):
            AdversarialChallengeEngine(self.profile_authority).run(master(self.plan_authority), challengers)

    def test_forged_challenger_profile_fails_closed(self):
        challengers = self.challengers()
        profile, port = challengers[ChallengeKind.COUNTERPLAN]
        challengers[ChallengeKind.COUNTERPLAN] = (replace(profile, profile_tag="0" * 64), port)
        with self.assertRaises(PermissionError):
            AdversarialChallengeEngine(self.profile_authority).run(master(self.plan_authority), challengers)


if __name__ == "__main__":
    unittest.main()
