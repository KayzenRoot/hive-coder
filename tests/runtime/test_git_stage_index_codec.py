from __future__ import annotations

import unittest

from hive_runtime.git_stage import GitStageUnavailableError
from hive_runtime.git_stage_contract import GitStageObservedState, GitStageWorktreeState
from hive_runtime.git_stage_index_codec import (
    DULWICH_CANDIDATE_VERSION,
    INDEX_CODEC_CONTRACT,
    DulwichIndexCodecCandidate,
    GitIndexCandidate,
    UnavailableGitIndexCodec,
)


SHA_A = "a" * 64
SHA_B = "b" * 64
OID = "1" * 40


def observed() -> GitStageObservedState:
    return GitStageObservedState(
        "repo:1",
        OID,
        "regular",
        "index:1",
        SHA_A,
        (GitStageWorktreeState("src/app.py", "file:1", SHA_B, 7),),
    )


class GitStageIndexCodecAcceptanceTests(unittest.TestCase):
    def test_contract_and_reviewed_candidate_version_are_fixed(self) -> None:
        self.assertEqual(INDEX_CODEC_CONTRACT, "hive-git-index-codec-v1")
        self.assertEqual(DULWICH_CANDIDATE_VERSION, "1.2.15")

    def test_default_codec_fails_closed_without_runtime_dependency(self) -> None:
        codec = UnavailableGitIndexCodec()
        with self.assertRaises(GitStageUnavailableError):
            codec.build_candidate(observed(), ["src/app.py"])

    def test_dulwich_candidate_cannot_be_instantiated_before_approval(self) -> None:
        with self.assertRaises(GitStageUnavailableError):
            DulwichIndexCodecCandidate()

    def test_candidate_is_data_only_and_binds_source_index_and_paths(self) -> None:
        candidate = GitIndexCandidate("proof-codec", SHA_A, ("src/app.py",), b"DIRC-candidate")
        self.assertEqual(candidate.source_index_sha256, SHA_A)
        self.assertEqual(candidate.paths, ("src/app.py",))
        self.assertEqual(candidate.serialized, b"DIRC-candidate")
        self.assertFalse(hasattr(candidate, "publish"))
        self.assertFalse(hasattr(candidate, "permit_token"))

    def test_candidate_rejects_bad_digest_empty_unsorted_duplicate_paths_and_nonbytes(self) -> None:
        invalid = (
            ("short", ("src/app.py",), b"x"),
            (SHA_A, (), b"x"),
            (SHA_A, ("z.py", "a.py"), b"x"),
            (SHA_A, ("a.py", "a.py"), b"x"),
        )
        for digest, paths, payload in invalid:
            with self.subTest(digest=digest, paths=paths):
                with self.assertRaises(ValueError):
                    GitIndexCandidate("proof-codec", digest, paths, payload)
        with self.assertRaises(TypeError):
            GitIndexCandidate("proof-codec", SHA_A, ("a.py",), bytearray(b"x"))  # type: ignore[arg-type]

    @unittest.skip("PREBUILT: enable only after reviewed Dulwich dependency is governed")
    def test_real_codec_round_trip_preserves_supported_index_semantics(self) -> None:
        self.fail("must prove parse/serialize round-trip before enabling backend")

    @unittest.skip("PREBUILT: real codec must reject unsupported index envelopes")
    def test_real_codec_rejects_sparse_split_conflicted_and_unknown_required_extensions(self) -> None:
        self.fail("must prove fail-closed unsupported index handling")

    @unittest.skip("PREBUILT: real codec must prove executable-extension isolation")
    def test_real_codec_cannot_invoke_porcelain_shell_hooks_filters_network_or_credentials(self) -> None:
        self.fail("must prove authority isolation")


if __name__ == "__main__":
    unittest.main()
