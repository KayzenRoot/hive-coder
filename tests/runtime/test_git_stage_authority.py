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
import sys
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


class LooseObjectPublicationSafetyTests(unittest.TestCase):
    """Crash-safety and no-clobber law for final loose-object publication.

    The canonical OID pathname must never contain partial bytes, must never be
    overwritten, and must never be deleted.
    """

    def _repo(self, root: Path) -> None:
        git_dir = root / ".git"
        (git_dir / "objects" / "info").mkdir(parents=True)
        (git_dir / "objects" / "pack").mkdir()
        (git_dir / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")

    def _fixture(self, root: Path):
        from hive_runtime.git_loose_object_transaction import LooseObjectPublisher, prepare_loose_blob

        self._repo(root)
        prepared, compressed = prepare_loose_blob(root, b"governed payload\n")
        return prepared, compressed, LooseObjectPublisher(root)

    def _final(self, root: Path, prepared) -> Path:
        return root / ".git" / prepared.relative_object_path

    def test_complete_object_is_promoted_and_temp_is_cleaned(self) -> None:
        from hive_runtime.git_loose_object_transaction import PUBLISHED_CREATED

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared, compressed, publisher = self._fixture(root)
            self.assertEqual(publisher.publish(prepared, compressed), PUBLISHED_CREATED)
            self.assertEqual(self._final(root, prepared).read_bytes(), compressed)
            # No private temp survives a successful publication.
            temp_dir = root / ".git" / "hive-object-tmp"
            self.assertEqual(list(temp_dir.glob("*")) if temp_dir.exists() else [], [])

    def test_partial_private_write_leaves_the_canonical_path_absent(self) -> None:
        """A private write that never completes must not create the OID pathname."""
        from hive_runtime.git_object_private_prep import PrivateObjectPreparer
        from hive_runtime.git_loose_object_transaction import LooseObjectPublisher

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared, compressed, _ = self._fixture(root)
            publisher = LooseObjectPublisher(root)

            real_materialize = PrivateObjectPreparer.materialize_private_temp

            def truncated(self, plan, payload):
                temp = real_materialize(self, plan, payload)
                # Simulate a private write that stopped early: the temp is short.
                Path(temp.identity.path).write_bytes(payload[: max(1, len(payload) // 2)])
                return temp

            with mock.patch.object(PrivateObjectPreparer, "materialize_private_temp", truncated):
                with self.assertRaises(GitStageUnavailableError):
                    publisher.publish(prepared, compressed)
            self.assertFalse(self._final(root, prepared).exists())

    def test_failed_private_materialization_leaves_the_canonical_path_absent(self) -> None:
        from hive_runtime.git_object_private_prep import PrivateObjectPreparer
        from hive_runtime.git_loose_object_transaction import LooseObjectPublisher

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared, compressed, _ = self._fixture(root)
            publisher = LooseObjectPublisher(root)
            with mock.patch.object(
                PrivateObjectPreparer, "materialize_private_temp", side_effect=GitStageUnavailableError("injected")
            ):
                with self.assertRaises(GitStageUnavailableError):
                    publisher.publish(prepared, compressed)
            self.assertFalse(self._final(root, prepared).exists())

    def test_abrupt_termination_before_promotion_leaves_the_canonical_path_absent(self) -> None:
        """Process death before promotion must not expose a canonical object.

        The child process materializes the private temporary and is killed with
        ``os._exit`` before promotion ever runs. This is the exact scenario the
        correction exists for: the old design streamed bytes directly into the
        canonical pathname, so a kill at this point would have left a partial
        object there.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            script = (
                "import os, sys\n"
                "from hive_runtime.git_loose_object_transaction import prepare_loose_blob\n"
                "from hive_runtime.git_object_private_prep import PrivateObjectPreparer, plan_private_object\n"
                "root = sys.argv[1]\n"
                "prepared, compressed = prepare_loose_blob(root, b'abrupt payload\\n')\n"
                "plan = plan_private_object(prepared, compressed)\n"
                "PrivateObjectPreparer(root).materialize_private_temp(plan, compressed)\n"
                "print(prepared.relative_object_path, flush=True)\n"
                "os._exit(9)\n"
            )
            env = dict(os.environ)
            env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])
            result = subprocess.run(
                [sys.executable, "-c", script, str(root)],
                capture_output=True,
                text=True,
                env=env,
                timeout=120,
                check=False,
            )
            self.assertEqual(result.returncode, 9, result.stderr)
            relative = result.stdout.strip()
            self.assertTrue(relative)
            self.assertFalse((root / ".git" / relative).exists())
            # The complete private temp is inert; the canonical pathname is absent.
            temp_dir = root / ".git" / "hive-object-tmp"
            self.assertTrue(temp_dir.exists())
            self.assertEqual(len(list(temp_dir.glob("*.tmp"))), 1)

    def test_existing_exact_object_is_never_overwritten(self) -> None:
        from hive_runtime.git_loose_object_transaction import PUBLISHED_ALREADY_PRESENT

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared, compressed, publisher = self._fixture(root)
            final = self._final(root, prepared)
            final.parent.mkdir(parents=True, exist_ok=True)
            final.write_bytes(compressed)
            before = final.stat().st_mtime_ns
            self.assertEqual(publisher.publish(prepared, compressed), PUBLISHED_ALREADY_PRESENT)
            self.assertEqual(final.read_bytes(), compressed)
            self.assertEqual(final.stat().st_mtime_ns, before)

    def test_corrupt_existing_object_fails_closed_and_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared, compressed, publisher = self._fixture(root)
            final = self._final(root, prepared)
            final.parent.mkdir(parents=True, exist_ok=True)
            foreign = b"not-the-approved-object"
            final.write_bytes(foreign)
            with self.assertRaises(Exception):
                publisher.publish(prepared, compressed)
            self.assertEqual(final.read_bytes(), foreign)

    def test_concurrent_winner_is_accepted_only_with_exact_proof(self) -> None:
        from hive_runtime.git_loose_object_transaction import PUBLISHED_ALREADY_PRESENT

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared, compressed, publisher = self._fixture(root)
            final = self._final(root, prepared)

            real_materialize = publisher._preparer.materialize_private_temp

            def racing(self, plan, payload):
                # Another publisher wins the final pathname before we promote.
                final.parent.mkdir(parents=True, exist_ok=True)
                final.write_bytes(payload)
                return real_materialize(plan, payload)

            with mock.patch.object(type(publisher._preparer), "materialize_private_temp", racing):
                self.assertEqual(publisher.publish(prepared, compressed), PUBLISHED_ALREADY_PRESENT)
            self.assertEqual(final.read_bytes(), compressed)

    def test_concurrent_corrupt_winner_fails_closed_without_clobbering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prepared, compressed, publisher = self._fixture(root)
            final = self._final(root, prepared)
            foreign = b"foreign-winner-must-survive"

            real_materialize = publisher._preparer.materialize_private_temp

            def racing(self, plan, payload):
                final.parent.mkdir(parents=True, exist_ok=True)
                final.write_bytes(foreign)
                return real_materialize(plan, payload)

            with mock.patch.object(type(publisher._preparer), "materialize_private_temp", racing):
                with self.assertRaises(Exception):
                    publisher.publish(prepared, compressed)
            self.assertEqual(final.read_bytes(), foreign)

    def test_no_clobber_promotion_primitive_is_available_here(self) -> None:
        """Native proof that os.link is an atomic create-if-absent on this platform."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.bin"
            target = root / "target.bin"
            source.write_bytes(b"payload")
            os.link(source, target)
            self.assertEqual(target.read_bytes(), b"payload")
            with self.assertRaises(FileExistsError):
                os.link(source, target)
            self.assertEqual(target.read_bytes(), b"payload")
            # The promoted object shares the inode, so the temp can be removed
            # without affecting the final pathname.
            os.unlink(source)
            self.assertEqual(target.read_bytes(), b"payload")

    def test_identity_safe_temp_cleanup_preserves_a_replacement(self) -> None:
        from hive_runtime.git_object_private_prep import PrivateObjectPreparer, plan_private_object
        from hive_runtime.git_loose_object_transaction import prepare_loose_blob

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._repo(root)
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"payload\n")
            temp = preparer.materialize_private_temp(plan_private_object(prepared, compressed), compressed)
            path = Path(temp.identity.path)
            path.unlink()
            path.mkdir()
            preparer.cleanup_private_temp(temp)
            self.assertTrue(path.is_dir())

    def test_published_object_is_readable_by_git(self) -> None:
        if _GIT is None:
            self.skipTest(_GIT_REASON)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            git(root, "init", "-q", ".")
            from hive_runtime.git_loose_object_transaction import LooseObjectPublisher, prepare_loose_blob

            prepared, compressed = prepare_loose_blob(root, b"governed payload\n")
            LooseObjectPublisher(root).publish(prepared, compressed)
            self.assertEqual(git(root, "cat-file", "-t", prepared.candidate.oid).strip(), "blob")
            self.assertEqual(git(root, "cat-file", "-s", prepared.candidate.oid).strip(), str(prepared.candidate.content_bytes))


@unittest.skipUnless(_GIT is not None, _GIT_REASON)
class ApprovalConfusionTests(unittest.TestCase):
    """A contradictory approved request must be rejected before permit consumption."""

    def _prepare(self, tmp: str):
        repo = RealRepo(Path(tmp) / "repo")
        repo.write("a.txt", "alpha\n")
        repo.write("b.txt", "beta\n")
        repo.seed()
        repo.write("a.txt", "alpha MODIFIED\n")
        repo.write("b.txt", "beta MODIFIED\n")
        harness = GovernedHarness(repo.root)
        return repo, harness

    def _approved_request(self, harness, paths):
        """Build a real challenge and permit for the given request."""
        request = harness.request(*paths)
        challenge = harness.plane.create_approval_challenge(request)
        token = harness.plane.approve_challenge_from_trusted_ui(challenge.challenge_id, session_id=harness.session)
        permit = harness.plane.authorize(request, approval_token=token)
        return request, permit

    def test_contradictory_paths_are_rejected_before_permit_consumption(self) -> None:
        """A contradictory request receives its OWN approval and permit, then is rejected.

        Approving the valid request and mutating it afterwards would prove only that
        the permit fingerprint no longer matches. It would not prove that semantic
        path equality blocks a contradictory request that legitimately obtained a
        permit for itself. This test builds the contradiction first, then runs the
        real challenge -> trusted approval -> permit flow against it, so the
        rejection can only come from the executor's own validation.
        """
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp)

            # 1) A legitimate request, used only as the source of consistent
            #    worktree states and path bindings.
            legitimate = harness.request("a.txt")

            # 2) Contradiction built BEFORE any challenge: declared paths name a
            #    different safe-looking file while the worktree states and bindings
            #    still describe "a.txt". The result stays schema-valid.
            arguments = dict(legitimate.arguments)
            arguments["paths"] = ["b.txt"]
            contradictory = replace(legitimate, arguments=arguments)

            # 3-5) Real challenge, real trusted approval, real permit bound to the
            #      CONTRADICTORY request.
            challenge = harness.plane.create_approval_challenge(contradictory)
            token = harness.plane.approve_challenge_from_trusted_ui(
                challenge.challenge_id, session_id=harness.session
            )
            permit = harness.plane.authorize(contradictory, approval_token=token)
            self.assertEqual(permit.request_fingerprint, harness.plane.request_fingerprint(contradictory))

            # 6) Snapshot before execution.
            before_index = repo.index_bytes()
            before_objects = repo.objects_listing()

            # 7-8) Execution must be rejected by semantic path validation.
            with self.assertRaises(Exception) as caught:
                harness.capability.stage_paths(contradictory, permit_token=permit.token)
            self.assertNotIsInstance(caught.exception, PermitError)

            # 9) Zero mutation, zero residual lock.
            self.assertEqual(repo.index_bytes(), before_index)
            self.assertEqual(repo.objects_listing(), before_objects)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())

            # 10) The permit was NOT consumed by stage_paths. Proven through the
            #     canonical control-plane API: consumption succeeds here only if the
            #     earlier rejection happened before the permit boundary.
            harness.plane.consume_execution_permit(permit.token, contradictory)
            with self.assertRaises(PermitError):
                harness.plane.consume_execution_permit(permit.token, contradictory)

    def test_path_count_disagreement_is_rejected(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp)
            request, permit = self._approved_request(harness, ["a.txt", "b.txt"])
            before_index = repo.index_bytes()
            arguments = dict(request.arguments)
            arguments["path_count"] = 1
            with self.assertRaises(Exception):
                harness.capability.stage_paths(replace(request, arguments=arguments), permit_token=permit.token)
            self.assertEqual(repo.index_bytes(), before_index)

    def test_reordered_paths_are_rejected(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp)
            request, permit = self._approved_request(harness, ["a.txt", "b.txt"])
            before_index = repo.index_bytes()
            arguments = dict(request.arguments)
            arguments["paths"] = ["b.txt", "a.txt"]
            with self.assertRaises(Exception):
                harness.capability.stage_paths(replace(request, arguments=arguments), permit_token=permit.token)
            self.assertEqual(repo.index_bytes(), before_index)

    def test_duplicate_declared_paths_are_rejected(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp)
            request, permit = self._approved_request(harness, ["a.txt"])
            arguments = dict(request.arguments)
            arguments["paths"] = ["a.txt", "a.txt"]
            with self.assertRaises(Exception):
                harness.capability.stage_paths(replace(request, arguments=arguments), permit_token=permit.token)

    def test_pathspec_string_and_glob_declared_paths_are_rejected(self) -> None:
        from dataclasses import replace

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp)
            request, permit = self._approved_request(harness, ["a.txt"])
            for bad in ("a.txt", ["*.txt"], ["../a.txt"], [".git/config"], ["a/../a.txt"]):
                with self.subTest(bad=bad):
                    arguments = dict(request.arguments)
                    arguments["paths"] = bad
                    with self.assertRaises(Exception):
                        harness.capability.stage_paths(replace(request, arguments=arguments), permit_token=permit.token)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())


