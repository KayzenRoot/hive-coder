from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.git_object_store_inspector import (
    OBJECT_STORE_INSPECTOR_CONTRACT,
    SUPPORTED_OBJECT_FORMAT,
    inspect_local_object_store,
)
from hive_runtime.git_stage import GitStageUnsupportedRepositoryError


def _repo(root: Path, config: bytes = b"[core]\n\trepositoryformatversion = 0\n") -> None:
    git = root / ".git"
    (git / "objects" / "info").mkdir(parents=True)
    (git / "objects" / "pack").mkdir()
    (git / "config").write_bytes(config)


@unittest.skipIf(os.name == "nt", "POSIX object-store proof")
class GitObjectStoreInspectorTests(unittest.TestCase):
    def test_accepts_only_repository_local_sha1_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root)
            envelope = inspect_local_object_store(root)
            self.assertEqual(envelope.contract, OBJECT_STORE_INSPECTOR_CONTRACT)
            self.assertEqual(envelope.object_format, SUPPORTED_OBJECT_FORMAT)
            self.assertTrue(envelope.repository_local)
            self.assertTrue(envelope.git_dir_identity.startswith("posix-dir:"))
            self.assertTrue(envelope.objects_identity.startswith("posix-dir:"))

    def test_rejects_missing_symlink_or_non_directory_object_store(self) -> None:
        for kind in ("missing", "file", "symlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _repo(root); objects = root / ".git" / "objects"
                for child in sorted(objects.rglob("*"), reverse=True):
                    if child.is_dir(): child.rmdir()
                    else: child.unlink()
                objects.rmdir()
                if kind == "file": objects.write_bytes(b"not-a-store")
                elif kind == "symlink": objects.symlink_to(root)
                with self.assertRaises(GitStageUnsupportedRepositoryError): inspect_local_object_store(root)

    def test_rejects_object_alternates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); (root / ".git" / "objects" / "info" / "alternates").write_text("/external/objects\n", encoding="ascii")
            with self.assertRaises(GitStageUnsupportedRepositoryError): inspect_local_object_store(root)

    def test_rejects_http_alternates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); (root / ".git" / "objects" / "info" / "http-alternates").write_text("https://example.invalid/objects\n", encoding="ascii")
            with self.assertRaises(GitStageUnsupportedRepositoryError): inspect_local_object_store(root)

    def test_rejects_sha256_partial_clone_promisor_and_worktree_config(self) -> None:
        configs = (
            b"[extensions]\n objectFormat = sha256\n",
            b"[extensions]\n partialClone = origin\n",
            b"[remote \"origin\"]\n promisor = true\n",
            b"[extensions]\n worktreeConfig = true\n",
        )
        for config in configs:
            with self.subTest(config=config), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp); _repo(root, config)
                with self.assertRaises(GitStageUnsupportedRepositoryError): inspect_local_object_store(root)

    def test_unsafe_config_never_looks_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); config = root / ".git" / "config"; config.unlink(); config.symlink_to(root / ".git" / "objects")
            with self.assertRaises(GitStageUnsupportedRepositoryError): inspect_local_object_store(root)

    def test_inspector_has_no_mutation_or_publication_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); _repo(root); before = sorted(str(p.relative_to(root)) for p in root.rglob("*")); envelope = inspect_local_object_store(root); after = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
            self.assertEqual(before, after)
            self.assertFalse(hasattr(envelope, "publish"))
            self.assertFalse(hasattr(envelope, "write"))
            self.assertFalse(hasattr(envelope, "permit_token"))


if __name__ == "__main__":
    unittest.main()
