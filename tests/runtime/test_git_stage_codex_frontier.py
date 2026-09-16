from __future__ import annotations

import unittest

from hive_runtime.git_stage_codex_frontier import FROZEN_FRONTIER, PRE_CODEX_FRONTIER_CONTRACT


class GitStageCodexFrontierTests(unittest.TestCase):
    def test_frontier_is_complete_but_non_authoritative(self) -> None:
        self.assertEqual(FROZEN_FRONTIER.contract, PRE_CODEX_FRONTIER_CONTRACT)
        self.assertEqual(FROZEN_FRONTIER.action, "git_stage_paths_v1")
        self.assertEqual(FROZEN_FRONTIER.capability, "git.write")
        self.assertTrue(FROZEN_FRONTIER.authority_late_binding)
        self.assertFalse(FROZEN_FRONTIER.public_mutation_enabled)
        self.assertFalse(FROZEN_FRONTIER.shell_process_allowed)
        self.assertFalse(FROZEN_FRONTIER.hooks_filters_allowed)
        self.assertFalse(FROZEN_FRONTIER.network_credentials_allowed)

    def test_every_remaining_seam_is_named_for_codex(self) -> None:
        seams = FROZEN_FRONTIER.remaining_seams()
        self.assertEqual(len(seams), 11)
        self.assertEqual(len(seams), len(set(seams)))
        self.assertIn("prove_and_pin_index_codec_backend", seams)
        self.assertIn("add_dedicated_git_write_control_plane_capability", seams)
        self.assertIn("prove_native_windows_linux_macos_e2e", seams)
        self.assertIn("complete_evidence_ledger_and_heds", seams)

    def test_frontier_cannot_mint_permit_or_publish(self) -> None:
        self.assertFalse(hasattr(FROZEN_FRONTIER, "mint_permit"))
        self.assertFalse(hasattr(FROZEN_FRONTIER, "publish"))
        self.assertFalse(hasattr(FROZEN_FRONTIER, "stage_paths"))


if __name__ == "__main__":
    unittest.main()
