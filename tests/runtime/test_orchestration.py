from __future__ import annotations

import hashlib
import unittest
from dataclasses import replace

from hive_runtime.agent_tasks import ActionKind, TaskBudget, TaskSnapshot, TaskStatus, NodeStatus
from hive_runtime.orchestration import (
    AgentOrchestrator, AgentRole, Assumption, ConfidenceLevel, CouncilAssessment,
    DeepPlanEngine, DeepPlanProposal, DigitalTwinNode, EvidenceGraph, EvidenceKind,
    EvidenceRecord, FindingSeverity, ObjectiveSpec, PlanApprovalAuthority,
    PlanGraphCompiler, PlanStep, PlanningPolicy, ProjectDigitalTwin, RiskTier,
    SelfCorrectionLedger, StopCondition, StopIntelligence,
)

_PLAN_KEY = b"planner-test-key-32-bytes-minimum!!!"


def authority():
    return PlanApprovalAuthority(_PLAN_KEY)


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


def changed_twin():
    return ProjectDigitalTwin((
        DigitalTwinNode("auth", "service-v2"),
        DigitalTwinNode("api", "service", ("auth",)),
        DigitalTwinNode("ui", "frontend", ("api",)),
        DigitalTwinNode("tests", "tests", ("auth", "api")),
    ))


def proposal(assumptions=None):
    return DeepPlanProposal(
        tuple(assumptions or (Assumption("a1", "existing auth boundary is understood", ConfidenceLevel.VERIFIED, True, ("repo-map",)),)),
        (
            PlanStep(
                step_id="design", title="Design auth change", role=AgentRole.ARCHITECT, action=ActionKind.MODEL_PROMPT,
                requirement_indexes=frozenset({0}), constraint_indexes=frozenset({0}), change_targets=frozenset({"auth"}),
                required_model_capabilities=frozenset({"tool_calling"}), instruction="Design the bounded auth change.", max_attempts=2,
            ),
            PlanStep(
                step_id="implement", title="Implement auth", role=AgentRole.BACKEND, action=ActionKind.MODEL_PROMPT,
                depends_on=("design",), requirement_indexes=frozenset({0, 1}), constraint_indexes=frozenset({0}),
                change_targets=frozenset({"auth"}), required_model_capabilities=frozenset({"tool_calling"}),
                instruction="Implement the approved design.", max_attempts=2,
            ),
            PlanStep(
                step_id="verify", title="Verify auth", role=AgentRole.QA, action=ActionKind.SKILL,
                depends_on=("implement",), requirement_indexes=frozenset({0, 1}), constraint_indexes=frozenset({0}),
                change_targets=frozenset({"tests"}), skill_id="tests.auth", skill_version="1.0.0", max_attempts=1,
            ),
        ),
    )


def council_port(_objective, _proposal, reviewer):
    return (CouncilAssessment(FindingSeverity.INFO, f"{reviewer.value}_reviewed"),)


def assumption_verifier(assumption):
    return assumption.evidence_refs == ("repo-map",)


class MasterPlannerTests(unittest.TestCase):
    def build(self, prop=None, council=None, obj=None, verifier=assumption_verifier, policy=None):
        return DeepPlanEngine(authority(), policy or PlanningPolicy()).build(
            obj or objective(), twin=twin(), planner=lambda _o, _t: prop or proposal(),
            council=council or council_port, assumption_verifier=verifier,
        )

    def test_deep_plan_builds_sealed_plan_with_host_bound_council(self):
        master = self.build()
        self.assertTrue(authority().verify(master))
        self.assertEqual(master.twin_fingerprint, twin().fingerprint())
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
        p = proposal(); steps = tuple(replace(step, requirement_indexes=frozenset({0})) for step in p.steps)
        with self.assertRaises(ValueError): self.build(prop=DeepPlanProposal(p.assumptions, steps))

    def test_plan_must_cover_every_objective_constraint(self):
        p = proposal(); steps = tuple(replace(step, constraint_indexes=frozenset()) for step in p.steps)
        with self.assertRaises(ValueError): self.build(prop=DeepPlanProposal(p.assumptions, steps))

    def test_cycle_blocks(self):
        p = proposal(); cycle_first = replace(p.steps[0], depends_on=("verify",))
        with self.assertRaises(ValueError): self.build(prop=DeepPlanProposal(p.assumptions, (cycle_first, *p.steps[1:])))

    def test_change_radius_is_reverse_dependency_aware(self):
        radius = twin().change_radius(("auth",), max_depth=4, max_nodes=20)
        self.assertEqual(radius.affected, frozenset({"auth", "api", "ui", "tests"})); self.assertFalse(radius.truncated)

    def test_depth_limited_change_radius_marks_truncation(self):
        radius = twin().change_radius(("auth",), max_depth=1, max_nodes=20)
        self.assertTrue(radius.truncated); self.assertEqual(radius.affected, frozenset({"auth", "api", "tests"}))

    def test_change_radius_bound_fails_closed(self):
        with self.assertRaises(ValueError): self.build(policy=PlanningPolicy(max_change_radius=1, change_radius_depth=4))

    def test_master_fingerprint_is_stable(self):
        self.assertEqual(self.build().fingerprint(), self.build().fingerprint())

    def test_semantic_assumption_change_changes_master_fingerprint(self):
        first = self.build()
        changed = proposal((Assumption("a1", "different verified fact", ConfidenceLevel.VERIFIED, True, ("repo-map",)),))
        self.assertNotEqual(first.fingerprint(), self.build(prop=changed).fingerprint())


