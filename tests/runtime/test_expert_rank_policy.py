from __future__ import annotations

from hive_runtime.expert_agents import (
    AgentMesh, CompetenceLevel, CompetenceStandard, ExperienceRouter,
    required_dimensions_for_role,
)
from hive_runtime.orchestration import AgentRole
from tests.runtime.expert_agent_fixture import ExpertAgentFixture, twin


class ExpertRankPolicyTests(ExpertAgentFixture):
    def test_agent_mesh_rejects_principal_standard_even_when_valid(self):
        backend = self.profile(AgentRole.BACKEND, "backend-principal")
        registry = self.registry((backend,))
        ledger = self.ledger()
        principal = CompetenceStandard(
            CompetenceLevel.PRINCIPAL,
            required_dimensions_for_role(AgentRole.BACKEND),
            30, 0.75, 2,
        )
        principal.validate()
        with self.assertRaises(ValueError):
            AgentMesh(
                self.plan_authority,
                twin(),
                registry,
                ExperienceRouter(self.profile_authority, ledger),
                {AgentRole.BACKEND: principal},
            )

    def test_fixture_distinguished_standard_meets_irreducible_floor(self):
        standard = self.standard(AgentRole.ARCHITECT)
        standard.validate()
        self.assertIs(standard.level, CompetenceLevel.DISTINGUISHED)
        self.assertGreaterEqual(standard.min_samples_per_dimension, 40)
        self.assertGreaterEqual(standard.min_lower_bound, 0.80)
        self.assertGreaterEqual(standard.min_independent_suites, 2)


if __name__ == "__main__":
    import unittest
    unittest.main()
