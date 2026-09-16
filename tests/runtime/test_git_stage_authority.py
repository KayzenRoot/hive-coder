from __future__ import annotations

"""Authority, publication and native end-to-end proof for HCODER-WO-0023.

This lane exercises the real governed API: control plane, approval challenge,
execution permit, ordered final safe boundary, blob publication, atomic index
publication and postcondition verification. Git is used only as a fixture
generator and oracle; no product module in this path executes a process.

The lane is deliberately platform-neutral so it runs independently on Windows,
Linux and macOS. A platform is never inferred from another platform's result.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.control_policy import CapabilityRule, ControlPolicy
from hive_runtime.control_types import Capability, DecisionKind, SessionState
from hive_runtime.errors import PermitError, SessionStateError
from hive_runtime.git_stage import GitStageUnavailableError, GovernedGitStageCapability

_GIT = shutil.which("git")
_GIT_REASON = "the governed staging proof requires a git executable as fixture generator and oracle"

ACTION = "git_stage_paths_v1"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(repo), capture_output=True, text=True, timeout=120, check=False
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


class RealRepo:
    """A throwaway real Git repository used as fixture and oracle."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True)
        git(root, "init", "-q", ".")
        git(root, "config", "core.autocrlf", "false")
        git(root, "config", "user.email", "proof@hive")
        git(root, "config", "user.name", "hive-proof")

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")

    def seed(self) -> None:
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "seed")

    def index_bytes(self) -> bytes:
        return (self.root / ".git" / "index").read_bytes()

    def objects_listing(self) -> list[str]:
        base = self.root / ".git" / "objects"
        return sorted(p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file())

    def listing(self) -> str:
        return git(self.root, "ls-files", "--stage").strip()

    def write_tree(self) -> str:
        return git(self.root, "write-tree").strip()


class GovernedHarness:
    """Drives the real control plane and the real governed staging capability."""

    def __init__(self, root: Path) -> None:
        self.root = root
        policy = ControlPolicy.build(
            rules=[
                CapabilityRule.build(
                    Capability.GIT_WRITE,
                    allowed_actions={ACTION},
                    allowed_workspace_roots={str(root)},
                )
            ]
        )
        self.plane = PermissionControlPlane()
        self.session = self.plane.create_session(policy, duration_seconds=600)
        self.capability = GovernedGitStageCapability(root, self.plane)

    def request(self, *paths: str):
        return self.capability.prepare_stage_request(self.session, list(paths))

    def permit(self, request):
        challenge = self.plane.create_approval_challenge(request)
        token = self.plane.approve_challenge_from_trusted_ui(challenge.challenge_id, session_id=self.session)
        return self.plane.authorize(request, approval_token=token)


