"""Compatibility smoke tests for the public expert-agent facade.

Detailed WO-0011 coverage is split across the expert identity, context,
evaluation and mesh hardening suites so each trust boundary is independently
reviewable.
"""
import unittest

import hive_runtime.expert_agents as expert_agents


class ExpertAgentFacadeTests(unittest.TestCase):
    def test_public_facade_exposes_core_contracts(self):
        required = {
            "AgentProfileAuthority",
            "ContextLens",
            "CodeTruthMap",
            "ArchitecturalGenome",
            "ExperienceLedger",
            "ExperienceRouter",
            "AgentMesh",
            "AdversarialChallengeEngine",
        }
        self.assertTrue(required.issubset(set(expert_agents.__all__)))


if __name__ == "__main__":
    unittest.main()