class PlanCompilerTests(unittest.TestCase):
    def test_master_plan_compiles_only_supported_task_node_types(self):
        master = MasterPlannerTests().build(); task_plan = PlanGraphCompiler(authority(), twin()).compile(master)
        self.assertEqual([n.action for n in task_plan.nodes], [ActionKind.MODEL_PROMPT, ActionKind.MODEL_PROMPT, ActionKind.SKILL])

    def test_forged_master_plan_cannot_compile(self):
        master = MasterPlannerTests().build()
        forged = replace(master, steps=(replace(master.steps[0], instruction="Do something else"), *master.steps[1:]))
        with self.assertRaises(PermissionError): PlanGraphCompiler(authority(), twin()).compile(forged)

    def test_unsealed_master_plan_cannot_compile(self):
        master = MasterPlannerTests().build()
        with self.assertRaises(PermissionError): PlanGraphCompiler(authority(), twin()).compile(replace(master, approval_tag=""))

    def test_changed_digital_twin_invalidates_compilation(self):
        master = MasterPlannerTests().build()
        with self.assertRaises(ValueError): PlanGraphCompiler(authority(), changed_twin()).compile(master)


class StopIntelligenceTests(unittest.TestCase):
    def setUp(self): self.subject = "1" * 64
    def record(self, evidence_id, kind, source="ci", subject=None):
        return EvidenceRecord(evidence_id, kind, source, hashlib.sha256(evidence_id.encode()).hexdigest(), subject or self.subject)
    def graph(self): return EvidenceGraph(self.subject, lambda record: record.source in {"ci", "security-gate", "heds"})

    def test_evidence_producer_cannot_self_mark_trust(self):
        graph = self.graph(); graph.add(self.record("claim", EvidenceKind.TEST, source="model-output"), requirement_indexes=(0,1), constraint_indexes=(0,), stop_conditions=("tests-green",))
        decision = StopIntelligence().evaluate(objective(), graph)
        self.assertFalse(decision.complete); self.assertEqual(decision.missing_acceptance, (0,1)); self.assertEqual(decision.missing_constraints, (0,))

    def test_evidence_from_different_plan_is_rejected(self):
        with self.assertRaises(ValueError): self.graph().add(self.record("old", EvidenceKind.TEST, subject="2"*64), requirement_indexes=(0,))

    def test_constraint_requires_trusted_completion_evidence(self):
        graph = self.graph()
        graph.add(self.record("t", EvidenceKind.TEST), requirement_indexes=(0,1), stop_conditions=("tests-green",))
        graph.add(self.record("s", EvidenceKind.SECURITY, "security-gate"), stop_conditions=("security-reviewed",))
        graph.add(self.record("r", EvidenceKind.REVIEW, "heds"), stop_conditions=("security-reviewed",))
        decision = StopIntelligence().evaluate(objective(), graph)
        self.assertFalse(decision.complete); self.assertEqual(decision.missing_constraints, (0,))

    def test_stop_requires_every_required_evidence_kind_and_constraint(self):
        graph = self.graph()
        graph.add(self.record("t", EvidenceKind.TEST), requirement_indexes=(0,1), stop_conditions=("tests-green",))
        graph.add(self.record("s", EvidenceKind.SECURITY, "security-gate"), constraint_indexes=(0,), stop_conditions=("security-reviewed",))
        self.assertFalse(StopIntelligence().evaluate(objective(), graph).complete)
        graph.add(self.record("r", EvidenceKind.REVIEW, "heds"), stop_conditions=("security-reviewed",))
        self.assertTrue(StopIntelligence().evaluate(objective(), graph).complete)

    def test_invalid_link_fails_atomically(self):
        graph = self.graph(); record = self.record("x", EvidenceKind.TEST)
        with self.assertRaises(ValueError): graph.add(record, constraint_indexes=(-1,))
        graph.add(record, constraint_indexes=(0,)); self.assertEqual(len(graph.trusted_for_constraint(0)), 1)

    def test_duplicate_evidence_id_rejected(self):
        graph = self.graph(); record = self.record("x", EvidenceKind.TEST); graph.add(record)
        with self.assertRaises(ValueError): graph.add(record)


class CorrectionAndOrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.auth = authority(); self.twin = twin(); self.master = MasterPlannerTests().build(); self.obj = objective()
    def ledger(self, **kwargs): return SelfCorrectionLedger(self.master, self.auth, self.twin, **kwargs)
    def orchestrator(self): return AgentOrchestrator(self.master, self.obj, self.auth, self.twin)

    def test_self_correction_cannot_expand_change_scope(self):
        with self.assertRaises(PermissionError): self.ledger().request("implement", "test_failed", ("ui",))

    def test_self_correction_is_bounded(self):
        ledger = self.ledger(max_total=2, max_per_step=1); ledger.request("implement", "test_failed", ("auth",))
        with self.assertRaises(RuntimeError): ledger.request("implement", "test_failed_again", ("auth",))

    def test_forged_master_plan_cannot_open_correction_ledger(self):
        with self.assertRaises(PermissionError): SelfCorrectionLedger(replace(self.master, approval_tag="0"*64), self.auth, self.twin)

    def test_changed_digital_twin_blocks_orchestrator(self):
        with self.assertRaises(ValueError): AgentOrchestrator(self.master, self.obj, self.auth, changed_twin())

    def snapshot(self, orchestrator, node_status):
        plan = orchestrator.task_plan(); status_map = dict(node_status)
        attempts = tuple((step.step_id, 1 if status_map[step.step_id] is NodeStatus.SUCCEEDED else 0) for step in self.master.steps)
        executions = sum(1 for value in status_map.values() if value is NodeStatus.SUCCEEDED)
        return TaskSnapshot("task", plan.fingerprint(), TaskStatus.PENDING, node_status, attempts, TaskBudget(20,5), executions, 0, 0, tuple())

    def full_evidence(self):
        subject = self.master.fingerprint(); graph = EvidenceGraph(subject, lambda record: record.source in {"ci", "security-gate", "heds"})
        graph.add(EvidenceRecord("tests", EvidenceKind.TEST, "ci", hashlib.sha256(b"tests").hexdigest(), subject), requirement_indexes=(0,1), stop_conditions=("tests-green",))
        graph.add(EvidenceRecord("security", EvidenceKind.SECURITY, "security-gate", hashlib.sha256(b"security").hexdigest(), subject), constraint_indexes=(0,), stop_conditions=("security-reviewed",))
        graph.add(EvidenceRecord("review", EvidenceKind.REVIEW, "heds", hashlib.sha256(b"review").hexdigest(), subject), stop_conditions=("security-reviewed",))
        return graph

    def test_complete_evidence_cannot_finish_incomplete_runtime(self):
        orchestrator = self.orchestrator(); nodes = (("design",NodeStatus.SUCCEEDED),("implement",NodeStatus.SUCCEEDED),("verify",NodeStatus.PENDING))
        telemetry = orchestrator.telemetry(self.snapshot(orchestrator,nodes), self.full_evidence(), self.ledger())
        self.assertEqual(telemetry.progress_percent, 66.67); self.assertFalse(telemetry.stop_complete)

    def test_runtime_and_evidence_together_satisfy_stop(self):
        orchestrator = self.orchestrator(); nodes = tuple((step.step_id,NodeStatus.SUCCEEDED) for step in self.master.steps)
        telemetry = orchestrator.telemetry(self.snapshot(orchestrator,nodes), self.full_evidence(), self.ledger())
        self.assertEqual(telemetry.progress_percent, 100.0); self.assertTrue(telemetry.stop_complete)

    def test_snapshot_fingerprint_mismatch_fails_closed(self):
        orchestrator = self.orchestrator(); nodes = tuple((step.step_id,NodeStatus.PENDING) for step in self.master.steps)
        snap = TaskSnapshot("task", "0"*64, TaskStatus.PENDING, nodes, tuple((step.step_id,0) for step in self.master.steps), TaskBudget(20,5), 0,0,0,tuple())
        with self.assertRaises(ValueError): orchestrator.telemetry(snap, self.full_evidence(), self.ledger())

    def test_evidence_graph_for_other_plan_fails_closed(self):
        orchestrator = self.orchestrator(); nodes = tuple((step.step_id,NodeStatus.PENDING) for step in self.master.steps)
        with self.assertRaises(ValueError): orchestrator.telemetry(self.snapshot(orchestrator,nodes), EvidenceGraph("2"*64, lambda _r: True), self.ledger())

    def test_forged_master_plan_cannot_create_orchestrator(self):
        with self.assertRaises(PermissionError): AgentOrchestrator(replace(self.master, approval_tag="0"*64), self.obj, self.auth, self.twin)


if __name__ == "__main__": unittest.main()