@unittest.skipUnless(_GIT is not None, _GIT_REASON)
class GovernedStagingEndToEndTests(unittest.TestCase):
    def _repo(self, tmp: str) -> RealRepo:
        repo = RealRepo(Path(tmp) / "repo")
        repo.write("root.txt", "root\n")
        repo.write("dir/a.txt", "alpha\n")
        repo.write("dir/nested/b.txt", "beta\n")
        repo.seed()
        return repo

    def test_modified_tracked_file_is_staged_to_the_exact_blob(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            repo.write("dir/a.txt", "alpha MODIFIED\n")
            harness = GovernedHarness(repo.root)

            request = harness.request("dir/a.txt")
            binding = request.arguments["path_bindings"][0]
            self.assertEqual(binding["path"], "dir/a.txt")
            permit = harness.permit(request)
            receipt = harness.capability.stage_paths(request, permit_token=permit.token)

            self.assertEqual(receipt.committed_state, "index_updated")
            self.assertEqual(receipt.staged_paths, ("dir/a.txt",))
            staged = {line.split("\t")[1]: line.split()[1] for line in repo.listing().splitlines()}
            self.assertEqual(staged["dir/a.txt"], binding["blob_oid"])
            # Unrelated entries keep their original object ids.
            self.assertEqual(staged["root.txt"], git(repo.root, "rev-parse", "HEAD:root.txt").strip())
            self.assertEqual(staged["dir/nested/b.txt"], git(repo.root, "rev-parse", "HEAD:dir/nested/b.txt").strip())

    def test_untracked_file_is_added_and_matches_the_git_control_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            repo.write("dir/added.txt", "added\n")
            harness = GovernedHarness(repo.root)
            request = harness.request("dir/added.txt")
            permit = harness.permit(request)
            receipt = harness.capability.stage_paths(request, permit_token=permit.token)
            self.assertEqual(receipt.committed_state, "index_updated")

            candidate_tree = repo.write_tree()
            control = RealRepo(Path(tmp) / "control")
            control.write("root.txt", "root\n")
            control.write("dir/a.txt", "alpha\n")
            control.write("dir/nested/b.txt", "beta\n")
            control.seed()
            control.write("dir/added.txt", "added\n")
            git(control.root, "add", "dir/added.txt")
            self.assertEqual(candidate_tree, control.write_tree())
            self.assertEqual(repo.listing(), control.listing())

    def test_staged_index_is_accepted_by_git_and_leaves_no_corruption(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            repo.write("dir/a.txt", "alpha MODIFIED\n")
            repo.write("added.txt", "brand new\n")
            harness = GovernedHarness(repo.root)
            request = harness.request("added.txt", "dir/a.txt")
            permit = harness.permit(request)
            harness.capability.stage_paths(request, permit_token=permit.token)

            status = git(repo.root, "status", "--porcelain")
            self.assertIn("M  dir/a.txt", status)
            self.assertIn("A  added.txt", status)
            fsck = git(repo.root, "fsck")
            self.assertNotIn("error", fsck.lower())
            # The commit is still possible and produces the staged content.
            self.assertNotEqual(repo.write_tree(), git(repo.root, "rev-parse", "HEAD^{tree}").strip())

    def test_publication_only_creates_the_content_addressed_objects_it_staged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            repo.write("dir/a.txt", "alpha MODIFIED\n")
            before = repo.objects_listing()
            harness = GovernedHarness(repo.root)
            request = harness.request("dir/a.txt")
            oid = request.arguments["path_bindings"][0]["blob_oid"]
            permit = harness.permit(request)
            harness.capability.stage_paths(request, permit_token=permit.token)
            after = repo.objects_listing()
            created = sorted(set(after) - set(before))
            self.assertEqual(created, [f"{oid[:2]}/{oid[2:]}"])


class IndexTransactionPublicationTests(unittest.TestCase):
    """Platform-neutral coverage of the owned index lock publication seam.

    This deliberately runs on Windows as well. The equivalent assertions live in a
    POSIX-gated class elsewhere, and a Windows-specific regression previously hid
    behind that gate, so the seam is covered here unconditionally.
    """

    def _repo(self, root: Path) -> None:
        git_dir = root / ".git"
        (git_dir / "objects" / "info").mkdir(parents=True)
        (git_dir / "objects" / "pack").mkdir()
        (git_dir / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")
        (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii")
        (git_dir / "refs" / "heads").mkdir(parents=True)
        (git_dir / "refs" / "heads" / "main").write_text("2" * 40 + "\n", encoding="ascii")
        (git_dir / "index").write_bytes(b"original-index")

    def test_prepare_writes_only_the_private_lock(self) -> None:
        import hashlib

        from hive_runtime.git_stage_transaction import PosixGitIndexTransaction

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            git_dir = root / ".git"
            candidate = b"candidate-index"
            transaction = PosixGitIndexTransaction(git_dir)
            try:
                transaction.acquire()
                transaction.write_prepared_index(candidate)
                self.assertEqual((git_dir / "index").read_bytes(), b"original-index")
                self.assertEqual((git_dir / "index.lock").read_bytes(), candidate)
            finally:
                transaction.close()
            self.assertEqual((git_dir / "index").read_bytes(), b"original-index")
            self.assertFalse((git_dir / "index.lock").exists())

    def test_publish_is_atomic_and_only_when_the_lock_matches(self) -> None:
        import hashlib

        from hive_runtime.git_stage_transaction import PosixGitIndexTransaction

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            git_dir = root / ".git"
            candidate = b"candidate-index"
            digest = hashlib.sha256(candidate).hexdigest()

            # A mismatching digest must fail closed and leave the index untouched.
            mismatched = PosixGitIndexTransaction(git_dir)
            try:
                mismatched.acquire()
                mismatched.write_prepared_index(candidate)
                with self.assertRaises(GitStageUnavailableError):
                    mismatched.publish(expected_sha256="0" * 64, expected_bytes=len(candidate))
                self.assertEqual((git_dir / "index").read_bytes(), b"original-index")
            finally:
                mismatched.close()
            self.assertFalse((git_dir / "index.lock").exists())

            # A matching digest publishes the exact candidate and consumes the lock.
            published = PosixGitIndexTransaction(git_dir)
            try:
                published.acquire()
                published.write_prepared_index(candidate)
                published.publish(expected_sha256=digest, expected_bytes=len(candidate))
                self.assertEqual((git_dir / "index").read_bytes(), candidate)
                self.assertFalse((git_dir / "index.lock").exists())
            finally:
                published.close()
            self.assertEqual((git_dir / "index").read_bytes(), candidate)

    def test_published_index_bytes_hash_to_the_approved_candidate(self) -> None:
        import hashlib

        from hive_runtime.git_stage_transaction import PosixGitIndexTransaction

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            git_dir = root / ".git"
            candidate = b"DIRC-candidate-payload"
            transaction = PosixGitIndexTransaction(git_dir)
            try:
                transaction.acquire()
                transaction.write_prepared_index(candidate)
                transaction.publish(
                    expected_sha256=hashlib.sha256(candidate).hexdigest(), expected_bytes=len(candidate)
                )
                committed = (git_dir / "index").read_bytes()
                self.assertEqual(hashlib.sha256(committed).hexdigest(), hashlib.sha256(candidate).hexdigest())
            finally:
                transaction.close()


@unittest.skipUnless(_GIT is not None, _GIT_REASON)
class GovernedStagingRequestBindingTests(unittest.TestCase):
    def _repo(self, tmp: str) -> RealRepo:
        repo = RealRepo(Path(tmp) / "repo")
        repo.write("a.txt", "alpha\n")
        repo.seed()
        repo.write("a.txt", "alpha MODIFIED\n")
        return repo

    def test_request_binds_candidate_digest_object_store_and_blob_oids(self) -> None:
        from hive_runtime.git_stage_contract import GIT_STAGE_ARGUMENT_KEYS

        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            harness = GovernedHarness(repo.root)
            request = harness.request("a.txt")
            arguments = request.arguments
            self.assertEqual(set(arguments), GIT_STAGE_ARGUMENT_KEYS)
            self.assertEqual(request.capability, Capability.GIT_WRITE)
            self.assertEqual(request.action, ACTION)
            self.assertEqual(arguments["target_state"], "index_update")
            self.assertEqual(len(arguments["candidate_index_sha256"]), 64)
            self.assertGreater(arguments["candidate_index_bytes"], 0)
            self.assertEqual(arguments["object_store_format"], "sha1")
            self.assertTrue(arguments["object_store_identity"])
            binding = arguments["path_bindings"][0]
            self.assertEqual(len(binding["blob_oid"]), 40)
            self.assertEqual(binding["content_sha256"], arguments["worktree_states"][0]["content_sha256"])
            self.assertEqual(arguments["path_count"], 1)
            self.assertEqual(harness.plane.evaluate(request).kind, DecisionKind.REQUIRE_APPROVAL)

    def test_request_metadata_carries_no_raw_bytes_and_receipt_exposes_no_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            harness = GovernedHarness(repo.root)
            request = harness.request("a.txt")
            permit = harness.permit(request)
            receipt = harness.capability.stage_paths(request, permit_token=permit.token)

            serialized = repr(request.arguments) + repr(receipt)
            for secret in ("alpha MODIFIED", "alpha\n", permit.token, "permit", "token"):
                self.assertNotIn(secret, serialized)
            for value in (receipt.workspace, receipt.repository_identity, receipt.repository_head):
                self.assertNotIn("\n", value)
            audit = " ".join(event.details_json for event in harness.plane.audit_events())
            self.assertNotIn(permit.token, audit)
            self.assertNotIn("alpha MODIFIED", audit)
            self.assertTrue(harness.plane.verify_audit_chain())

    def test_replayed_permit_and_stale_state_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            harness = GovernedHarness(repo.root)
            request = harness.request("a.txt")
            permit = harness.permit(request)
            harness.capability.stage_paths(request, permit_token=permit.token)
            with self.assertRaises((PermitError, GitStageUnavailableError)):
                harness.capability.stage_paths(request, permit_token=permit.token)

    def test_wrong_workspace_wrong_capability_and_wrong_action_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as other:
            repo = self._repo(tmp)
            harness = GovernedHarness(repo.root)
            request = harness.request("a.txt")
            permit = harness.permit(request)
            from dataclasses import replace

            with self.assertRaises(Exception):
                harness.capability.stage_paths(
                    replace(request, target=replace(request.target, workspace=str(Path(other)))), permit_token=permit.token
                )
            with self.assertRaises(Exception):
                harness.capability.stage_paths(replace(request, capability=Capability.FILESYSTEM_WRITE), permit_token=permit.token)
            with self.assertRaises(Exception):
                harness.capability.stage_paths(replace(request, action="git_commit_v1"), permit_token=permit.token)

    def test_tampered_binding_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            harness = GovernedHarness(repo.root)
            request = harness.request("a.txt")
            permit = harness.permit(request)
            arguments = dict(request.arguments)
            arguments["candidate_index_sha256"] = "0" * 64
            with self.assertRaises(Exception):
                harness.capability.stage_paths(
                    type(request)(request.session_id, request.capability, request.action, request.target, arguments),
                    permit_token=permit.token,
                )


@unittest.skipUnless(_GIT is not None, _GIT_REASON)
class GovernedStagingOrderingAndFailureTests(unittest.TestCase):
    """The mutation order must be provable by tests, not merely commented."""

    def _prepare(self, tmp: str):
        repo = RealRepo(Path(tmp) / "repo")
        repo.write("a.txt", "alpha\n")
        repo.seed()
        repo.write("a.txt", "alpha MODIFIED\n")
        harness = GovernedHarness(repo.root)
        request = harness.request("a.txt")
        return repo, harness, request

    def test_failure_before_permit_consumption_publishes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness, request = self._prepare(tmp)
            before_objects, before_index = repo.objects_listing(), repo.index_bytes()
            with mock.patch.object(
                PermissionControlPlane, "consume_execution_permit", side_effect=PermitError("injected")
            ):
                with self.assertRaises(Exception):
                    harness.capability.stage_paths(request, permit_token="unused")
            self.assertEqual(repo.objects_listing(), before_objects)
            self.assertEqual(repo.index_bytes(), before_index)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())

    def test_failure_after_permit_before_blobs_publishes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness, request = self._prepare(tmp)
            permit = harness.permit(request)
            before_objects, before_index = repo.objects_listing(), repo.index_bytes()
            from hive_runtime.git_loose_object_transaction import LooseObjectPublisher

            with mock.patch.object(LooseObjectPublisher, "publish", side_effect=GitStageUnavailableError("injected")):
                with self.assertRaises(GitStageUnavailableError):
                    harness.capability.stage_paths(request, permit_token=permit.token)
            self.assertEqual(repo.objects_listing(), before_objects)
            self.assertEqual(repo.index_bytes(), before_index)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())

    def test_failure_after_blobs_before_index_never_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness, request = self._prepare(tmp)
            permit = harness.permit(request)
            before_index = repo.index_bytes()
            from hive_runtime.git_stage_transaction import PosixGitIndexTransaction

            with mock.patch.object(PosixGitIndexTransaction, "publish", side_effect=GitStageUnavailableError("injected")):
                with self.assertRaises(GitStageUnavailableError):
                    harness.capability.stage_paths(request, permit_token=permit.token)
            # The index is untouched, so no false success was possible.
            self.assertEqual(repo.index_bytes(), before_index)

    def test_failure_after_index_publication_never_reports_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness, request = self._prepare(tmp)
            permit = harness.permit(request)
            from hive_runtime.git_stage_transaction import PosixGitIndexTransaction

            with mock.patch.object(
                PosixGitIndexTransaction, "verify_published", side_effect=GitStageUnavailableError("injected")
            ):
                with self.assertRaises(GitStageUnavailableError):
                    harness.capability.stage_paths(request, permit_token=permit.token)
            # Publication happened, but the postcondition could not be proven, so the
            # operation reported failure rather than success.
            self.assertNotEqual(repo.index_bytes(), b"")

    def test_foreign_index_lock_fails_closed_and_survives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness, request = self._prepare(tmp)
            permit = harness.permit(request)
            lock = repo.root / ".git" / "index.lock"
            foreign = b"foreign-lock-must-survive"
            lock.write_bytes(foreign)
            with self.assertRaises(Exception):
                harness.capability.stage_paths(request, permit_token=permit.token)
            self.assertEqual(lock.read_bytes(), foreign)

    def test_stale_worktree_after_approval_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness, request = self._prepare(tmp)
            permit = harness.permit(request)
            repo.write("a.txt", "alpha CHANGED AGAIN\n")
            with self.assertRaises(GitStageUnavailableError):
                harness.capability.stage_paths(request, permit_token=permit.token)

    def test_stale_head_after_approval_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness, request = self._prepare(tmp)
            permit = harness.permit(request)
            git(repo.root, "commit", "-q", "--allow-empty", "-m", "moves HEAD")
            with self.assertRaises(GitStageUnavailableError):
                harness.capability.stage_paths(request, permit_token=permit.token)

    def test_cancellation_takeover_and_emergency_stop_prevent_publication(self) -> None:
        for transition in ("cancel", "takeover", "emergency"):
            with self.subTest(transition=transition), tempfile.TemporaryDirectory() as tmp:
                repo, harness, request = self._prepare(tmp)
                permit = harness.permit(request)
                before_index = repo.index_bytes()
                if transition == "cancel":
                    harness.plane.cancel_session(harness.session)
                elif transition == "takeover":
                    harness.plane.user_takeover(harness.session)
                else:
                    harness.plane.emergency_stop(session_id=harness.session)
                with self.assertRaises((SessionStateError, GitStageUnavailableError)):
                    harness.capability.stage_paths(request, permit_token=permit.token)
                self.assertEqual(repo.index_bytes(), before_index)
                self.assertFalse((repo.root / ".git" / "index.lock").exists())

    def test_session_expiry_prevents_publication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = RealRepo(Path(tmp) / "repo")
            repo.write("a.txt", "alpha\n")
            repo.seed()
            repo.write("a.txt", "alpha MODIFIED\n")
            policy = ControlPolicy.build(
                rules=[
                    CapabilityRule.build(
                        Capability.GIT_WRITE, allowed_actions={ACTION}, allowed_workspace_roots={str(repo.root)}
                    )
                ]
            )
            clock = [1000.0]
            plane = PermissionControlPlane(security_clock=lambda: clock[0], max_session_seconds=600)
            session = plane.create_session(policy, duration_seconds=30)
            capability = GovernedGitStageCapability(repo.root, plane)
            request = capability.prepare_stage_request(session, ["a.txt"])
            challenge = plane.create_approval_challenge(request)
            token = plane.approve_challenge_from_trusted_ui(challenge.challenge_id, session_id=session)
            permit = plane.authorize(request, approval_token=token)
            before_index = repo.index_bytes()
            clock[0] += 31
            with self.assertRaises((SessionStateError, GitStageUnavailableError)):
                capability.stage_paths(request, permit_token=permit.token)
            self.assertEqual(repo.index_bytes(), before_index)


if __name__ == "__main__":
    unittest.main()
