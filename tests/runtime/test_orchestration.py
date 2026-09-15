from __future__ import annotations

import hashlib
import unittest

from hive_runtime.agent_tasks import ActionKind, TaskSnapshot, TaskStatus, NodeStatus, TaskEvent
from hive_runtime.orchestration import (
    AgentOrchestrator,
    AgentRole,
    Assumption,
    ConfidenceLevel,
    CouncilFinding,
    DeepPlanEngine,
    DeepPlanProposal,
    DigitalTwinNode,
    EvidenceGraph,
    EvidenceKind,
    EvidenceRecord,
    FindingSeverity,
    ObjectiveSpec,
    PlanGraphCompiler,
    PlanStep,
    ProjectDigitalTwin,
    RiskTier,
    SelfCorrectionLedger,
    StopCondition,
    StopIntelligence,
)


def objective(risk=RiskTier.ELEVATED):
    return ObjectiveSpec(
        "obj-1",
        "Implement secure authentication",
        risk,
        ("no credential leakage",),
        ("login works", "invalid tokens rejected"),
        (
            StopCondition("tests-green", "tests must pass", frozenset({EvidenceKind.TEST})),
            StopCondition("security-reviewed", "security review complete", frozenset({EvidenceKind.SECURITY, EvidenceKind.REVIEW})),
        ),
    )


def twin():
    return ProjectDigitalTwin((
        DigitalTwinNode("auth", "service"),
        DigitalTwinNode("api", "service", ("auth",)),
        DigitalTwinNode("ui", "frontend", ("api",)),
        DigitalTwinNode("tests", "tests", ("auth", "api")),
    ))


def proposal(assumptions=None):
    return DeepPlanProposal(
        tuple(assumptions or (Assumption("a1", "existing auth boundary is understood", ConfidenceLevel.VERIFIED, True, ("repo-map",)),)),
        (
            PlanStep(
                "design", "Design auth change", AgentRole.ARCHITECT, ActionKind.MODEL_PROMPT,
                requirement_indexes=frozenset({0}), change_targets=frozenset({"auth"}),
                required_model_capabilities=frozenset({"tool_calling"}), instruction="Design the bounded auth change.", max_attempts=2,
            ),
            PlanStep(
                "implement", "Implement auth", AgentRole.BACKEND, ActionKind.MODEL_PROMPT,
                depends_on=("design",), requirement_indexes=frozenset({0, 1}), change_targets=frozenset({"auth"}),
                required_model_capabilities=frozenset({"tool_calling"}), instruction="Implement the approved design.", max_attempts=2,
            ),
            PlanStep(
                "verify", "Verify auth", AgentRole.QA, ActionKind.SKILL,
                depends_on=("implement",), requirement_indexes=frozenset({0, 1}), change_targets=frozenset({"tests"}),
                skill_id="tests.auth", skill_version="1.0.0", max_attempts=1,
            ),
        ),
    )


def council(extra=()):
    return (
        CouncilFinding(AgentRole.ARCHITECT, FindingSeverity.INFO, "architecture_reviewed"),
        CouncilFinding(AgentRole.SECURITY, FindingSeverity.INFO, "security_reviewed"),
        CouncilFinding(AgentRole.QA, FindingSeverity.INFO, "qa_reviewed"),
        CouncilFinding(AgentRole.REVIEWER, FindingSeverity.INFO, "independent_reviewed"),
        *tuple(extra),
    )


class MasterPlannerTests(unittest.TestCase):
    def build(self, prop=None, findings=None, obj=None):
        return DeepPlanEngine().build(
            obj or objective(),
            twin=twin(),
            planner=lambda _objective, _twin: prop or proposal(),
            council=lambda _objective, _proposal: findings or council(),
        )

    def test_deep_plan_builds_with_independent_council(self):
        master = self.build()
        self.assertEqual(len(master.steps), 3)
        self.assertEqual(master.change_radius.targets, frozenset({"auth", "tests"}))
        self.assertIn("ui", master.change_radius.affected)

    def test_critical_unknown_assumption_blocks(self):
        bad = proposal((Assumption("a1", "unknown system fact", ConfidenceLevel.UNKNOWN, True),))
        with self.assertRaises(ValueError):
            self.build(prop=bad)

    def test_high_assurance_critical_inferred_assumption_blocks(self):
        bad = proposal((Assumption("a1", "inferred system fact", ConfidenceLevel.INFERRED, True),))
        with self.assertRaises(ValueError):
            self.build(prop=bad, obj=objective(RiskTier.HIGH_ASSURANCE))

    def test_missing_council_role_blocks(self):
        findings = tuple(item for item in council() if item.reviewer is not AgentRole.SECURITY)
        with self.assertRaises(ValueError):
            self.build(findings=findings)

    def test_high_council_finding_blocks(self):
        findings = council((CouncilFinding(AgentRole.SECURITY, FindingSeverity.HIGH, "credential_boundary_broken", "implement"),))
        with self.assertRaises(ValueError):
            self.build(findings=findings)

    def test_unapproved_council_role_cannot_vote(self):
        findings = council((CouncilFinding(AgentRole.BACKEND, FindingSeverity.INFO, "looks_good"),))
        with self.assertRaises(ValueError):
            self.build(findings=findings)

    def test_plan_must_cover_every_acceptance_criterion(self):
        p = proposal()
        steps = tuple(
            PlanStep(
                s.step_id, s.title, s.role, s.action, s.depends_on,
                frozenset({0}), s.change_targets, s.required_model_capabilities, s.provider,
                s.instruction, s.skill_id, s.skill_version, s.max_attempts,
            )
            for s in p.steps
        )
        with self.assertRaises(ValueError):
            self.build(prop=DeepPlanProposal(p.assumptions, steps))

    def test_cycle_blocks(self):
        p = proposal()
        first = p.steps[0]
        cycle_first = PlanStep(
            first.step_id, first.title, first.role, first.action, ("verify",), first.requirement_indexes,
            first.change_targets, first.required_model_capabilities, first.provider, first.instruction,
            first.skill_id, first.skill_version, first.max_attempts,
        )
        with self.assertRaises(ValueError):
            self.build(prop=DeepPlanProposal(p.assumptions, (cycle_first, *p.steps[1:])))

    def test_change_radius_is_reverse_dependency_aware(self):
        radius = twin().change_radius(("auth",), max_depth=4, max_nodes=20)
        self.assertEqual(radius.affected, frozenset({"auth", "api", "ui", "tests"}))

    def test_change_radius_bound_fails_closed(self):
        engine = DeepPlanEngine()
        engine.policy = type(engine.policy)(engine.policy.required_council_roles, max_change_radius=1, change_radius_depth=4)
        with self.assertRaises(ValueError):
            engine.build(objective(), twin=twin(), planner=lambda *_: proposal(), council=lambda *_: council())

    def test_master_fingerprint_is_stable(self):
        self.assertEqual(self.build().fingerprint(), self.build().fingerprint())


