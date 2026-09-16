from __future__ import annotations

import unittest


class GitStageSecurityAcceptanceMap(unittest.TestCase):
    """Executable checklist that remains skipped until the governed adapter exists.

    These skips are intentional prebuilt gates, not promotion evidence. WO-0023 cannot be
    promoted while any item in this class is skipped.
    """

    @unittest.skip("PREBUILT: implement exact-path normalizer in governed Git adapter")
    def test_rejects_traversal_dot_git_pathspec_magic_and_duplicate_aliases(self) -> None:
        self.fail("executor must materialize adversarial path cases")

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
