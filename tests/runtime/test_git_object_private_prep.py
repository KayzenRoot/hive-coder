from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.git_loose_object_transaction import MAX_LOOSE_OBJECT_COMPRESSED_BYTES, prepare_loose_blob
from hive_runtime.git_object_private_prep import (
    PRIVATE_OBJECT_PREP_CONTRACT,
    PRIVATE_TEMP_DIRNAME,
    PrivateObjectPreparer,
)
from hive_runtime.git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError


def _repo(root: Path) -> None:
    git = root / ".git"
    (git / "objects" / "info").mkdir(parents=True)
    (git / "objects" / "pack").mkdir()
    (git / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")


class PrivateObjectPreparationTests(unittest.TestCase):
    """Pre-authority temp material only: never publishes a final Git object."""

    def test_materialize_creates_an_owned_temp_outside_the_object_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"payload\n")
            plan = preparer.plan(prepared, compressed)

            self.assertEqual(plan.contract, PRIVATE_OBJECT_PREP_CONTRACT)
            self.assertEqual(plan.oid, prepared.candidate.oid)
            self.assertEqual(plan.compressed_sha256, hashlib.sha256(compressed).hexdigest())

            temp = preparer.materialize_private_temp(plan, compressed)
            path = Path(temp.identity.path)
            self.assertTrue(path.is_file())
            self.assertTrue(temp.relative_path.startswith(PRIVATE_TEMP_DIRNAME + "/"))
            self.assertEqual(path.read_bytes(), compressed)

            # Repository-local and never inside the object store.
            self.assertEqual(path.parent.parent, (root / ".git").resolve())
            self.assertNotIn("objects", temp.relative_path)
            self.assertFalse((root / ".git" / prepared.relative_object_path).exists())
            self.assertFalse((root / ".git" / "objects" / prepared.fanout).exists())
            preparer.cleanup_private_temp(temp)

    def test_materialized_bytes_match_the_planned_digest_and_length(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"binary\x00\x1apayload\n")
            plan = preparer.plan(prepared, compressed)
            temp = preparer.materialize_private_temp(plan, compressed)
            on_disk = Path(temp.identity.path).read_bytes()
            self.assertEqual(on_disk, compressed)
            self.assertEqual(hashlib.sha256(on_disk).hexdigest(), plan.compressed_sha256)
            self.assertEqual(len(on_disk), plan.compressed_bytes)
            self.assertEqual(temp.compressed_bytes, len(compressed))

    def test_temp_is_bounded_and_rejects_an_oversized_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"small\n")
            plan = preparer.plan(prepared, compressed)
            oversized = b"\x00" * (MAX_LOOSE_OBJECT_COMPRESSED_BYTES + 1)
            with self.assertRaises(GitStageUnsupportedRepositoryError):
                preparer.materialize_private_temp(plan, oversized)

    def test_payload_must_still_match_the_approved_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"small\n")
            plan = preparer.plan(prepared, compressed)
            with self.assertRaises(ValueError):
                preparer.materialize_private_temp(plan, compressed + b"x")
            with self.assertRaises(TypeError):
                preparer.materialize_private_temp(plan, bytearray(compressed))  # type: ignore[arg-type]

    def test_cleanup_removes_only_the_owned_identity_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"payload\n")
            plan = preparer.plan(prepared, compressed)

            # Identity changed (the pathname is now a directory, not our regular file):
            # the temporary must NOT be removed.
            foreign = preparer.materialize_private_temp(plan, compressed)
            foreign_path = Path(foreign.identity.path)
            foreign_path.unlink()
            foreign_path.mkdir()
            preparer.cleanup_private_temp(foreign)
            self.assertTrue(foreign_path.is_dir())

            owned = preparer.materialize_private_temp(plan, compressed)
            owned_path = Path(owned.identity.path)
            preparer.cleanup_private_temp(owned)
            self.assertFalse(owned_path.exists())
            preparer.cleanup_private_temp(owned)  # idempotent
            self.assertFalse(owned_path.exists())

    def test_private_temp_creation_leaves_the_object_store_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            objects = root / ".git" / "objects"
            before = sorted(str(p.relative_to(root)) for p in objects.rglob("*"))
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"payload\n")
            temp = preparer.materialize_private_temp(preparer.plan(prepared, compressed), compressed)
            after = sorted(str(p.relative_to(root)) for p in objects.rglob("*"))
            self.assertEqual(before, after)
            preparer.cleanup_private_temp(temp)

    def test_non_directory_temp_path_fails_closed(self) -> None:
        """A plain file where the Hive-owned temporary directory belongs must fail closed.

        This is the cross-platform half of the symlink/reparse rejection: the
        directory is proven, not assumed.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / ".git" / PRIVATE_TEMP_DIRNAME).write_bytes(b"not-a-directory")
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"payload\n")
            plan = preparer.plan(prepared, compressed)
            with self.assertRaises(GitStageUnsupportedRepositoryError):
                preparer.materialize_private_temp(plan, compressed)

    def test_symlinked_temp_directory_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as elsewhere:
            root = Path(tmp)
            _repo(root)
            link = root / ".git" / PRIVATE_TEMP_DIRNAME
            try:
                link.symlink_to(Path(elsewhere), target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink fixture unavailable on this platform/privilege level: {type(exc).__name__}")
            preparer = PrivateObjectPreparer(root)
            prepared, compressed = prepare_loose_blob(root, b"payload\n")
            plan = preparer.plan(prepared, compressed)
            with self.assertRaises(GitStageUnsupportedRepositoryError):
                preparer.materialize_private_temp(plan, compressed)

    def test_repository_root_is_required_and_publish_stays_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            unprefixed = PrivateObjectPreparer()
            prepared, compressed = prepare_loose_blob(root, b"payload\n")
            plan = unprefixed.plan(prepared, compressed)
            self.assertFalse(unprefixed.mutation_authority_enabled)
            with self.assertRaises(GitStageUnavailableError):
                unprefixed.materialize_private_temp(plan, compressed)
            with self.assertRaises(GitStageUnavailableError):
                unprefixed.publish(plan)

    def test_preparer_exposes_no_public_stage_or_commit_authority(self) -> None:
        preparer = PrivateObjectPreparer()
        for forbidden in ("publish_final", "stage_paths", "commit", "add"):
            self.assertFalse(hasattr(preparer, forbidden))
        self.assertFalse(preparer.mutation_authority_enabled)


if __name__ == "__main__":
    unittest.main()
