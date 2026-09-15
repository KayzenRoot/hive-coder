from __future__ import annotations
from dataclasses import replace
from hive_runtime.expert_agents import AdversarialChallengeEngine, AgentMesh, ChallengeAssessment, ChallengeKind, ExperienceRouter
from hive_runtime.orchestration import AgentRole, DigitalTwinNode, FindingSeverity, ProjectDigitalTwin
from tests.runtime.expert_agent_fixture import ExpertAgentFixture, master, twin


class AgentMeshTests(ExpertAgentFixture):
    def setup_mesh(self, backend_lineage: str, reviewer_lineage: str,
                   *, backend_caps: frozenset[str] = frozenset({"tool_calling", "structured_output"})):
        backend = self.profile(AgentRole.BACKEND, "backend-a", backend_lineage, caps=backend_caps)
        reviewer = self.profile(AgentRole.REVIEWER, "reviewer-a", reviewer_lineage)
        registry = self.registry((backend, reviewer)); ledger = self.ledger()
        self.add_results(ledger, backend); self.add_results(ledger, reviewer)
        router = ExperienceRouter(self.profile_authority, ledger)
        standards = {AgentRole.BACKEND: self.standard(AgentRole.BACKEND),
                     AgentRole.REVIEWER: self.standard(AgentRole.REVIEWER)}
        return AgentMesh(self.plan_authority, twin(), registry, router, standards)

    def test_agent_mesh_assigns_measured_specialists(self):
        assignments = self.setup_mesh("impl-lineage", "review-lineage").assign(master(self.plan_authority))
        self.assertEqual([item.agent_id for item in assignments], ["backend-a", "reviewer-a"])

    def test_reviewer_separation_is_order_independent(self):
        mesh = self.setup_mesh("shared-lineage", "shared-lineage")
        for review_first in (False, True):
            with self.assertRaises(PermissionError):
                mesh.assign(master(self.plan_authority, review_first=review_first))

    def test_step_capability_requirements_must_fit_selected_profile(self):
        mesh = self.setup_mesh("impl-lineage", "review-lineage")
        with self.assertRaises(LookupError):
            mesh.assign(master(self.plan_authority, backend_caps=frozenset({"tool_calling", "vision"})))

    def test_agent_mesh_rejects_forged_master_and_twin_drift(self):
        mesh = self.setup_mesh("impl-lineage", "review-lineage")
        forged = replace(master(self.plan_authority), approval_tag="0" * 64)
        with self.assertRaises(PermissionError):
            mesh.assign(forged)
        changed_twin = ProjectDigitalTwin((DigitalTwinNode("api", "service"),
                                           DigitalTwinNode("tests", "tests", ("api",)),
                                           DigitalTwinNode("ui", "frontend", ("api",))))
        with self.assertRaises(ValueError):
            mesh.assign(master(self.plan_authority, changed_twin))


class ChallengeEngineTests(ExpertAgentFixture):
    def setup_engine(self, *, measure=True):
        architect = self.profile(AgentRole.ARCHITECT, "counterplan-agent", "counter-lineage")
        reviewer = self.profile(AgentRole.REVIEWER, "failure-agent", "failure-lineage")
        registry = self.registry((architect, reviewer)); ledger = self.ledger()
        if measure:
            self.add_results(ledger, architect); self.add_results(ledger, reviewer)
        router = ExperienceRouter(self.profile_authority, ledger)
        standards = {AgentRole.ARCHITECT: self.standard(AgentRole.ARCHITECT),
                     AgentRole.REVIEWER: self.standard(AgentRole.REVIEWER)}
        engine = AdversarialChallengeEngine(
            self.plan_authority, twin(), self.profile_authority, registry, router, standards,
        )
        return engine, architect, reviewer

    @staticmethod
    def challengers(architect, reviewer, *, blocking=False):
        severity = FindingSeverity.HIGH if blocking else FindingSeverity.INFO
        return {
            ChallengeKind.COUNTERPLAN: (architect, lambda _m: (
                ChallengeAssessment(FindingSeverity.INFO, "alternative-considered", "impl", ("repo-map",)),)),
            ChallengeKind.FAILURE_ORACLE: (reviewer, lambda _m: (
                ChallengeAssessment(severity, "failure-mode-reviewed", "review", ("test-evidence",)),)),
        }

    def test_challengers_are_host_bound_measured_and_independent(self):
        engine, architect, reviewer = self.setup_engine()
        report = engine.run(master(self.plan_authority), self.challengers(architect, reviewer))
        self.assertFalse(report.blocked)
        self.assertEqual({item.challenger_agent_id for item in report.findings},
                         {"counterplan-agent", "failure-agent"})

    def test_unmeasured_challenger_is_rejected(self):
        engine, architect, reviewer = self.setup_engine(measure=False)
        with self.assertRaises(PermissionError):
            engine.run(master(self.plan_authority), self.challengers(architect, reviewer))

    def test_challenge_engine_rejects_forged_master(self):
        engine, architect, reviewer = self.setup_engine()
        forged = replace(master(self.plan_authority), approval_tag="0" * 64)
        with self.assertRaises(PermissionError):
            engine.run(forged, self.challengers(architect, reviewer))

    def test_challenge_role_eligibility_is_enforced(self):
        backend = self.profile(AgentRole.BACKEND, "backend-challenger", "backend-lineage")
        reviewer = self.profile(AgentRole.REVIEWER, "failure-agent", "failure-lineage")
        registry = self.registry((backend, reviewer)); ledger = self.ledger()
        self.add_results(ledger, backend); self.add_results(ledger, reviewer)
        router = ExperienceRouter(self.profile_authority, ledger)
        standards = {AgentRole.BACKEND: self.standard(AgentRole.BACKEND),
                     AgentRole.REVIEWER: self.standard(AgentRole.REVIEWER)}
        engine = AdversarialChallengeEngine(
            self.plan_authority, twin(), self.profile_authority, registry, router, standards,
        )
        with self.assertRaises(PermissionError):
            engine.run(master(self.plan_authority), self.challengers(backend, reviewer))

    def test_blocking_challenge_is_reported(self):
        engine, architect, reviewer = self.setup_engine()
        report = engine.run(master(self.plan_authority), self.challengers(architect, reviewer, blocking=True))
        self.assertTrue(report.blocked)
        self.assertIn("failure-mode-reviewed", report.blocking_codes)

    def test_challengers_must_be_independence_separated(self):
        architect = self.profile(AgentRole.ARCHITECT, "counterplan-agent", "shared")
        reviewer = self.profile(AgentRole.REVIEWER, "failure-agent", "shared")
        registry = self.registry((architect, reviewer)); ledger = self.ledger()
        self.add_results(ledger, architect); self.add_results(ledger, reviewer)
        engine = AdversarialChallengeEngine(
            self.plan_authority, twin(), self.profile_authority, registry,
            ExperienceRouter(self.profile_authority, ledger),
            {AgentRole.ARCHITECT: self.standard(AgentRole.ARCHITECT),
             AgentRole.REVIEWER: self.standard(AgentRole.REVIEWER)},
        )
        with self.assertRaises(PermissionError):
            engine.run(master(self.plan_authority), self.challengers(architect, reviewer))
