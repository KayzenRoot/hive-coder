from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
import zlib
from pathlib import Path

from hive_runtime.git_loose_object_transaction import LOOSE_OBJECT_TRANSACTION_CONTRACT, PreAuthorityLooseObjectTransaction, prepare_loose_blob
from hive_runtime.git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError


def _repo(root: Path) -> None:
    git = root / ".git"; (git / "objects" / "info").mkdir(parents=True); (git / "objects" / "pack").mkdir(); (git / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")


def _install(root: Path, prepared, compressed: bytes) -> Path:
    path = root / ".git" / prepared.relative_object_path; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(compressed); return path


@unittest.skipIf(os.name == "nt", "POSIX pre-authority object-store proof")
class GitLooseObjectTransactionTests(unittest.TestCase):
    def test_preparation_matches_canonical_git_blob_and_fanout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); content = b"hello\n"; prepared, compressed = prepare_loose_blob(root, content); oid = hashlib.sha1(b"blob 6\x00hello\n").hexdigest()
            self.assertEqual(prepared.contract, LOOSE_OBJECT_TRANSACTION_CONTRACT); self.assertEqual(prepared.candidate.oid, oid); self.assertEqual(prepared.fanout, oid[:2]); self.assertEqual(prepared.leaf, oid[2:]); self.assertEqual(prepared.relative_object_path, f"objects/{oid[:2]}/{oid[2:]}"); self.assertEqual(zlib.decompress(compressed), b"blob 6\x00hello\n"); self.assertEqual(prepared.compressed_sha256, hashlib.sha256(compressed).hexdigest())

    def test_binary_bytes_are_framed_as_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); content = b"\x00\xffbinary\x00"; prepared, compressed = prepare_loose_blob(root, content)
            self.assertEqual(zlib.decompress(compressed), b"blob " + str(len(content)).encode("ascii") + b"\x00" + content); self.assertEqual(len(prepared.candidate.oid), 40)

    def test_prepare_creates_no_fanout_temp_or_object_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); before = sorted(str(p.relative_to(root)) for p in root.rglob("*")); prepared, _ = prepare_loose_blob(root, b"source"); after = sorted(str(p.relative_to(root)) for p in root.rglob("*")); self.assertEqual(before, after); self.assertFalse((root / ".git" / prepared.relative_object_path).exists())

    def test_missing_existing_object_is_distinct_from_unsafe_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); tx = PreAuthorityLooseObjectTransaction(root); prepared, _ = tx.prepare(b"source"); self.assertIsNone(tx.inspect_existing(prepared))

    def test_exact_existing_object_is_proven_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); tx = PreAuthorityLooseObjectTransaction(root); prepared, compressed = tx.prepare(b"source"); path = _install(root, prepared, compressed); before = path.read_bytes(); proof = tx.inspect_existing(prepared)
            self.assertIsNotNone(proof); assert proof is not None
            self.assertEqual(proof.oid, prepared.candidate.oid); self.assertEqual(proof.content_sha256, prepared.candidate.content_sha256); self.assertEqual(proof.content_bytes, prepared.candidate.content_bytes); self.assertEqual(path.read_bytes(), before)

    def test_conflicting_corrupt_wrong_type_or_wrong_length_object_fails_closed(self) -> None:
        payloads = (b"not-zlib", zlib.compress(b"tree 0\x00"), zlib.compress(b"blob 99\x00short"), zlib.compress(b"blob 7\x00changed"))
        for payload in payloads:
            with self.subTest(payload=payload[:12]), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _repo(root); tx = PreAuthorityLooseObjectTransaction(root); prepared, _ = tx.prepare(b"source"); _install(root, prepared, payload)
                with self.assertRaises(GitStageUnsupportedRepositoryError): tx.inspect_existing(prepared)

    def test_symlink_existing_object_never_looks_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); tx = PreAuthorityLooseObjectTransaction(root); prepared, compressed = tx.prepare(b"source"); target = root / "foreign-object"; target.write_bytes(compressed); path = root / ".git" / prepared.relative_object_path; path.parent.mkdir(parents=True); path.symlink_to(target)
            with self.assertRaises(GitStageUnsupportedRepositoryError): tx.inspect_existing(prepared)

    def test_store_identity_change_invalidates_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); tx = PreAuthorityLooseObjectTransaction(root); prepared, _ = tx.prepare(b"source"); objects = root / ".git" / "objects"; moved = root / ".git" / "objects-old"; objects.rename(moved); objects.mkdir()
            with self.assertRaises(GitStageUnavailableError): tx.inspect_existing(prepared)

    def test_transaction_has_verification_but_no_publication_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); tx = PreAuthorityLooseObjectTransaction(root); prepared, compressed = tx.prepare(b"source"); self.assertFalse(tx.mutation_authority_enabled); self.assertIsNone(tx.inspect_existing(prepared))
            with self.assertRaises(GitStageUnavailableError): tx.publish(prepared, compressed)


if __name__ == "__main__": unittest.main()
