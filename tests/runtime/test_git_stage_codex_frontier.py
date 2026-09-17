from __future__ import annotations

import unittest

from hive_runtime.git_stage_codex_frontier import FROZEN_FRONTIER, PRE_CODEX_FRONTIER_CONTRACT


class GitStageCodexFrontierTests(unittest.TestCase):
    def test_frontier_records_authority_without_holding_it(self) -> None:
        self.assertEqual(FROZEN_FRONTIER.contract, PRE_CODEX_FRONTIER_CONTRACT)
        self.assertEqual(FROZEN_FRONTIER.action, "git_stage_paths_v1")
        self.assertEqual(FROZEN_FRONTIER.capability, "git.write")
        self.assertTrue(FROZEN_FRONTIER.authority_late_binding)
        # Mutation is now reachable through the governed capability, and this
        # module itself still grants nothing.
        self.assertTrue(FROZEN_FRONTIER.public_mutation_enabled)
        self.assertFalse(FROZEN_FRONTIER.shell_process_allowed)
        self.assertFalse(FROZEN_FRONTIER.hooks_filters_allowed)
        self.assertFalse(FROZEN_FRONTIER.network_credentials_allowed)

    def test_pre_codex_seam_list_is_preserved_and_completion_is_reported(self) -> None:
        seams = FROZEN_FRONTIER.pre_codex_seams()
        self.assertEqual(len(seams), 11)
        self.assertEqual(len(seams), len(set(seams)))
        self.assertIn("prove_and_pin_index_codec_backend", seams)
        self.assertIn("add_dedicated_git_write_control_plane_capability", seams)
        self.assertIn("prove_native_windows_linux_macos_e2e", seams)
        self.assertIn("complete_evidence_ledger_and_heds", seams)

        completed = FROZEN_FRONTIER.completed_seams()
        remaining = FROZEN_FRONTIER.remaining_seams()
        self.assertEqual(set(completed) | set(remaining), set(seams))
        self.assertEqual(set(completed) & set(remaining), set())
        # Every implementation seam is complete; only the independent promotion
        # review remains, and that is not an implementation seam.
        self.assertEqual(remaining, ("complete_evidence_ledger_and_heds",))
        self.assertEqual(len(completed), 10)

    def test_frontier_cannot_mint_permit_or_publish(self) -> None:
        self.assertFalse(hasattr(FROZEN_FRONTIER, "mint_permit"))
        self.assertFalse(hasattr(FROZEN_FRONTIER, "publish"))
        self.assertFalse(hasattr(FROZEN_FRONTIER, "stage_paths"))


if __name__ == "__main__":
    unittest.main()
