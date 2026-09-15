from __future__ import annotations

import hashlib
import unittest

from hive_runtime.agent_tasks import ActionKind, TaskBudget, TaskSnapshot, TaskStatus, NodeStatus
from hive_runtime.orchestration import (
    AgentOrchestrator, AgentRole, Assumption, ConfidenceLevel, CouncilAssessment,
    DeepPlanEngine, DeepPlanProposal, DigitalTwinNode, EvidenceGraph, EvidenceKind,
    EvidenceRecord, FindingSeverity, ObjectiveSpec, PlanGraphCompiler, PlanStep,
    PlanningPolicy, ProjectDigitalTwin, RiskTier, SelfCorrectionLedger, StopCondition,
    StopIntelligence,
)


def objective(risk=RiskTier.ELEVATED):
    return ObjectiveSpec(
        "obj-1", "Implement secure authentication", risk,
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


def council_port(_objective, _proposal, reviewer):
    return (CouncilAssessment(FindingSeverity.INFO, f"{reviewer.value}_reviewed"),)


def assumption_verifier(assumption):
    return assumption.evidence_refs == ("repo-map",)


class MasterPlannerTests(unittest.TestCase):
    def build(self, prop=None, council=None, obj=None, verifier=assumption_verifier, policy=None):
        return DeepPlanEngine(policy or PlanningPolicy()).build(
            obj or objective(), twin=twin(), planner=lambda _o, _t: prop or proposal(),
            council=council or council_port, assumption_verifier=verifier,
        )

    def test_deep_plan_builds_with_host_bound_independent_council(self):
        master = self.build()
        self.assertEqual(len(master.steps), 3)
        self.assertEqual({f.reviewer for f in master.council_findings},
                         {AgentRole.ARCHITECT, AgentRole.SECURITY, AgentRole.QA, AgentRole.REVIEWER})
        self.assertIn("ui", master.change_radius.affected)

    def test_planner_cannot_self_assert_verified_assumption(self):
        with self.assertRaises(ValueError): self.build(verifier=lambda _a: False)

    def test_critical_unknown_assumption_blocks(self):
        bad = proposal((Assumption("a1", "unknown system fact", ConfidenceLevel.UNKNOWN, True),))
        with self.assertRaises(ValueError): self.build(prop=bad)

    def test_high_assurance_critical_inferred_assumption_blocks(self):
        bad = proposal((Assumption("a1", "inferred system fact", ConfidenceLevel.INFERRED, True),))
        with self.assertRaises(ValueError): self.build(prop=bad, obj=objective(RiskTier.HIGH_ASSURANCE))

    def test_missing_council_assessment_blocks(self):
        def missing(_o, _p, reviewer):
            return () if reviewer is AgentRole.SECURITY else (CouncilAssessment(FindingSeverity.INFO, "reviewed"),)
        with self.assertRaises(ValueError): self.build(council=missing)

    def test_high_council_finding_blocks(self):
        def blocked(_o, _p, reviewer):
            sev = FindingSeverity.HIGH if reviewer is AgentRole.SECURITY else FindingSeverity.INFO
            return (CouncilAssessment(sev, "credential_boundary_broken", "implement"),)
        with self.assertRaises(ValueError): self.build(council=blocked)

    def test_medium_council_finding_blocks_elevated_plan(self):
        def blocked(_o, _p, reviewer):
            sev = FindingSeverity.MEDIUM if reviewer is AgentRole.QA else FindingSeverity.INFO
            return (CouncilAssessment(sev, "coverage_gap"),)
        with self.assertRaises(ValueError): self.build(council=blocked)

    def test_plan_must_cover_every_acceptance_criterion(self):
        p = proposal(); steps = tuple(
            PlanStep(s.step_id, s.title, s.role, s.action, s.depends_on, frozenset({0}), s.change_targets,
                     s.required_model_capabilities, s.provider, s.instruction, s.skill_id, s.skill_version, s.max_attempts)
            for s in p.steps
        )
        with self.assertRaises(ValueError): self.build(prop=DeepPlanProposal(p.assumptions, steps))

    def test_cycle_blocks(self):
        p = proposal(); first = p.steps[0]
        cycle_first = PlanStep(first.step_id, first.title, first.role, first.action, ("verify",), first.requirement_indexes,
                               first.change_targets, first.required_model_capabilities, first.provider, first.instruction,
                               first.skill_id, first.skill_version, first.max_attempts)
        with self.assertRaises(ValueError): self.build(prop=DeepPlanProposal(p.assumptions, (cycle_first, *p.steps[1:])))

    def test_change_radius_is_reverse_dependency_aware(self):
        radius = twin().change_radius(("auth",), max_depth=4, max_nodes=20)
        self.assertEqual(radius.affected, frozenset({"auth", "api", "ui", "tests"}))
        self.assertFalse(radius.truncated)

    def test_depth_limited_change_radius_marks_truncation(self):
        radius = twin().change_radius(("auth",), max_depth=1, max_nodes=20)
        self.assertTrue(radius.truncated)
        self.assertEqual(radius.affected, frozenset({"auth", "api", "tests"}))

    def test_change_radius_bound_fails_closed(self):
        policy = PlanningPolicy(max_change_radius=1, change_radius_depth=4)
        with self.assertRaises(ValueError): self.build(policy=policy)

    def test_master_fingerprint_is_stable(self):
        self.assertEqual(self.build().fingerprint(), self.build().fingerprint())


class PlanCompilerTests(unittest.TestCase):
    def test_master_plan_compiles_only_supported_task_node_types(self):
        master = MasterPlannerTests().build()
        task_plan = PlanGraphCompiler().compile(master)
        self.assertEqual([n.action for n in task_plan.nodes], [ActionKind.MODEL_PROMPT, ActionKind.MODEL_PROMPT, ActionKind.SKILL])
        self.assertEqual(task_plan.nodes[2].skill_id, "tests.auth")


class StopIntelligenceTests(unittest.TestCase):
    def record(self, evidence_id, kind, source="ci"):
        return EvidenceRecord(evidence_id, kind, source, hashlib.sha256(evidence_id.encode()).hexdigest())

    def graph(self):
        return EvidenceGraph(lambda record: record.source in {"ci", "security-gate", "heds"})

    def test_evidence_producer_cannot_self_mark_trust(self):
        graph = self.graph()
        record = self.record("claim", EvidenceKind.TEST, source="model-output")
        graph.add(record, requirement_indexes=(0, 1), stop_conditions=("tests-green",))
        decision = StopIntelligence().evaluate(objective(), graph)
        self.assertFalse(decision.complete)
        self.assertEqual(decision.missing_acceptance, (0, 1))

    def test_stop_requires_every_required_evidence_kind(self):
        graph = self.graph()
        graph.add(self.record("t", EvidenceKind.TEST), requirement_indexes=(0,1), stop_conditions=("tests-green",))
        graph.add(self.record("s", EvidenceKind.SECURITY, "security-gate"), stop_conditions=("security-reviewed",))
        self.assertFalse(StopIntelligence().evaluate(objective(), graph).complete)
        graph.add(self.record("r", EvidenceKind.REVIEW, "heds"), stop_conditions=("security-reviewed",))
        self.assertTrue(StopIntelligence().evaluate(objective(), graph).complete)

    def test_invalid_link_fails_atomically(self):
        graph = self.graph(); record = self.record("x", EvidenceKind.TEST)
        with self.assertRaises(ValueError): graph.add(record, requirement_indexes=(-1,))
        graph.add(record, requirement_indexes=(0,))
        self.assertEqual(len(graph.trusted_for_requirement(0)), 1)

    def test_duplicate_evidence_id_rejected(self):
        graph = self.graph(); record = self.record("x", EvidenceKind.TEST); graph.add(record)
        with self.assertRaises(ValueError): graph.add(record)


class CorrectionAndOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.master = MasterPlannerTests().build(); self.obj = objective()

    def test_self_correction_cannot_expand_change_scope(self):
        ledger = SelfCorrectionLedger(self.master)
        with self.assertRaises(PermissionError): ledger.request("implement", "test_failed", ("ui",))

    def test_self_correction_is_bounded(self):
        ledger = SelfCorrectionLedger(self.master, max_total=2, max_per_step=1)
        ledger.request("implement", "test_failed", ("auth",))
        with self.assertRaises(RuntimeError): ledger.request("implement", "test_failed_again", ("auth",))

    def snapshot(self, orchestrator, node_status):
        plan = orchestrator.task_plan()
        attempts = tuple((step.step_id, 1 if dict(node_status)[step.step_id] is NodeStatus.SUCCEEDED else 0) for step in self.master.steps)
        return TaskSnapshot("task", plan.fingerprint(), TaskStatus.PENDING, node_status, attempts, TaskBudget(20, 5), 2, 0, 0, tuple())

    def test_orchestrator_telemetry_uses_task_state_and_trusted_stop_evidence(self):
        orchestrator = AgentOrchestrator(self.master, self.obj)
        node_status = (("design", NodeStatus.SUCCEEDED), ("implement", NodeStatus.SUCCEEDED), ("verify", NodeStatus.PENDING))
        graph = EvidenceGraph(lambda record: record.source == "ci")
        graph.add(EvidenceRecord("tests", EvidenceKind.TEST, "ci", hashlib.sha256(b"tests").hexdigest()),
                  requirement_indexes=(0,1), stop_conditions=("tests-green",))
        telemetry = orchestrator.telemetry(self.snapshot(orchestrator, node_status), graph, SelfCorrectionLedger(self.master))
        self.assertEqual(telemetry.completed_steps, 2)
        self.assertEqual(telemetry.progress_percent, 66.67)
        self.assertFalse(telemetry.stop_complete)

    def test_snapshot_fingerprint_mismatch_fails_closed(self):
        orchestrator = AgentOrchestrator(self.master, self.obj)
        node_status = (("design", NodeStatus.PENDING), ("implement", NodeStatus.PENDING), ("verify", NodeStatus.PENDING))
        snap = TaskSnapshot("task", "0" * 64, TaskStatus.PENDING, node_status,
                            (("design",0),("implement",0),("verify",0)), TaskBudget(20,5), 0, 0, 0, tuple())
        with self.assertRaises(ValueError): orchestrator.telemetry(snap, EvidenceGraph(lambda _r: True), SelfCorrectionLedger(self.master))


if __name__ == "__main__":
    unittest.main()