class PlanCompilerTests(unittest.TestCase):
    def test_master_plan_compiles_only_supported_task_node_types(self):
        master = MasterPlannerTests().build()
        task_plan = PlanGraphCompiler().compile(master)
        self.assertEqual([n.action for n in task_plan.nodes], [ActionKind.MODEL_PROMPT, ActionKind.MODEL_PROMPT, ActionKind.SKILL])
        self.assertEqual(task_plan.nodes[2].skill_id, "tests.auth")


class StopIntelligenceTests(unittest.TestCase):
    def record(self, evidence_id, kind, trusted=True):
        return EvidenceRecord(evidence_id, kind, "ci", hashlib.sha256(evidence_id.encode()).hexdigest(), trusted)

    def test_untrusted_agent_claim_cannot_satisfy_stop(self):
        graph = EvidenceGraph()
        graph.add(self.record("claim", EvidenceKind.TEST, trusted=False), requirement_indexes=(0, 1), stop_conditions=("tests-green",))
        decision = StopIntelligence().evaluate(objective(), graph)
        self.assertFalse(decision.complete)
        self.assertEqual(decision.missing_acceptance, (0, 1))

    def test_stop_requires_every_required_evidence_kind(self):
        graph = EvidenceGraph()
        graph.add(self.record("t", EvidenceKind.TEST), requirement_indexes=(0, 1), stop_conditions=("tests-green",))
        graph.add(self.record("s", EvidenceKind.SECURITY), stop_conditions=("security-reviewed",))
        self.assertFalse(StopIntelligence().evaluate(objective(), graph).complete)
        graph.add(self.record("r", EvidenceKind.REVIEW), stop_conditions=("security-reviewed",))
        self.assertTrue(StopIntelligence().evaluate(objective(), graph).complete)

    def test_duplicate_evidence_id_rejected(self):
        graph = EvidenceGraph(); record = self.record("x", EvidenceKind.TEST)
        graph.add(record)
        with self.assertRaises(ValueError): graph.add(record)


class CorrectionAndOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.master = MasterPlannerTests().build()
        self.obj = objective()

    def test_self_correction_cannot_expand_change_scope(self):
        ledger = SelfCorrectionLedger(self.master)
        with self.assertRaises(PermissionError):
            ledger.request("implement", "test_failed", ("ui",))

    def test_self_correction_is_bounded(self):
        ledger = SelfCorrectionLedger(self.master, max_total=2, max_per_step=1)
        ledger.request("implement", "test_failed", ("auth",))
        with self.assertRaises(RuntimeError):
            ledger.request("implement", "test_failed_again", ("auth",))

    def test_orchestrator_telemetry_uses_task_state_and_trusted_stop_evidence(self):
        orchestrator = AgentOrchestrator(self.master, self.obj)
        node_status = (("design", NodeStatus.SUCCEEDED), ("implement", NodeStatus.SUCCEEDED), ("verify", NodeStatus.PENDING))
        snap = TaskSnapshot("task", "fp", TaskStatus.PENDING, node_status, (("design",1),("implement",1),("verify",0)), 2, 0, 0, tuple())
        graph = EvidenceGraph()
        graph.add(EvidenceRecord("tests", EvidenceKind.TEST, "ci", hashlib.sha256(b"tests").hexdigest(), True), requirement_indexes=(0,1), stop_conditions=("tests-green",))
        ledger = SelfCorrectionLedger(self.master)
        telemetry = orchestrator.telemetry(snap, graph, ledger)
        self.assertEqual(telemetry.completed_steps, 2)
        self.assertEqual(telemetry.progress_percent, 66.67)
        self.assertFalse(telemetry.stop_complete)

    def test_snapshot_plan_mismatch_fails_closed(self):
        orchestrator = AgentOrchestrator(self.master, self.obj)
        snap = TaskSnapshot("task", "fp", TaskStatus.PENDING, (("wrong", NodeStatus.PENDING),), (("wrong",0),), 0, 0, 0, tuple())
        with self.assertRaises(ValueError):
            orchestrator.telemetry(snap, EvidenceGraph(), SelfCorrectionLedger(self.master))


if __name__ == "__main__":
    unittest.main()
