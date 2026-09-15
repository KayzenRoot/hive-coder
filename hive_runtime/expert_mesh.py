"""Measured AgentMesh assignment and bounded adversarial challenge contracts."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Mapping, Protocol
from .orchestration import AgentRole, FindingSeverity, MasterPlan, PlanApprovalAuthority, ProjectDigitalTwin
from .expert_common import _SAFE_ID, _SAFE_TOKEN, ChallengeKind
from .expert_identity import AgentProfile, AgentProfileAuthority, ExpertAgentRegistry
from .expert_evaluation import CompetenceReport, CompetenceStandard, ExperienceRouter

@dataclass(frozen=True)
class AgentAssignment:
    step_id: str
    agent_id: str
    profile_fingerprint: str
    capsule_fingerprint: str
    competence_fingerprint: str
    independence_key: str


class AgentMesh:
    """Binds sealed MasterPlan steps to measured specialist profiles."""

    OVERSIGHT_ROLES = frozenset({AgentRole.SECURITY, AgentRole.QA, AgentRole.REVIEWER})

    def __init__(self, approval_authority: PlanApprovalAuthority, twin: ProjectDigitalTwin,
                 registry: ExpertAgentRegistry, router: ExperienceRouter,
                 standards: Mapping[AgentRole, CompetenceStandard]) -> None:
        self.approval_authority = approval_authority
        self.twin = twin
        self.registry = registry
        self.router = router
        self.standards = dict(standards)

    def assign(self, master: MasterPlan) -> tuple[AgentAssignment, ...]:
        if not self.approval_authority.verify(master):
            raise PermissionError("master plan approval seal invalid")
        if master.twin_fingerprint != self.twin.fingerprint():
            raise ValueError("project digital twin changed after master plan approval")
        capsules = self.registry.capsules()
        routed: list[tuple[object, AgentProfile, CompetenceReport]] = []
        for step in master.steps:
            standard = self.standards.get(step.role)
            if standard is None:
                raise LookupError(f"no competence standard configured for role {step.role.value}")
            eligible = tuple(
                profile for profile in self.registry.profiles_for(step.role)
                if step.required_model_capabilities.issubset(profile.required_model_capabilities)
            )
            if not eligible:
                raise LookupError(f"no specialist profile satisfies step capabilities: {step.step_id}")
            profile, report = self.router.route(eligible, capsules, step.role, standard)
            routed.append((step, profile, report))

        implementation_lineages = {
            profile.independence_key for step, profile, _report in routed
            if step.role not in self.OVERSIGHT_ROLES
        }
        oversight_lineages = [
            profile.independence_key for step, profile, _report in routed
            if step.role in self.OVERSIGHT_ROLES
        ]
        if implementation_lineages & set(oversight_lineages):
            raise PermissionError("oversight agent is not independent from implementation lineage")
        if len(oversight_lineages) != len(set(oversight_lineages)):
            raise PermissionError("oversight roles must use distinct independence lineages")

        return tuple(
            AgentAssignment(
                step.step_id, profile.agent_id, profile.fingerprint(), profile.capsule_fingerprint,
                report.fingerprint(), profile.independence_key,
            )
            for step, profile, report in routed
        )


@dataclass(frozen=True)
class ChallengeAssessment:
    severity: FindingSeverity
    code: str
    target_step: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not _SAFE_TOKEN.fullmatch(self.code):
            raise ValueError("invalid challenge code")
        if self.target_step is not None and not _SAFE_ID.fullmatch(self.target_step):
            raise ValueError("invalid challenge target")
        if any(not _SAFE_ID.fullmatch(ref) for ref in self.evidence_refs):
            raise ValueError("invalid challenge evidence reference")


@dataclass(frozen=True)
class ChallengeFinding:
    kind: ChallengeKind
    challenger_agent_id: str
    severity: FindingSeverity
    code: str
    target_step: str | None
    evidence_refs: tuple[str, ...]


class ChallengePort(Protocol):
    def __call__(self, master: MasterPlan) -> Iterable[ChallengeAssessment]: ...


@dataclass(frozen=True)
class ChallengeReport:
    findings: tuple[ChallengeFinding, ...]
    blocked: bool
    blocking_codes: tuple[str, ...]


@dataclass(frozen=True)
class ChallengePolicy:
    required_kinds: frozenset[ChallengeKind] = frozenset({ChallengeKind.COUNTERPLAN, ChallengeKind.FAILURE_ORACLE})
    blocking_severities: frozenset[FindingSeverity] = frozenset({FindingSeverity.MEDIUM, FindingSeverity.HIGH, FindingSeverity.CRITICAL})


class AdversarialChallengeEngine:
    """Runs measured, host-identified challengers. Findings grant no authority."""

    ALLOWED_ROLES: Mapping[ChallengeKind, frozenset[AgentRole]] = {
        ChallengeKind.COUNTERPLAN: frozenset({AgentRole.PLANNER, AgentRole.ARCHITECT, AgentRole.REVIEWER}),
        ChallengeKind.FAILURE_ORACLE: frozenset({AgentRole.ARCHITECT, AgentRole.SECURITY, AgentRole.QA, AgentRole.REVIEWER}),
    }

    def __init__(self, approval_authority: PlanApprovalAuthority, twin: ProjectDigitalTwin,
                 profile_authority: AgentProfileAuthority, registry: ExpertAgentRegistry,
                 router: ExperienceRouter, standards: Mapping[AgentRole, CompetenceStandard],
                 policy: ChallengePolicy = ChallengePolicy()) -> None:
        self.approval_authority = approval_authority
        self.twin = twin
        self.profile_authority = profile_authority
        self.registry = registry
        self.router = router
        self.standards = dict(standards)
        self.policy = policy

    def run(self, master: MasterPlan,
            challengers: Mapping[ChallengeKind, tuple[AgentProfile, ChallengePort]]) -> ChallengeReport:
        if not self.approval_authority.verify(master):
            raise PermissionError("master plan approval seal invalid")
        if master.twin_fingerprint != self.twin.fingerprint():
            raise ValueError("project digital twin changed after master plan approval")
        if not self.policy.required_kinds.issubset(challengers):
            raise ValueError("required adversarial challenge kind missing")
        known_steps = {step.step_id for step in master.steps}
        findings: list[ChallengeFinding] = []
        lineages: set[str] = set()
        for kind in sorted(self.policy.required_kinds, key=lambda item: item.value):
            profile, port = challengers[kind]
            if not self.profile_authority.verify(profile):
                raise PermissionError("challenger profile seal invalid")
            try:
                registered = self.registry.get_profile(profile.agent_id)
            except KeyError as exc:
                raise PermissionError("challenger profile is not registered") from exc
            if registered.fingerprint() != profile.fingerprint() or registered.profile_tag != profile.profile_tag:
                raise PermissionError("challenger profile does not match registered specialist")
            if profile.role not in self.ALLOWED_ROLES[kind]:
                raise PermissionError(f"role is not eligible for {kind.value} challenge")
            standard = self.standards.get(profile.role)
            if standard is None:
                raise LookupError("challenger role has no competence standard")
            competence = self.router.evaluate(profile, self.registry.capsule_for(profile), standard)
            if not competence.passed:
                raise PermissionError("challenger has not earned required measured competence")
            if profile.independence_key in lineages:
                raise PermissionError("adversarial challengers must be independence-separated")
            lineages.add(profile.independence_key)
            assessments = tuple(port(master))
            if not assessments:
                raise ValueError(f"challenge produced no assessment: {kind.value}")
            for assessment in assessments:
                if not isinstance(assessment, ChallengeAssessment):
                    raise TypeError("challenge port returned invalid assessment")
                assessment.validate()
                if assessment.target_step is not None and assessment.target_step not in known_steps:
                    raise ValueError("challenge references unknown step")
                findings.append(ChallengeFinding(
                    kind, profile.agent_id, assessment.severity, assessment.code,
                    assessment.target_step, assessment.evidence_refs,
                ))
        blocking = tuple(sorted({item.code for item in findings if item.severity in self.policy.blocking_severities}))
        return ChallengeReport(tuple(findings), bool(blocking), blocking)
