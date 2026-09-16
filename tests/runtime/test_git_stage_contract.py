from __future__ import annotations

import unittest

from hive_runtime.git_stage import GitStageUnavailableError
from hive_runtime.git_stage_index_codec import DULWICH_CANDIDATE_VERSION, DulwichGitIndexCodec, GitIndexCandidate, UnavailableGitIndexCodec
from hive_runtime.git_stage_contract import ABSENT_INDEX_IDENTITY, ABSENT_INDEX_SHA256, GIT_STAGE_ACTION, GIT_STAGE_ARGUMENT_KEYS, GIT_STAGE_CONTRACT, GIT_STAGE_TARGET_STATE, MAX_STAGE_PATHS, UNBORN_HEAD, GitStageIndexCandidateBinding, GitStageObjectStoreBinding, GitStageObservedState, GitStagePathBinding, GitStageReceipt, GitStageRequestBinding, GitStageWorktreeState, GitStageWorktreeStat

DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
OID = "1" * 40

def state(path: str = "src/app.py", *, digest: str = DIGEST_A) -> GitStageWorktreeState:
    return GitStageWorktreeState(path, "file:1", digest, 7)

class GitStageContractTests(unittest.TestCase):
    def test_fixed_contract_constants(self) -> None:
        self.assertEqual(GIT_STAGE_CONTRACT, "hive-git-stage-v1"); self.assertEqual(GIT_STAGE_ACTION, "git_stage_paths_v1"); self.assertEqual(GIT_STAGE_TARGET_STATE, "index_update"); self.assertEqual(MAX_STAGE_PATHS, 128)
        self.assertEqual(GIT_STAGE_ARGUMENT_KEYS, {
            "contract","repository_identity","repository_head","index_state","index_identity","index_sha256",
            "path_count","paths","worktree_states","path_bindings",
            "candidate_index_sha256","candidate_index_bytes",
            "object_store_contract","object_store_format","git_dir_identity","object_store_identity",
            "target_state",
        })

    def test_path_binding_rejects_malformed_identities(self) -> None:
        good = GitStagePathBinding("src/app.py", DIGEST_A, 7, "1" * 40)
        self.assertEqual(good.canonical()["blob_oid"], "1" * 40)
        with self.assertRaises(ValueError): GitStagePathBinding("", DIGEST_A, 7, "1" * 40)
        with self.assertRaises(ValueError): GitStagePathBinding("a.py", "short", 7, "1" * 40)
        with self.assertRaises(ValueError): GitStagePathBinding("a.py", DIGEST_A, -1, "1" * 40)
        with self.assertRaises(ValueError): GitStagePathBinding("a.py", DIGEST_A, 7, "xyz")

    def test_request_binding_binds_exact_candidate_store_and_has_no_raw_bytes(self) -> None:
        bound = GitStageRequestBinding(
            observed=GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state(),)),
            path_bindings=(GitStagePathBinding("src/app.py", DIGEST_A, 7, "2" * 40),),
            candidate=GitStageIndexCandidateBinding(DIGEST_A, 512),
            object_store=GitStageObjectStoreBinding("s", "sha1", "gitdir:1", "objects:1"),
        )
        arguments = bound.arguments()
        self.assertEqual(set(arguments), GIT_STAGE_ARGUMENT_KEYS)
        self.assertEqual(arguments["path_count"], 1)
        self.assertEqual(arguments["candidate_index_sha256"], DIGEST_A)
        self.assertEqual(arguments["candidate_index_bytes"], 512)
        self.assertEqual(arguments["object_store_identity"], "objects:1")
        self.assertEqual(arguments["target_state"], "index_update")
        # No raw byte payload may be representable in the approved metadata.
        for value in (arguments["paths"], arguments["worktree_states"], arguments["path_bindings"]):
            self.assertNotIsInstance(value, (bytes, bytearray))
        import json
        json.dumps(arguments)  # the approved metadata must be JSON-serializable

    def test_request_binding_rejects_binding_that_disagrees_with_observation(self) -> None:
        with self.assertRaises(ValueError):
            GitStageRequestBinding(
                observed=GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state(),)),
                path_bindings=(GitStagePathBinding("other.py", DIGEST_A, 7, "2" * 40),),
                candidate=GitStageIndexCandidateBinding(DIGEST_A, 512),
                object_store=GitStageObjectStoreBinding("s", "sha1", "g", "o"),
            )
        # Content digest disagrees with the approved worktree state.
        with self.assertRaises(ValueError):
            GitStageRequestBinding(
                observed=GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state(),)),
                path_bindings=(GitStagePathBinding("src/app.py", DIGEST_B, 7, "2" * 40),),
                candidate=GitStageIndexCandidateBinding(DIGEST_A, 512),
                object_store=GitStageObjectStoreBinding("s", "sha1", "g", "o"),
            )
        # Byte length disagrees with the approved worktree state.
        with self.assertRaises(ValueError):
            GitStageRequestBinding(
                observed=GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state(),)),
                path_bindings=(GitStagePathBinding("src/app.py", DIGEST_A, 999, "2" * 40),),
                candidate=GitStageIndexCandidateBinding(DIGEST_A, 512),
                object_store=GitStageObjectStoreBinding("s", "sha1", "g", "o"),
            )

    def test_candidate_and_store_bindings_are_strict(self) -> None:
        with self.assertRaises(ValueError): GitStageIndexCandidateBinding("short", 10)
        with self.assertRaises(ValueError): GitStageIndexCandidateBinding(DIGEST_A, 0)
        with self.assertRaises(ValueError): GitStageObjectStoreBinding("", "sha1", "g", "o")

    def test_worktree_state_is_redacted_metadata_only(self) -> None:
        observed = state()
        canonical = observed.canonical()
        self.assertEqual(set(canonical), {"path","file_identity","content_sha256","content_bytes","state","stat"})
        self.assertNotIn("content", canonical)
        self.assertNotIn("bytes", canonical)
        # The stat record is bounded numeric metadata only: no raw file bytes.
        self.assertIsNone(canonical["stat"])
        stats = {"dev":1,"ino":2,"mode":0o100644,"uid":0,"gid":0,"size":3,"mtime_s":1,"mtime_ns":0,"ctime_s":1,"ctime_ns":0}
        with_stat = GitStageWorktreeState("src/app.py", "file:1", DIGEST_A, 3, stat=GitStageWorktreeStat(**stats))
        self.assertEqual(with_stat.canonical()["stat"], stats)
        self.assertTrue(all(isinstance(value, int) for value in with_stat.canonical()["stat"].values()))
        # Access time is deliberately absent: Git does not store it in an index
        # entry and observing a file updates it, which would make an unchanged
        # repository report as stale.
        self.assertNotIn("atime_s", stats)
        self.assertNotIn("atime_ns", stats)

    def test_rejects_non_regular_state(self) -> None:
        with self.assertRaises(ValueError): GitStageWorktreeState("src/link", "file:1", DIGEST_A, 3, "symlink")

    def test_rejects_bad_digest(self) -> None:
        with self.assertRaises(ValueError): GitStageWorktreeState("src/app.py", "file:1", "ABC", 3)

    def test_observed_state_requires_deterministic_unique_paths(self) -> None:
        with self.assertRaises(ValueError): GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state("z.py"), state("a.py")))
        with self.assertRaises(ValueError): GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state("a.py"), state("a.py")))

    def test_absent_index_requires_explicit_sentinels(self) -> None:
        value = GitStageObservedState("repo:1", UNBORN_HEAD, "absent", ABSENT_INDEX_IDENTITY, ABSENT_INDEX_SHA256, (state(),)); self.assertEqual(value.index_state, "absent")
        with self.assertRaises(ValueError): GitStageObservedState("repo:1", UNBORN_HEAD, "absent", "wrong", "wrong", (state(),))

    def test_regular_index_requires_identity_and_sha256(self) -> None:
        value = GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state(),)); self.assertEqual(value.index_sha256, DIGEST_B)
        with self.assertRaises(ValueError): GitStageObservedState("repo:1", OID, "regular", "", DIGEST_B, (state(),))

    def test_receipt_contains_no_raw_content(self) -> None:
        receipt = GitStageReceipt("workspace", "repo:1", OID, DIGEST_A, DIGEST_B, ("src/app.py",), "index_updated"); self.assertFalse(hasattr(receipt, "content")); self.assertEqual(receipt.staged_paths, ("src/app.py",))

    def test_index_codec_boundary_is_inert_until_backend_approval(self) -> None:
        observed = GitStageObservedState("repo:1", OID, "regular", "index:1", DIGEST_B, (state(),))
        with self.assertRaises(GitStageUnavailableError): UnavailableGitIndexCodec().build_candidate(observed, ("src/app.py",))
        self.assertEqual(DULWICH_CANDIDATE_VERSION, "1.2.15")
        # The reviewed backend is now proven, so the boundary that still matters is
        # that a real codec cannot produce candidate bytes without the full governed
        # inputs: an authority-free stage plan and the exact observed source state.
        with self.assertRaises(GitStageUnavailableError): DulwichGitIndexCodec().build_candidate(observed, ("src/app.py",))

    def test_index_candidate_requires_deterministic_redacted_envelope(self) -> None:
        candidate = GitIndexCandidate("test-codec", DIGEST_B, ("a.py","z.py"), b"candidate-index")
        self.assertEqual(candidate.paths, ("a.py","z.py")); self.assertEqual(candidate.source_index_sha256, DIGEST_B)
        with self.assertRaises(ValueError): GitIndexCandidate("test-codec", DIGEST_B, ("z.py","a.py"), b"x")
        with self.assertRaises(ValueError): GitIndexCandidate("test-codec", "bad", ("a.py",), b"x")

if __name__ == "__main__": unittest.main()
