from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError, GovernedGitStageAdapter, UnsupportedGitStageBackend
from hive_runtime.git_stage_observer import PosixGitStageObserver
from hive_runtime.git_stage_transaction import GitIndexLockBusyError, PosixGitIndexTransaction


def _ordinary_repo(root: Path) -> None:
    git = root / ".git"; (git / "refs" / "heads").mkdir(parents=True); oid = "1" * 40
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii"); (git / "refs" / "heads" / "main").write_text(oid + "\n", encoding="ascii")


@unittest.skipIf(os.name == "nt", "POSIX observer proof")
class PosixGitStageSecurityAcceptanceMap(unittest.TestCase):
    def test_rejects_symlink_directory_and_special_file_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); (root / "regular.txt").write_bytes(b"safe"); observer = PosixGitStageObserver(root); (root / "dir").mkdir()
            with self.assertRaises(GitStageUnsupportedRepositoryError): observer.observe(["dir"])
            (root / "link.txt").symlink_to(root / "regular.txt")
            with self.assertRaises(GitStageUnsupportedRepositoryError): observer.observe(["link.txt"])
            (root / "parent").mkdir(); (root / "parent" / "real.txt").write_bytes(b"safe"); (root / "parent-link").symlink_to(root / "parent", target_is_directory=True)
            with self.assertRaises(GitStageUnsupportedRepositoryError): observer.observe(["parent-link/real.txt"])
            if hasattr(os, "mkfifo"):
                os.mkfifo(root / "pipe")
                with self.assertRaises(GitStageUnsupportedRepositoryError): observer.observe(["pipe"])

    def test_rejects_gitdir_indirection_and_unsupported_repository_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / ".git").write_text("gitdir: elsewhere\n", encoding="ascii")
            with self.assertRaises(GitStageUnsupportedRepositoryError): PosixGitStageObserver(root)
        for feature in ("commondir", "modules", "shallow"):
            with self.subTest(feature=feature), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _ordinary_repo(root); candidate = root / ".git" / feature; candidate.mkdir() if feature == "modules" else candidate.write_text("unsupported\n", encoding="ascii"); (root / "a.txt").write_bytes(b"a"); observer = PosixGitStageObserver(root)
                with self.assertRaises(GitStageUnsupportedRepositoryError): observer.observe(["a.txt"])

    def test_rejects_nested_repository_and_gitdir_boundaries_on_approved_path(self) -> None:
        for marker_kind in ("directory", "gitdir-file"):
            with self.subTest(marker_kind=marker_kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _ordinary_repo(root); nested = root / "vendor"; nested.mkdir(); target = nested / "src"; target.mkdir(); (target / "a.py").write_bytes(b"a")
                marker = nested / ".git"
                if marker_kind == "directory": marker.mkdir()
                else: marker.write_text("gitdir: ../../.git/modules/vendor\n", encoding="ascii")
                with self.assertRaises(GitStageUnsupportedRepositoryError): PosixGitStageObserver(root).observe(["vendor/src/a.py"])

    def test_unrelated_nested_repository_does_not_poison_safe_path_observation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); safe = root / "src"; safe.mkdir(); (safe / "a.py").write_bytes(b"a"); unrelated = root / "vendor"; unrelated.mkdir(); (unrelated / ".git").mkdir()
            state = PosixGitStageObserver(root).observe(["src/a.py"])
            self.assertEqual(tuple(item.path for item in state.worktree_states), ("src/a.py",))

    def test_only_true_absence_may_fall_back_from_loose_ref_to_packed_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); git = root / ".git"; loose = git / "refs" / "heads" / "main"; loose.unlink(); (git / "packed-refs").write_text("2" * 40 + " refs/heads/main\n", encoding="ascii"); (root / "a.txt").write_bytes(b"a")
            self.assertEqual(PosixGitStageObserver(root).observe(["a.txt"]).repository_head, "2" * 40)

    def test_unsafe_loose_ref_never_falls_back_to_packed_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); git = root / ".git"; loose = git / "refs" / "heads" / "main"; loose.unlink(); loose.symlink_to(git / "HEAD"); (git / "packed-refs").write_text("2" * 40 + " refs/heads/main\n", encoding="ascii"); (root / "a.txt").write_bytes(b"a")
            with self.assertRaises(GitStageUnsupportedRepositoryError): PosixGitStageObserver(root).observe(["a.txt"])

    def test_unsafe_packed_refs_never_looks_absent_or_unborn(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); git = root / ".git"; (git / "refs" / "heads" / "main").unlink(); packed = git / "packed-refs"; packed.symlink_to(git / "HEAD"); (root / "a.txt").write_bytes(b"a")
            with self.assertRaises(GitStageUnsupportedRepositoryError): PosixGitStageObserver(root).observe(["a.txt"])

    def test_unsafe_index_never_looks_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); git = root / ".git"; (root / "a.txt").write_bytes(b"a"); (git / "index-target").write_bytes(b"index"); (git / "index").symlink_to(git / "index-target")
            with self.assertRaises(GitStageUnsupportedRepositoryError): PosixGitStageObserver(root).observe(["a.txt"])

    def test_observation_binds_head_index_and_worktree_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); (root / ".git" / "index").write_bytes(b"synthetic-index-for-observation-only"); (root / "a.txt").write_bytes(b"approved bytes"); before_index = (root / ".git" / "index").read_bytes(); before_file = (root / "a.txt").read_bytes(); observer = PosixGitStageObserver(root); state = observer.observe(["a.txt"])
            self.assertEqual(state.repository_head, "1" * 40); self.assertEqual(state.index_state, "regular"); self.assertTrue(state.index_identity.startswith("posix:")); self.assertEqual(len(state.index_sha256), 64); self.assertEqual(tuple(item.path for item in state.worktree_states), ("a.txt",)); self.assertEqual(state.worktree_states[0].content_bytes, len(before_file)); self.assertEqual((root / ".git" / "index").read_bytes(), before_index); self.assertEqual((root / "a.txt").read_bytes(), before_file)

    def test_rejects_stale_head_index_or_worktree_after_approval(self) -> None:
        for mutation in ("head", "index", "worktree"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _ordinary_repo(root); git = root / ".git"; (git / "index").write_bytes(b"index-v1"); (root / "a.txt").write_bytes(b"worktree-v1"); observer = PosixGitStageObserver(root); approved = observer.observe(["a.txt"]); observer.revalidate(approved)
                if mutation == "head": (git / "refs" / "heads" / "main").write_text("2" * 40 + "\n", encoding="ascii")
                elif mutation == "index": (git / "index").write_bytes(b"index-v2")
                else: (root / "a.txt").write_bytes(b"worktree-v2")
                with self.assertRaises(GitStageUnavailableError): observer.revalidate(approved)

    def test_foreign_index_lock_fails_closed_and_is_never_removed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); lock = root / ".git" / "index.lock"; foreign = b"foreign-lock-must-survive"; lock.write_bytes(foreign); tx = PosixGitIndexTransaction(root / ".git")
            with self.assertRaises(GitIndexLockBusyError): tx.acquire()
            tx.close(); self.assertEqual(lock.read_bytes(), foreign)

    def test_owned_index_lock_is_private_preparation_and_cleanup_is_identity_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _ordinary_repo(root); git = root / ".git"; index = git / "index"; index.write_bytes(b"original-index"); tx = PosixGitIndexTransaction(git); identity = tx.acquire(); self.assertTrue(tx.owns_lock); self.assertEqual(tx.lock_identity, identity); tx.write_prepared_index(b"candidate-index"); self.assertEqual(index.read_bytes(), b"original-index"); self.assertEqual((git / "index.lock").read_bytes(), b"candidate-index")
            with self.assertRaises(GitStageUnavailableError): tx.publish()
            tx.close(); self.assertFalse((git / "index.lock").exists()); self.assertEqual(index.read_bytes(), b"original-index")


