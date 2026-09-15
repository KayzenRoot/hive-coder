"""Expert-grade Hive planning and orchestration primitives.

LLM/planner/council output is proposal data only. Deterministic validation,
trusted evidence and existing Hive authority boundaries decide what may execute.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Protocol

from .agent_tasks import ActionKind, TaskNode, TaskPlan, TaskSnapshot, NodeStatus

_SAFE_ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,128}$")
_SAFE_CODE = re.compile(r"^[a-zA-Z0-9_.:-]{1,80}$")


class ConfidenceLevel(str, Enum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class RiskTier(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    ELEVATED = "elevated"
    HIGH_ASSURANCE = "high_assurance"


class AgentRole(str, Enum):
    PLANNER = "planner"
    ARCHITECT = "architect"
    BACKEND = "backend"
    FRONTEND = "frontend"
    DATA = "data"
    SECURITY = "security"
    QA = "qa"
    PERFORMANCE = "performance"
    DEVOPS = "devops"
    REVIEWER = "reviewer"
    DOCUMENTATION = "documentation"


class FindingSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceKind(str, Enum):
    TEST = "test"
    BUILD = "build"
    STATIC_ANALYSIS = "static_analysis"
    REVIEW = "review"
    RUNTIME = "runtime"
    REQUIREMENT = "requirement"
    SECURITY = "security"


@dataclass(frozen=True)
class StopCondition:
    condition_id: str
    description: str
    required_evidence: frozenset[EvidenceKind]

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.condition_id):
            raise ValueError("invalid stop condition id")
        if not self.description.strip() or not self.required_evidence:
            raise ValueError("stop condition requires description and evidence")


@dataclass(frozen=True)
class ObjectiveSpec:
    objective_id: str
    objective: str
    risk: RiskTier
    constraints: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    stop_conditions: tuple[StopCondition, ...]

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.objective_id) or not self.objective.strip():
            raise ValueError("invalid objective")
        if not self.acceptance_criteria or not self.stop_conditions:
            raise ValueError("objective requires acceptance criteria and stop conditions")
        if any(not item.strip() for item in self.constraints + self.acceptance_criteria):
            raise ValueError("objective text fields cannot be empty")
        ids = [item.condition_id for item in self.stop_conditions]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate stop condition")
        for condition in self.stop_conditions:
            condition.validate()

    def fingerprint(self) -> str:
        self.validate()
        payload = {
            "objective_id": self.objective_id,
            "objective": self.objective,
            "risk": self.risk.value,
            "constraints": list(self.constraints),
            "acceptance_criteria": list(self.acceptance_criteria),
            "stop_conditions": [
                {
                    "id": item.condition_id,
                    "description": item.description,
                    "required_evidence": sorted(kind.value for kind in item.required_evidence),
                }
                for item in self.stop_conditions
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    statement: str
    confidence: ConfidenceLevel
    critical: bool = False
    evidence_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.assumption_id) or not self.statement.strip():
            raise ValueError("invalid assumption")
        if self.confidence is ConfidenceLevel.VERIFIED and not self.evidence_refs:
            raise ValueError("verified assumption requires evidence reference")


@dataclass(frozen=True)
class DigitalTwinNode:
    node_id: str
    kind: str
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class ChangeRadius:
    targets: frozenset[str]
    affected: frozenset[str]
    truncated: bool


class ProjectDigitalTwin:
    """Descriptive dependency map. It never grants execution authority."""

    def __init__(self, nodes: Iterable[DigitalTwinNode]) -> None:
        self._nodes: dict[str, DigitalTwinNode] = {}
        for node in nodes:
            if not _SAFE_ID.fullmatch(node.node_id) or not node.kind.strip():
                raise ValueError("invalid digital twin node")
            if node.node_id in self._nodes:
                raise ValueError("duplicate digital twin node")
            self._nodes[node.node_id] = node
        known = set(self._nodes)
        if any(not set(node.depends_on).issubset(known) for node in self._nodes.values()):
            raise ValueError("digital twin contains unknown dependency")

    def change_radius(self, targets: Iterable[str], *, max_depth: int = 4, max_nodes: int = 200) -> ChangeRadius:
        roots = frozenset(targets)
        if not roots or not roots.issubset(self._nodes):
            raise ValueError("change target not present in digital twin")
        if not 0 <= max_depth <= 20 or not 1 <= max_nodes <= 10_000:
            raise ValueError("invalid change-radius bounds")
        reverse: dict[str, set[str]] = {key: set() for key in self._nodes}
        for node in self._nodes.values():
            for dep in node.depends_on:
                reverse[dep].add(node.node_id)
        affected = set(roots)
        frontier = set(roots)
        truncated = False
        for _ in range(max_depth):
            nxt: set[str] = set()
            for current in sorted(frontier):
                nxt.update(reverse[current])
            nxt -= affected
            if not nxt:
                break
            for item in sorted(nxt):
                if len(affected) >= max_nodes:
                    truncated = True
                    break
                affected.add(item)
            if truncated:
                break
            frontier = nxt
        return ChangeRadius(roots, frozenset(affected), truncated)


@dataclass(frozen=True)
class PlanStep:
    step_id: str
    title: str
    role: AgentRole
    action: ActionKind
    depends_on: tuple[str, ...] = ()
    requirement_indexes: frozenset[int] = frozenset()
    change_targets: frozenset[str] = frozenset()
    required_model_capabilities: frozenset[str] = frozenset()
    provider: str | None = None
    instruction: str | None = None
    skill_id: str | None = None
    skill_version: str | None = None
    max_attempts: int = 1

    def validate(self, acceptance_count: int) -> None:
        if not _SAFE_ID.fullmatch(self.step_id) or not self.title.strip():
            raise ValueError("invalid plan step")
        if any(index < 0 or index >= acceptance_count for index in self.requirement_indexes):
            raise ValueError("plan step references unknown acceptance criterion")
        if self.action is ActionKind.MODEL_PROMPT:
            if not self.instruction or not self.instruction.strip():
                raise ValueError("model step requires instruction")
            if self.skill_id is not None or self.skill_version is not None:
                raise ValueError("model step cannot declare a skill")
        elif self.action is ActionKind.SKILL:
            if not self.skill_id or not self.skill_version:
                raise ValueError("skill step requires id/version")
            if self.instruction is not None or self.required_model_capabilities or self.provider is not None:
                raise ValueError("skill step cannot carry model fields")
        else:
            raise ValueError("unsupported plan action")
        if not 1 <= self.max_attempts <= 20:
            raise ValueError("invalid step attempt budget")


@dataclass(frozen=True)
class DeepPlanProposal:
    assumptions: tuple[Assumption, ...]
    steps: tuple[PlanStep, ...]


@dataclass(frozen=True)
class CouncilFinding:
    reviewer: AgentRole
    severity: FindingSeverity
    code: str
    target_step: str | None = None

    def validate(self) -> None:
        if self.reviewer in {AgentRole.PLANNER, AgentRole.BACKEND, AgentRole.FRONTEND, AgentRole.DATA,
                             AgentRole.PERFORMANCE, AgentRole.DEVOPS, AgentRole.DOCUMENTATION}:
            # These specialists may participate later, but the approval council in
            # this increment is deliberately restricted to independent review roles.
            raise ValueError("reviewer role is not an approval-council role")
        if not _SAFE_CODE.fullmatch(self.code):
            raise ValueError("invalid finding code")
        if self.target_step is not None and not _SAFE_ID.fullmatch(self.target_step):
            raise ValueError("invalid finding target")


class PlannerPort(Protocol):
    def __call__(self, objective: ObjectiveSpec, twin: ProjectDigitalTwin) -> DeepPlanProposal: ...


class CouncilPort(Protocol):
    def __call__(self, objective: ObjectiveSpec, proposal: DeepPlanProposal) -> Iterable[CouncilFinding]: ...


@dataclass(frozen=True)
class PlanningPolicy:
    required_council_roles: frozenset[AgentRole] = frozenset({AgentRole.ARCHITECT, AgentRole.SECURITY, AgentRole.QA, AgentRole.REVIEWER})
    max_change_radius: int = 200
    change_radius_depth: int = 4


@dataclass(frozen=True)
class MasterPlan:
    objective_fingerprint: str
    steps: tuple[PlanStep, ...]
    assumptions: tuple[Assumption, ...]
    council_findings: tuple[CouncilFinding, ...]
    change_radius: ChangeRadius

    def fingerprint(self) -> str:
        payload = {
            "objective": self.objective_fingerprint,
            "steps": [
                {
                    "id": step.step_id,
                    "role": step.role.value,
                    "action": step.action.value,
                    "deps": list(step.depends_on),
                    "requirements": sorted(step.requirement_indexes),
                    "targets": sorted(step.change_targets),
                    "capabilities": sorted(step.required_model_capabilities),
                    "provider": step.provider,
                    "instruction_sha256": hashlib.sha256((step.instruction or "").encode()).hexdigest(),
                    "skill_id": step.skill_id,
                    "skill_version": step.skill_version,
                    "max_attempts": step.max_attempts,
                }
                for step in self.steps
            ],
            "assumptions": [
                {"id": a.assumption_id, "confidence": a.confidence.value, "critical": a.critical, "refs": list(a.evidence_refs)}
                for a in self.assumptions
            ],
            "findings": [
                {"reviewer": f.reviewer.value, "severity": f.severity.value, "code": f.code, "target": f.target_step}
                for f in self.council_findings
            ],
            "radius": sorted(self.change_radius.affected),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


class DeepPlanEngine:
    """Deterministic approval shell around high-intelligence planning ports."""

    def __init__(self, policy: PlanningPolicy = PlanningPolicy()) -> None:
        self.policy = policy

    def build(self, objective: ObjectiveSpec, *, twin: ProjectDigitalTwin, planner: PlannerPort, council: CouncilPort) -> MasterPlan:
        objective.validate()
        proposal = planner(objective, twin)
        if not isinstance(proposal, DeepPlanProposal):
            raise TypeError("planner returned invalid proposal type")
        self._validate_proposal(objective, proposal, twin)
        findings = tuple(council(objective, proposal))
        self._validate_council(proposal, findings)
        targets = frozenset(target for step in proposal.steps for target in step.change_targets)
        radius = twin.change_radius(targets, max_depth=self.policy.change_radius_depth, max_nodes=self.policy.max_change_radius)
        if radius.truncated:
            raise ValueError("change radius exceeded planning bound")
        return MasterPlan(objective.fingerprint(), proposal.steps, proposal.assumptions, findings, radius)

    def _validate_proposal(self, objective: ObjectiveSpec, proposal: DeepPlanProposal, twin: ProjectDigitalTwin) -> None:
        if not proposal.steps:
            raise ValueError("planner produced empty plan")
        for assumption in proposal.assumptions:
            assumption.validate()
            if assumption.critical and assumption.confidence is ConfidenceLevel.UNKNOWN:
                raise ValueError("critical UNKNOWN assumption blocks planning")
            if objective.risk is RiskTier.HIGH_ASSURANCE and assumption.critical and assumption.confidence is not ConfidenceLevel.VERIFIED:
                raise ValueError("HIGH_ASSURANCE critical assumption must be VERIFIED")
        ids = [step.step_id for step in proposal.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate plan step")
        known = set(ids)
        covered: set[int] = set()
        for step in proposal.steps:
            step.validate(len(objective.acceptance_criteria))
            if not set(step.depends_on).issubset(known) or step.step_id in step.depends_on:
                raise ValueError("invalid plan dependency")
            if not step.change_targets:
                raise ValueError("every plan step requires explicit change target")
            twin.change_radius(step.change_targets, max_depth=0, max_nodes=self.policy.max_change_radius)
            covered.update(step.requirement_indexes)
        if covered != set(range(len(objective.acceptance_criteria))):
            raise ValueError("plan does not cover every acceptance criterion")
        graph = {step.step_id: step.depends_on for step in proposal.steps}
        visiting: set[str] = set(); visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise ValueError("plan graph contains dependency cycle")
            visiting.add(node)
            for dep in graph[node]:
                visit(dep)
            visiting.remove(node); visited.add(node)
        for node in ids:
            visit(node)

    def _validate_council(self, proposal: DeepPlanProposal, findings: tuple[CouncilFinding, ...]) -> None:
        roles: set[AgentRole] = set()
        known_steps = {step.step_id for step in proposal.steps}
        for finding in findings:
            finding.validate()
            roles.add(finding.reviewer)
            if finding.target_step is not None and finding.target_step not in known_steps:
                raise ValueError("council finding references unknown step")
            if finding.severity in {FindingSeverity.HIGH, FindingSeverity.CRITICAL}:
                raise ValueError(f"blocking council finding: {finding.code}")
        if not self.policy.required_council_roles.issubset(roles):
            raise ValueError("required independent council roles did not review plan")


class PlanGraphCompiler:
    def compile(self, master: MasterPlan) -> TaskPlan:
        nodes = []
        for step in master.steps:
            nodes.append(TaskNode(
                node_id=step.step_id,
                action=step.action,
                depends_on=step.depends_on,
                required_model_capabilities=step.required_model_capabilities,
                provider=step.provider,
                prompt=step.instruction,
                skill_id=step.skill_id,
                skill_version=step.skill_version,
                max_attempts=step.max_attempts,
            ))
        plan = TaskPlan(tuple(nodes))
        plan.validate()
        return plan


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    kind: EvidenceKind
    source: str
    digest: str
    trusted: bool

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.evidence_id) or not self.source.strip():
            raise ValueError("invalid evidence record")
        if not re.fullmatch(r"[0-9a-f]{64}", self.digest):
            raise ValueError("evidence digest must be sha256 hex")


class EvidenceGraph:
    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}
        self._requirements: dict[int, set[str]] = {}
        self._stops: dict[str, set[str]] = {}

    def add(self, record: EvidenceRecord, *, requirement_indexes: Iterable[int] = (), stop_conditions: Iterable[str] = ()) -> None:
        record.validate()
        if record.evidence_id in self._records:
            raise ValueError("duplicate evidence id")
        self._records[record.evidence_id] = record
        for index in requirement_indexes:
            if index < 0:
                raise ValueError("invalid requirement index")
            self._requirements.setdefault(index, set()).add(record.evidence_id)
        for condition in stop_conditions:
            if not _SAFE_ID.fullmatch(condition):
                raise ValueError("invalid stop condition id")
            self._stops.setdefault(condition, set()).add(record.evidence_id)

    def trusted_for_requirement(self, index: int) -> tuple[EvidenceRecord, ...]:
        return tuple(self._records[item] for item in sorted(self._requirements.get(index, ())) if self._records[item].trusted)

    def trusted_for_stop(self, condition_id: str) -> tuple[EvidenceRecord, ...]:
        return tuple(self._records[item] for item in sorted(self._stops.get(condition_id, ())) if self._records[item].trusted)


@dataclass(frozen=True)
class StopDecision:
    complete: bool
    missing_acceptance: tuple[int, ...]
    missing_conditions: tuple[str, ...]


class StopIntelligence:
    """Evidence-based STOP evaluator. Agent/model assertions are not evidence."""

    def evaluate(self, objective: ObjectiveSpec, evidence: EvidenceGraph) -> StopDecision:
        objective.validate()
        missing_acceptance = tuple(index for index in range(len(objective.acceptance_criteria)) if not evidence.trusted_for_requirement(index))
        missing_conditions = []
        for condition in objective.stop_conditions:
            kinds = {record.kind for record in evidence.trusted_for_stop(condition.condition_id)}
            if not condition.required_evidence.issubset(kinds):
                missing_conditions.append(condition.condition_id)
        return StopDecision(not missing_acceptance and not missing_conditions, missing_acceptance, tuple(missing_conditions))


@dataclass(frozen=True)
class CorrectionEntry:
    sequence: int
    step_id: str
    reason_code: str
    targets: frozenset[str]


class SelfCorrectionLedger:
    """Bounded correction requests that cannot broaden the approved change scope."""

    def __init__(self, master: MasterPlan, *, max_total: int = 12, max_per_step: int = 3) -> None:
        if not 0 <= max_total <= 100 or not 0 <= max_per_step <= 20:
            raise ValueError("invalid correction bounds")
        self.master = master; self.max_total = max_total; self.max_per_step = max_per_step
        self._entries: list[CorrectionEntry] = []
        self._allowed = {step.step_id: step.change_targets for step in master.steps}

    def request(self, step_id: str, reason_code: str, targets: Iterable[str]) -> CorrectionEntry:
        if step_id not in self._allowed or not _SAFE_CODE.fullmatch(reason_code):
            raise ValueError("invalid correction request")
        requested = frozenset(targets)
        if not requested or not requested.issubset(self._allowed[step_id]):
            raise PermissionError("self-correction cannot expand approved change scope")
        if len(self._entries) >= self.max_total:
            raise RuntimeError("global correction budget exhausted")
        if sum(1 for item in self._entries if item.step_id == step_id) >= self.max_per_step:
            raise RuntimeError("step correction budget exhausted")
        entry = CorrectionEntry(len(self._entries) + 1, step_id, reason_code, requested)
        self._entries.append(entry)
        return entry

    def entries(self) -> tuple[CorrectionEntry, ...]:
        return tuple(self._entries)


@dataclass(frozen=True)
class OrchestratorTelemetry:
    completed_steps: int
    total_steps: int
    progress_percent: float
    correction_count: int
    unknown_assumptions: int
    stop_complete: bool


class AgentOrchestrator:
    """Compiles approved intelligence into CP-0009 execution and evidence telemetry."""

    def __init__(self, master: MasterPlan, objective: ObjectiveSpec) -> None:
        if master.objective_fingerprint != objective.fingerprint():
            raise ValueError("master plan/objective mismatch")
        self.master = master; self.objective = objective

    def task_plan(self) -> TaskPlan:
        return PlanGraphCompiler().compile(self.master)

    def telemetry(self, snapshot: TaskSnapshot, evidence: EvidenceGraph, corrections: SelfCorrectionLedger) -> OrchestratorTelemetry:
        step_ids = {step.step_id for step in self.master.steps}
        state = dict(snapshot.node_status)
        if set(state) != step_ids:
            raise ValueError("task snapshot does not match master plan")
        completed = sum(1 for value in state.values() if value is NodeStatus.SUCCEEDED)
        stop = StopIntelligence().evaluate(self.objective, evidence)
        unknown = sum(1 for item in self.master.assumptions if item.confidence is ConfidenceLevel.UNKNOWN)
        return OrchestratorTelemetry(
            completed,
            len(step_ids),
            round((completed / len(step_ids)) * 100.0, 2),
            len(corrections.entries()),
            unknown,
            stop.complete,
        )
