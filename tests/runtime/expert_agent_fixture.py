from __future__ import annotations

import hashlib
import unittest

from hive_runtime.agent_tasks import ActionKind
from hive_runtime.expert_agents import (
    AgentProfile, AgentProfileAuthority, BenchmarkDimension, BenchmarkResult,
    CompetenceLevel, CompetenceStandard, ExperienceLedger, ExpertAgentRegistry,
    build_default_expertise_capsules, required_dimensions_for_role,
)
from hive_runtime.orchestration import (
    AgentRole, ChangeRadius, DigitalTwinNode, MasterPlan,
    PlanApprovalAuthority, PlanStep, ProjectDigitalTwin,
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


def master(authority: PlanApprovalAuthority, current_twin: ProjectDigitalTwin | None = None,
           *, review_first: bool = False,
           backend_caps: frozenset[str] = frozenset({"tool_calling"})) -> MasterPlan:
    current_twin = current_twin or twin()
    impl = PlanStep(
        "impl", "Implement bounded change", AgentRole.BACKEND, ActionKind.MODEL_PROMPT,
        change_targets=frozenset({"api"}), required_model_capabilities=backend_caps,
        instruction="Implement the approved bounded change.", max_attempts=2,
    )
    review = PlanStep(
        "review", "Review bounded change", AgentRole.REVIEWER, ActionKind.MODEL_PROMPT,
        depends_on=("impl",), change_targets=frozenset({"tests"}),
        required_model_capabilities=frozenset({"tool_calling"}),
        instruction="Review the approved change.",
    )
    steps = (review, impl) if review_first else (impl, review)
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

    def profile(self, role: AgentRole, agent_id: str, independence: str | None = None,
                *, stack: str | None = None,
                caps: frozenset[str] = frozenset({"tool_calling", "structured_output"})) -> AgentProfile:
        capsule = self.by_role[role]
        return self.profile_authority.seal(AgentProfile(
            agent_id, role, capsule.fingerprint(), caps, 64_000,
            independence or f"lineage.{agent_id}", sha(stack or f"stack:{agent_id}"),
        ))

    def registry(self, profiles: tuple[AgentProfile, ...]) -> ExpertAgentRegistry:
        registry = ExpertAgentRegistry(self.profile_authority)
        for capsule in self.capsules:
            registry.add_capsule(capsule)
        for profile in profiles:
            registry.add_profile(profile)
        return registry

    def standard(self, role: AgentRole) -> CompetenceStandard:
        return CompetenceStandard(
            CompetenceLevel.DISTINGUISHED, required_dimensions_for_role(role),
            40, 0.80, 2,
        )

    @staticmethod
    def ledger() -> ExperienceLedger:
        return ExperienceLedger(lambda result: result.result_id.startswith("trusted."))

    def add_results(self, ledger: ExperienceLedger, profile: AgentProfile,
                    dimensions: frozenset[BenchmarkDimension] | None = None,
                    *, successes: int = 20, total: int = 20, critical: int = 0,
                    policy: int = 0, tamper: int = 0, trusted: bool = True,
                    families: tuple[str, ...] = ("hive-fresh", "terminal-lab")) -> None:
        dimensions = dimensions or required_dimensions_for_role(profile.role)
        for dimension in dimensions:
            for index, family in enumerate(families):
                prefix = "trusted" if trusted else "claim"
                result_id = f"{prefix}.{profile.agent_id}.{dimension.value}.{index}"
                ledger.add(BenchmarkResult(
                    result_id, profile.agent_id, profile.fingerprint(), dimension,
                    family, f"{family}-suite", "1.0.0",
                    sha(f"samples:{profile.fingerprint()}:{dimension.value}:{family}:{index}"),
                    successes, total, critical, policy, tamper,
                    sha(f"evidence:{result_id}"),
                ))