class GitStageSecurityAcceptanceMap(unittest.TestCase):
    def test_rejects_traversal_dot_git_pathspec_magic_and_duplicate_aliases(self) -> None:
        adapter = GovernedGitStageAdapter(); invalid = (["../escape.py"],["a/../b.py"],["./a.py"],["/absolute.py"],[".git/index"],[".GIT/config"],["*.py"],["src/?.py"],["src/[ab].py"],[":(top)src/a.py"],["src/a.py","src/a.py"],["src\\a.py","src/a.py"],["src//a.py"],["src/./a.py"],["src/../a.py"],["bad\x00name.py"])
        for paths in invalid:
            with self.subTest(paths=paths):
                with self.assertRaises(ValueError): adapter.prepare(paths)

    def test_default_adapter_is_non_mutating_and_fails_closed(self) -> None:
        adapter = GovernedGitStageAdapter(); self.assertEqual(adapter.backend_id,"unsupported-git-stage-v1"); self.assertFalse(adapter.mutation_authority_enabled)
        with self.assertRaises(GitStageUnavailableError): adapter.prepare(["src/a.py"])

    def test_pre_authority_adapter_exposes_no_public_stage_operation(self) -> None:
        adapter = GovernedGitStageAdapter(UnsupportedGitStageBackend()); self.assertFalse(hasattr(adapter,"stage_paths")); self.assertFalse(adapter.mutation_authority_enabled)

    @unittest.skip("PREBUILT: integrate dedicated git.write control-plane action")
    def test_permit_is_request_bound_single_use_and_consumed_at_final_safe_boundary(self) -> None: self.fail("executor must prove permit ordering")
    @unittest.skip("PREBUILT: integrate session state with staging executor")
    def test_cancel_takeover_expiry_and_emergency_stop_prevent_publication(self) -> None: self.fail("executor must prove session safety")
    @unittest.skip("PREBUILT: implement Git adapter without executable extension points")
    def test_staging_executes_no_shell_process_hook_external_filter_network_or_credentials(self) -> None: self.fail("executor must prove authority isolation")
    @unittest.skip("PREBUILT: implement redacted request/audit/receipt")
    def test_raw_worktree_and_index_bytes_never_enter_approval_audit_or_receipt(self) -> None: self.fail("executor must prove redaction")
    @unittest.skip("PREBUILT: add native CI proof on all target platforms")
    def test_windows_linux_and_macos_require_independent_non_skipped_native_proof(self) -> None: self.fail("promotion gate")


if __name__ == "__main__": unittest.main()
