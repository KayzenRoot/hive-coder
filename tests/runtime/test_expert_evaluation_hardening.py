from __future__ import annotations
from hive_runtime.expert_agents import BenchmarkDimension, BenchmarkResult, ExperienceLedger, ExperienceRouter, required_dimensions_for_role
from hive_runtime.orchestration import AgentRole
from tests.runtime.expert_agent_fixture import ExpertAgentFixture, sha


class ExperienceRoutingTests(ExpertAgentFixture):
    def test_untrusted_benchmark_claims_do_not_count(self):
        ledger = self.ledger(); profile = self.profile(AgentRole.BACKEND, "backend-a")
        self.add_results(ledger, profile, trusted=False)
        report = ExperienceRouter(self.profile_authority, ledger).evaluate(
            profile, self.by_role[AgentRole.BACKEND], self.standard(AgentRole.BACKEND),
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("insufficient_samples" in code for code in report.blocking_codes))

    def test_old_benchmark_does_not_certify_changed_execution_stack(self):
        ledger = self.ledger()
        old = self.profile(AgentRole.BACKEND, "backend-a", stack="stack-v1")
        self.add_results(ledger, old)
        new = self.profile(AgentRole.BACKEND, "backend-a", stack="stack-v2")
        report = ExperienceRouter(self.profile_authority, ledger).evaluate(
            new, self.by_role[AgentRole.BACKEND], self.standard(AgentRole.BACKEND),
        )
        self.assertFalse(report.passed)
        self.assertTrue(all(score.samples == 0 for score in report.scores))

    def test_duplicate_trusted_sample_set_is_rejected(self):
        ledger = self.ledger(); profile = self.profile(AgentRole.BACKEND, "backend-a")
        dimension = BenchmarkDimension.DEBUGGING
        sample = sha("same-samples")
        first = BenchmarkResult("trusted.one", profile.agent_id, profile.fingerprint(), dimension,
                                "family-a", "suite-a", "1", sample, 10, 10, 0, 0, 0, sha("ev1"))
        second = BenchmarkResult("trusted.two", profile.agent_id, profile.fingerprint(), dimension,
                                 "family-b", "suite-b", "1", sample, 10, 10, 0, 0, 0, sha("ev2"))
        ledger.add(first)
        with self.assertRaises(ValueError):
            ledger.add(second)

    def test_two_versions_of_one_suite_family_do_not_fake_diversity(self):
        ledger = self.ledger(); profile = self.profile(AgentRole.BACKEND, "backend-a")
        for dim in required_dimensions_for_role(AgentRole.BACKEND):
            for index, version in enumerate(("1", "2")):
                result_id = f"trusted.{dim.value}.{version}"
                ledger.add(BenchmarkResult(
                    result_id, profile.agent_id, profile.fingerprint(), dim,
                    "same-family", f"suite-{version}", version,
                    sha(f"samples:{dim.value}:{index}"), 10, 10, 0, 0, 0,
                    sha(result_id),
                ))
        report = ExperienceRouter(self.profile_authority, ledger).evaluate(
            profile, self.by_role[AgentRole.BACKEND], self.standard(AgentRole.BACKEND),
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("suite_diversity" in code for code in report.blocking_codes))

    def test_critical_policy_or_tamper_incident_blocks_even_perfect_score(self):
        for incident in ("critical", "policy", "tamper"):
            ledger = self.ledger(); profile = self.profile(AgentRole.SECURITY, f"security-{incident}")
            kwargs = {"critical": 0, "policy": 0, "tamper": 0}; kwargs[incident] = 1
            self.add_results(ledger, profile, **kwargs)
            report = ExperienceRouter(self.profile_authority, ledger).evaluate(
                profile, self.by_role[AgentRole.SECURITY], self.standard(AgentRole.SECURITY),
            )
            self.assertFalse(report.passed)

    def test_router_prefers_stronger_confidence_adjusted_agent(self):
        ledger = self.ledger()
        weaker = self.profile(AgentRole.BACKEND, "backend-weaker")
        stronger = self.profile(AgentRole.BACKEND, "backend-stronger")
        self.add_results(ledger, weaker, successes=9, total=10)
        self.add_results(ledger, stronger, successes=20, total=20)
        registry = self.registry((weaker, stronger))
        profile, report = ExperienceRouter(self.profile_authority, ledger).route(
            registry.profiles_for(AgentRole.BACKEND), registry.capsules(), AgentRole.BACKEND,
            self.standard(AgentRole.BACKEND, min_samples=10, lower=0.5),
        )
        self.assertEqual(profile.agent_id, "backend-stronger")
        self.assertTrue(report.passed)

    def test_wilson_lower_bound_penalizes_small_perfect_samples(self):
        self.assertLess(ExperienceLedger.wilson_lower_bound(5, 5),
                        ExperienceLedger.wilson_lower_bound(50, 50))