@unittest.skipUnless(_GIT is not None, _GIT_REASON)
class MidPublicationAuthorityTests(unittest.TestCase):
    """The session stays authoritative during a multi-object staging action."""

    def _prepare(self, tmp: str):
        repo = RealRepo(Path(tmp) / "repo")
        for name in ("a.txt", "b.txt", "c.txt"):
            repo.write(name, f"{name} original\n")
        repo.seed()
        for name in ("a.txt", "b.txt", "c.txt"):
            repo.write(name, f"{name} modified\n")
        harness = GovernedHarness(repo.root)
        return repo, harness

    def _assert_transition_after_first_blob(self, transition: str) -> None:
        """Transition the session after the first blob and assert the consequences.

        All assertions run inside the live fixture: the repository is a temporary
        directory that is removed as soon as this method returns.
        """
        from hive_runtime.git_loose_object_transaction import LooseObjectPublisher

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp)
            request = harness.request("a.txt", "b.txt", "c.txt")
            bound = [item["blob_oid"] for item in request.arguments["path_bindings"]]
            permit = harness.permit(request)
            before_index = repo.index_bytes()

            calls = {"count": 0}
            real_publish = LooseObjectPublisher.publish

            def publishing_then_transition(self, preparation, compressed, *, pre_publish_check=None):
                result = real_publish(self, preparation, compressed, pre_publish_check=pre_publish_check)
                calls["count"] += 1
                if calls["count"] == 1:
                    if transition == "cancel":
                        harness.plane.cancel_session(harness.session)
                    elif transition == "takeover":
                        harness.plane.user_takeover(harness.session)
                    elif transition == "emergency":
                        harness.plane.emergency_stop(session_id=harness.session)
                    else:
                        harness.plane.emergency_stop()
                return result

            with mock.patch.object(LooseObjectPublisher, "publish", publishing_then_transition):
                with self.assertRaises((SessionStateError, GitStageUnavailableError)):
                    harness.capability.stage_paths(request, permit_token=permit.token)

            published = [oid for oid in bound if (repo.root / ".git" / "objects" / oid[:2] / oid[2:]).exists()]
            # Exactly the first blob was published; no later promotion ever ran.
            self.assertEqual(published, [bound[0]], f"{transition}: only the first blob may be published")
            self.assertEqual(calls["count"], 1, f"{transition}: no later promotion may run")
            # The index is untouched and no owned lock is left behind.
            self.assertEqual(repo.index_bytes(), before_index)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())
            # The already-published blob is NOT rolled back: it stays reachable.
            self.assertEqual(git(repo.root, "cat-file", "-t", bound[0]).strip(), "blob")
            for oid in bound[1:]:
                self.assertFalse((repo.root / ".git" / "objects" / oid[:2] / oid[2:]).exists())

    def test_cancellation_after_first_blob_stops_later_blobs_and_index(self) -> None:
        self._assert_transition_after_first_blob("cancel")

    def test_takeover_after_first_blob_stops_later_blobs_and_index(self) -> None:
        self._assert_transition_after_first_blob("takeover")

    def test_emergency_stop_after_first_blob_stops_later_blobs_and_index(self) -> None:
        self._assert_transition_after_first_blob("emergency")

    def test_global_emergency_stop_after_first_blob_stops_later_blobs_and_index(self) -> None:
        self._assert_transition_after_first_blob("global_emergency")

    def test_multi_file_staging_succeeds_when_no_transition_occurs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp)
            request = harness.request("a.txt", "b.txt", "c.txt")
            permit = harness.permit(request)
            receipt = harness.capability.stage_paths(request, permit_token=permit.token)
            self.assertEqual(receipt.committed_state, "index_updated")
            self.assertEqual(receipt.staged_paths, ("a.txt", "b.txt", "c.txt"))
            staged = {line.split("\t")[1]: line.split()[1] for line in repo.listing().splitlines()}
            for item in request.arguments["path_bindings"]:
                self.assertEqual(staged[item["path"]], item["blob_oid"])


