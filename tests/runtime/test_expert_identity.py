from __future__ import annotations
from dataclasses import replace
from hive_runtime.expert_agents import AgentProfile, BenchmarkDimension, CompetenceLevel, distinguished_standard_for, required_dimensions_for_role
from hive_runtime.orchestration import AgentRole
from tests.runtime.expert_agent_fixture import ExpertAgentFixture, sha


class ExpertiseCapsuleTests(ExpertAgentFixture):
    def test_default_capsules_cover_every_specialist_role(self):
        self.assertEqual({capsule.role for capsule in self.capsules}, set(AgentRole))
        self.assertEqual(len({capsule.fingerprint() for capsule in self.capsules}), len(AgentRole))
        for capsule in self.capsules:
            self.assertGreaterEqual(len(capsule.principles), 4)
            self.assertGreaterEqual(len(capsule.anti_patterns), 4)
            self.assertTrue(required_dimensions_for_role(capsule.role).issubset(capsule.benchmark_dimensions))

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

    def test_execution_stack_change_invalidates_old_profile_seal(self):
        profile = self.profile(AgentRole.BACKEND, "backend-a", stack="stack-v1")
        tampered = replace(profile, execution_stack_digest=sha("stack-v2"))
        self.assertFalse(self.profile_authority.verify(tampered))

    def test_registry_rejects_unsealed_profile(self):
        capsule = self.by_role[AgentRole.BACKEND]
        unsealed = AgentProfile(
            "backend-a", AgentRole.BACKEND, capsule.fingerprint(),
            frozenset({"tool_calling", "structured_output"}), 64_000,
            "lineage-a", sha("stack"),
        )
        with self.assertRaises(PermissionError):
            self.registry(tuple()).add_profile(unsealed)
