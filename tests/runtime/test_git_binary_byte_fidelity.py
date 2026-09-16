from __future__ import annotations

"""Binary byte-fidelity regression for the WO-0023 Git modules.

On Windows, ``os.open`` without ``O_BINARY`` uses the CRT **text** mode, where:

* ``os.read`` stops at the first ``0x1A`` (Ctrl-Z) byte, silently truncating the
  digest of any Git metadata, index or worktree file that contains one; and
* ``os.write`` translates every ``LF`` into ``CRLF``, corrupting binary bytes.

Git index entries and compressed loose objects routinely contain both bytes, so
both behaviours are correctness defects, not cosmetic ones. These tests fail if
``O_BINARY`` is ever dropped from a Git open path.
"""

import hashlib
import os
import tempfile
import unittest
import zlib
from pathlib import Path

from hive_runtime.git_loose_object_transaction import PreAuthorityLooseObjectTransaction, prepare_loose_blob
from hive_runtime.git_stage_observer import PosixGitStageObserver
from hive_runtime.git_stage_transaction import PosixGitIndexTransaction

CTRL_Z = b"\x1a"


def _repo(root: Path) -> None:
    git = root / ".git"
    (git / "objects" / "info").mkdir(parents=True)
    (git / "objects" / "pack").mkdir()
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii")
    (git / "refs" / "heads" / "main").write_text("2" * 40 + "\n", encoding="ascii")


class BinaryByteFidelityTests(unittest.TestCase):
    def test_worktree_digest_is_exact_for_content_containing_ctrl_z(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            payload = b"before" + CTRL_Z + b"after\nline2\n"
            (root / "binary.bin").write_bytes(payload)

            state = PosixGitStageObserver(root).observe(["binary.bin"])
            observed = state.worktree_states[0]
            self.assertEqual(observed.content_bytes, len(payload))
            self.assertEqual(observed.content_sha256, hashlib.sha256(payload).hexdigest())

    def test_index_digest_is_exact_for_index_bytes_containing_ctrl_z(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            # A real Git index is full of binary SHA-1 bytes, so 0x1A is common.
            index = b"DIRC" + b"\x00\x00\x00\x02\x00\x00\x00\x00" + CTRL_Z + b"\x00" * 32
            index = index + hashlib.sha1(index).digest()
            (root / ".git" / "index").write_bytes(index)
            (root / "a.txt").write_bytes(b"a")

            state = PosixGitStageObserver(root).observe(["a.txt"])
            self.assertEqual(state.index_sha256, hashlib.sha256(index).hexdigest())

    def test_index_lock_write_preserves_lf_and_ctrl_z_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            git = root / ".git"
            (git / "index").write_bytes(b"original")
            candidate = b"DIRC\n\x1a\x00binary\r\npayload"
            tx = PosixGitIndexTransaction(git)
            try:
                tx.acquire()
                tx.write_prepared_index(candidate)
                on_disk = (git / "index.lock").read_bytes()
                self.assertEqual(on_disk, candidate)
                # The live index must never be written by preparation.
                self.assertEqual((git / "index").read_bytes(), b"original")
            finally:
                tx.close()
            self.assertFalse((git / "index.lock").exists())

    def test_existing_loose_object_with_ctrl_z_is_proven_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            # zlib output is deterministic per version but not guaranteed to contain
            # 0x1A for arbitrary input, so select a payload whose compressed form does.
            content = None
            for index in range(4000):
                candidate = b"payload-%d\x1atail\n" % index
                framed = b"blob " + str(len(candidate)).encode("ascii") + b"\x00" + candidate
                if CTRL_Z in zlib.compress(framed):
                    content = candidate
                    break
            self.assertIsNotNone(content, "no ctrl-Z-bearing compressed fixture found")
            assert content is not None

            tx = PreAuthorityLooseObjectTransaction(root)
            prepared, compressed = tx.prepare(content)
            self.assertIn(CTRL_Z, compressed)
            path = root / ".git" / prepared.relative_object_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(compressed)

            proof = tx.inspect_existing(prepared)
            self.assertIsNotNone(proof)
            assert proof is not None
            self.assertEqual(proof.content_sha256, hashlib.sha256(content).hexdigest())
            self.assertEqual(proof.content_bytes, len(content))
            self.assertEqual(zlib.decompress(compressed), b"blob " + str(len(content)).encode() + b"\x00" + content)

    def test_truncated_digest_would_have_been_silently_wrong(self) -> None:
        """Guard the fixture itself: prove the ctrl-Z fixture is not accidentally short."""
        payload = b"before" + CTRL_Z + b"after\n"
        self.assertGreater(len(payload), payload.index(CTRL_Z) + 1)
        self.assertNotEqual(hashlib.sha256(payload).hexdigest(), hashlib.sha256(payload[: payload.index(CTRL_Z)]).hexdigest())


if __name__ == "__main__":
    unittest.main()
