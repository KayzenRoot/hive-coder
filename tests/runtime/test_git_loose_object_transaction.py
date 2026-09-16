from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
import zlib
from pathlib import Path

from hive_runtime.git_loose_object_transaction import (
    LOOSE_OBJECT_TRANSACTION_CONTRACT,
    PreAuthorityLooseObjectTransaction,
    prepare_loose_blob,
)
from hive_runtime.git_stage import GitStageUnavailableError


def _repo(root: Path) -> None:
    git = root / ".git"
    (git / "objects" / "info").mkdir(parents=True)
    (git / "objects" / "pack").mkdir()
    (git / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")


@unittest.skipIf(os.name == "nt", "POSIX pre-authority object-store proof")
class GitLooseObjectTransactionTests(unittest.TestCase):
    def test_preparation_matches_canonical_git_blob_and_fanout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); content = b"hello\n"
            prepared, compressed = prepare_loose_blob(root, content)
            oid = hashlib.sha1(b"blob 6\x00hello\n").hexdigest()
            self.assertEqual(prepared.contract, LOOSE_OBJECT_TRANSACTION_CONTRACT)
            self.assertEqual(prepared.candidate.oid, oid)
            self.assertEqual(prepared.fanout, oid[:2])
            self.assertEqual(prepared.leaf, oid[2:])
            self.assertEqual(prepared.relative_object_path, f"objects/{oid[:2]}/{oid[2:]}")
            self.assertEqual(zlib.decompress(compressed), b"blob 6\x00hello\n")
            self.assertEqual(prepared.compressed_sha256, hashlib.sha256(compressed).hexdigest())
            self.assertEqual(prepared.compressed_bytes, len(compressed))

    def test_binary_bytes_are_framed_as_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); content = b"\x00\xffbinary\x00"
            prepared, compressed = prepare_loose_blob(root, content)
            self.assertEqual(zlib.decompress(compressed), b"blob " + str(len(content)).encode("ascii") + b"\x00" + content)
            self.assertEqual(len(prepared.candidate.oid), 40)

    def test_prepare_creates_no_fanout_temp_or_object_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            prepared, _ = prepare_loose_blob(root, b"source")
            after = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            self.assertEqual(before, after)
            self.assertFalse((root / ".git" / prepared.relative_object_path).exists())

    def test_transaction_exposes_no_enabled_mutation_authority(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); tx = PreAuthorityLooseObjectTransaction(root); prepared, compressed = tx.prepare(b"source")
            self.assertFalse(tx.mutation_authority_enabled)
            with self.assertRaises(GitStageUnavailableError): tx.inspect_existing(prepared)
            with self.assertRaises(GitStageUnavailableError): tx.publish(prepared, compressed)
            tx.close()

    def test_preparation_binds_store_identity_and_compressed_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); prepared, compressed = prepare_loose_blob(root, b"approved")
            self.assertTrue(prepared.store.repository_local)
            self.assertTrue(prepared.store.objects_identity.startswith("posix-dir:"))
            self.assertEqual(hashlib.sha256(compressed).hexdigest(), prepared.compressed_sha256)


if __name__ == "__main__":
    unittest.main()
