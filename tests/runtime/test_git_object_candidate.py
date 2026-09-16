from __future__ import annotations

import hashlib
import unittest

from hive_runtime.git_object_candidate import (
    GIT_BLOB_CANDIDATE_CONTRACT,
    GIT_OBJECT_FORMAT,
    MAX_GIT_BLOB_BYTES,
    GitBlobCandidate,
    prepare_git_blob_candidate,
)


class GitBlobCandidateTests(unittest.TestCase):
    def test_contract_and_object_format_are_fixed(self) -> None:
        self.assertEqual(GIT_BLOB_CANDIDATE_CONTRACT, "hive-git-blob-candidate-v1")
        self.assertEqual(GIT_OBJECT_FORMAT, "sha1")

    def test_computes_canonical_git_blob_oid(self) -> None:
        content = b"hello\n"
        candidate = prepare_git_blob_candidate(content)
        expected = hashlib.sha1(b"blob 6\x00hello\n").hexdigest()
        self.assertEqual(candidate.oid, expected)
        self.assertEqual(candidate.content_sha256, hashlib.sha256(content).hexdigest())
        self.assertEqual(candidate.content_bytes, 6)

    def test_binary_and_nul_content_are_data_not_control(self) -> None:
        content = b"\x00\xff\x10binary\x00"
        candidate = prepare_git_blob_candidate(content)
        self.assertEqual(candidate.content_bytes, len(content))
        self.assertEqual(len(candidate.oid), 40)

    def test_size_is_part_of_git_object_identity(self) -> None:
        left = prepare_git_blob_candidate(b"a")
        right = prepare_git_blob_candidate(b"a\x00")
        self.assertNotEqual(left.oid, right.oid)
        self.assertNotEqual(left.content_sha256, right.content_sha256)

    def test_changed_content_changes_oid_and_approval_digest(self) -> None:
        before = prepare_git_blob_candidate(b"approved")
        after = prepare_git_blob_candidate(b"changed")
        self.assertNotEqual(before.oid, after.oid)
        self.assertNotEqual(before.content_sha256, after.content_sha256)

    def test_rejects_non_bytes_and_governed_size_overflow(self) -> None:
        with self.assertRaises(TypeError):
            prepare_git_blob_candidate(bytearray(b"x"))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            prepare_git_blob_candidate(b"x" * (MAX_GIT_BLOB_BYTES + 1))

    def test_candidate_is_inert_and_contains_no_raw_content_or_authority(self) -> None:
        candidate = prepare_git_blob_candidate(b"secret-source-bytes")
        self.assertIsInstance(candidate, GitBlobCandidate)
        self.assertFalse(hasattr(candidate, "content"))
        self.assertFalse(hasattr(candidate, "publish"))
        self.assertFalse(hasattr(candidate, "permit_token"))
        self.assertFalse(hasattr(candidate, "path"))
        self.assertEqual(candidate.contract, GIT_BLOB_CANDIDATE_CONTRACT)


if __name__ == "__main__":
    unittest.main()