@unittest.skipUnless(_GIT is not None, _GIT_REASON)
class FinalLinkFreshnessTests(unittest.TestCase):
    """CR-05-A: authority is enforced at the real final-link boundary.

    The session is transitioned after the private temporary has been materialized
    and re-proved, and before the atomic promotion. The injection point is the
    real fanout helper: the test calls the genuine behavior and then applies the
    transition, so no test-only hook exists in production code and the timing is
    deterministic rather than sleep-based.
    """

    def _prepare(self, tmp: str, files=("a.txt",)):
        repo = RealRepo(Path(tmp) / "repo")
        for name in files:
            repo.write(name, f"{name} original\n")
        repo.seed()
        for name in files:
            repo.write(name, f"{name} modified\n")
        harness = GovernedHarness(repo.root)
        return repo, harness

    def _assert_transition_at_final_link(self, transition: str, files=("a.txt",)) -> None:
        from hive_runtime import git_loose_object_transaction as loose_module

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp, files)
            request = harness.request(*files)
            bound = [item["blob_oid"] for item in request.arguments["path_bindings"]]
            permit = harness.permit(request)
            before_index = repo.index_bytes()
            before_objects = repo.objects_listing()

            real_fanout = loose_module._ensure_fanout_directory
            calls = {"count": 0}

            def fanout_then_transition(objects_dir, fanout):
                result = real_fanout(objects_dir, fanout)
                calls["count"] += 1
                if calls["count"] == 1:
                    if transition == "cancel":
                        harness.plane.cancel_session(harness.session)
                    elif transition == "takeover":
                        harness.plane.user_takeover(harness.session)
                    elif transition == "emergency":
                        harness.plane.emergency_stop(session_id=harness.session)
                    else:
                        harness.plane.emergency_stop()
                return result

            with mock.patch.object(loose_module, "_ensure_fanout_directory", fanout_then_transition):
                with self.assertRaises((SessionStateError, GitStageUnavailableError)):
                    # No success receipt: the call raises instead of returning one.
                    harness.capability.stage_paths(request, permit_token=permit.token)

            # The transition happened after temp materialization, before the link.
            self.assertEqual(calls["count"], 1, f"{transition}: the fanout helper must run once")
            for oid in bound:
                self.assertFalse(
                    (repo.root / ".git" / "objects" / oid[:2] / oid[2:]).exists(),
                    f"{transition}: no canonical object may appear after the transition",
                )
            self.assertEqual(repo.index_bytes(), before_index)
            self.assertEqual(repo.objects_listing(), before_objects)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())

    def test_cancel_at_final_link_boundary(self) -> None:
        self._assert_transition_at_final_link("cancel")

    def test_takeover_at_final_link_boundary(self) -> None:
        self._assert_transition_at_final_link("takeover")

    def test_emergency_stop_at_final_link_boundary(self) -> None:
        self._assert_transition_at_final_link("emergency")

    def test_global_emergency_stop_at_final_link_boundary(self) -> None:
        self._assert_transition_at_final_link("global_emergency")

    def test_session_expiry_at_final_link_boundary(self) -> None:
        from hive_runtime import git_loose_object_transaction as loose_module

        with tempfile.TemporaryDirectory() as tmp:
            repo = RealRepo(Path(tmp) / "repo")
            repo.write("a.txt", "a.txt original\n")
            repo.seed()
            repo.write("a.txt", "a.txt modified\n")

            clock = [1000.0]
            policy = ControlPolicy.build(
                rules=[
                    CapabilityRule.build(
                        Capability.GIT_WRITE, allowed_actions={ACTION}, allowed_workspace_roots={str(repo.root)}
                    )
                ]
            )
            plane = PermissionControlPlane(security_clock=lambda: clock[0], max_session_seconds=600)
            session = plane.create_session(policy, duration_seconds=30)
            capability = GovernedGitStageCapability(repo.root, plane)
            request = capability.prepare_stage_request(session, ["a.txt"])
            oid = request.arguments["path_bindings"][0]["blob_oid"]
            challenge = plane.create_approval_challenge(request)
            token = plane.approve_challenge_from_trusted_ui(challenge.challenge_id, session_id=session)
            permit = plane.authorize(request, approval_token=token)
            before_index = repo.index_bytes()

            real_fanout = loose_module._ensure_fanout_directory

            def fanout_then_expire(objects_dir, fanout):
                result = real_fanout(objects_dir, fanout)
                clock[0] += 31
                return result

            with mock.patch.object(loose_module, "_ensure_fanout_directory", fanout_then_expire):
                with self.assertRaises((SessionStateError, GitStageUnavailableError)):
                    capability.stage_paths(request, permit_token=permit.token)

            self.assertFalse((repo.root / ".git" / "objects" / oid[:2] / oid[2:]).exists())
            self.assertEqual(repo.index_bytes(), before_index)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())

    def test_later_blobs_and_index_are_not_published_after_transition(self) -> None:
        """Multi-file: a blob already published stays; later blobs and the index do not."""
        from hive_runtime import git_loose_object_transaction as loose_module

        with tempfile.TemporaryDirectory() as tmp:
            repo, harness = self._prepare(tmp, ("a.txt", "b.txt", "c.txt"))
            request = harness.request("a.txt", "b.txt", "c.txt")
            bound = [item["blob_oid"] for item in request.arguments["path_bindings"]]
            permit = harness.permit(request)
            before_index = repo.index_bytes()

            real_fanout = loose_module._ensure_fanout_directory
            real_publish = loose_module.LooseObjectPublisher.publish
            calls = {"published": 0}

            def counting_publish(self, preparation, compressed, *, pre_publish_check=None):
                result = real_publish(self, preparation, compressed, pre_publish_check=pre_publish_check)
                calls["published"] += 1
                return result

            def fanout_then_transition(objects_dir, fanout):
                result = real_fanout(objects_dir, fanout)
                # Only the second promotion is interrupted, so one blob is already
                # canonical when the transition happens.
                if calls["published"] == 1:
                    harness.plane.cancel_session(harness.session)
                return result

            with mock.patch.object(loose_module.LooseObjectPublisher, "publish", counting_publish), mock.patch.object(
                loose_module, "_ensure_fanout_directory", fanout_then_transition
            ):
                with self.assertRaises((SessionStateError, GitStageUnavailableError)):
                    harness.capability.stage_paths(request, permit_token=permit.token)

            present = [oid for oid in bound if (repo.root / ".git" / "objects" / oid[:2] / oid[2:]).exists()]
            self.assertEqual(present, [bound[0]], "only the first blob may be canonical")
            self.assertEqual(repo.index_bytes(), before_index)
            self.assertFalse((repo.root / ".git" / "index.lock").exists())
            # The already-published blob is valid and unreachable; it is not rolled back.
            self.assertEqual(git(repo.root, "cat-file", "-t", bound[0]).strip(), "blob")


if __name__ == "__main__":
    unittest.main()
