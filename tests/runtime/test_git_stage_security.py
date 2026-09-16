from __future__ import annotations

import unittest

from hive_runtime.git_stage import (
    GitStageUnavailableError,
    GovernedGitStageAdapter,
    UnsupportedGitStageBackend,
)


class GitStageSecurityAcceptanceMap(unittest.TestCase):
    """Security acceptance map for the governed Git staging boundary.

    Only properties objectively implemented by the pre-authority adapter are active. The
    remaining skips are hard promotion gates and must become native/backend evidence before
    WO-0023 can be promoted.
    """

    def test_rejects_traversal_dot_git_pathspec_magic_and_duplicate_aliases(self) -> None:
        adapter = GovernedGitStageAdapter()
        invalid = (
            ["../escape.py"],
            ["a/../b.py"],
            ["./a.py"],
            ["/absolute.py"],
            [".git/index"],
            [".GIT/config"],
            ["*.py"],
            ["src/?.py"],
            ["src/[ab].py"],
            [":(top)src/a.py"],
            ["src/a.py", "src/a.py"],
            ["src\\a.py", "src/a.py"],
            ["src//a.py"],
            ["src/./a.py"],
            ["src/../a.py"],
            ["bad\x00name.py"],
        )
        for paths in invalid:
            with self.subTest(paths=paths):
                with self.assertRaises(ValueError):
                    adapter.prepare(paths)

    def test_default_adapter_is_non_mutating_and_fails_closed(self) -> None:
        adapter = GovernedGitStageAdapter()
        self.assertEqual(adapter.backend_id, "unsupported-git-stage-v1")
        self.assertFalse(adapter.mutation_authority_enabled)
        with self.assertRaises(GitStageUnavailableError):
            adapter.prepare(["src/a.py"])

    def test_pre_authority_adapter_exposes_no_public_stage_operation(self) -> None:
        adapter = GovernedGitStageAdapter(UnsupportedGitStageBackend())
        self.assertFalse(hasattr(adapter, "stage_paths"))
        self.assertFalse(adapter.mutation_authority_enabled)

    @unittest.skip("PREBUILT: implement no-follow worktree observation")
    def test_rejects_symlink_reparse_directory_and_special_file_targets(self) -> None:
        self.fail("executor must prove native path safety")

    @unittest.skip("PREBUILT: implement supported repository envelope")
    def test_rejects_linked_worktree_nested_repo_submodule_and_bare_repo(self) -> None:
        self.fail("executor must prove repository-boundary checks")

    @unittest.skip("PREBUILT: implement exact approval observation")
    def test_rejects_stale_head_index_or_worktree_after_approval(self) -> None:
        self.fail("executor must prove stale-state rejection")

    @unittest.skip("PREBUILT: implement ownership-safe index transaction")
    def test_foreign_index_lock_fails_closed_and_is_never_removed(self) -> None:
        self.fail("executor must prove lock ownership")

    @unittest.skip("PREBUILT: integrate dedicated git.write control-plane action")
    def test_permit_is_request_bound_single_use_and_consumed_at_final_safe_boundary(self) -> None:
        self.fail("executor must prove permit ordering")

    @unittest.skip("PREBUILT: integrate session state with staging executor")
    def test_cancel_takeover_expiry_and_emergency_stop_prevent_publication(self) -> None:
        self.fail("executor must prove session safety")

    @unittest.skip("PREBUILT: implement Git adapter without executable extension points")
    def test_staging_executes_no_shell_process_hook_external_filter_network_or_credentials(self) -> None:
        self.fail("executor must prove authority isolation")

    @unittest.skip("PREBUILT: implement redacted request/audit/receipt")
    def test_raw_worktree_and_index_bytes_never_enter_approval_audit_or_receipt(self) -> None:
        self.fail("executor must prove redaction")

    @unittest.skip("PREBUILT: add native CI proof on all target platforms")
    def test_windows_linux_and_macos_require_independent_non_skipped_native_proof(self) -> None:
        self.fail("promotion gate")


if __name__ == "__main__":
    unittest.main()
