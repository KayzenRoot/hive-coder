from __future__ import annotations

"""Real-Git semantic proof for the WO-0023 index candidate.

This lane exists because "the candidate parses" is not proof. The defect it
guards against is semantic: Git's ``TREE`` extension is a cache-tree whose nodes
record tree object ids describing the *previous* index. Appending the previous
region to a candidate that changed an entry gives Git a structurally consistent
but stale cache. Git does not detect that, and ``write-tree`` silently reuses the
old subtree, discarding the staged change with no error at all.

The proof therefore compares the produced tree against the tree Git itself
produces for the identical change, and it also constructs a deliberately
stale-TREE-carrying candidate so the lane fails if the regression ever returns.

Git is used strictly as a fixture generator and oracle. No product runtime module
in this path executes a process.
"""

import hashlib
import io
import os
import shutil
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from hive_runtime.git_index_envelope import inspect_git_index_envelope
from hive_runtime.git_loose_object_transaction import prepare_loose_blob
from hive_runtime.git_stage import GitStagePreparation
from hive_runtime.git_stage_index_codec import DulwichGitIndexCodec
from hive_runtime.git_stage_observer import PosixGitStageObserver
from hive_runtime.git_stage_plan import bind_stage_plan

try:  # pragma: no cover - exercised by CI, which installs the governed dependency
    import dulwich  # noqa: F401

    _DULWICH_AVAILABLE = True
    _DULWICH_REASON = ""
except ImportError:  # pragma: no cover
    _DULWICH_AVAILABLE = False
    _DULWICH_REASON = "governed dependency dulwich==1.2.15 is not materialized in this interpreter"

_GIT = shutil.which("git")
_GIT_REASON = "the real-Git semantic proof requires a git executable as fixture generator and oracle"


def _git(repo: Path, *args: str, index: Path | None = None) -> str:
    env = dict(os.environ)
    if index is not None:
        env["GIT_INDEX_FILE"] = str(index)
    result = subprocess.run(
        ["git", *args], cwd=str(repo), env=env, capture_output=True, text=True, timeout=120, check=False
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _extension_region(index_bytes: bytes) -> bytes:
    """Test-local extraction of the raw extension region.

    Deliberately implemented here rather than reusing product code, so the
    negative control constructs the unsafe artifact independently of the module
    under test.
    """
    payload = index_bytes[:-20]
    offset = 12
    for _ in range(struct.unpack(">I", index_bytes[8:12])[0]):
        flags = struct.unpack(">H", payload[offset + 60 : offset + 62])[0]
        name_length = flags & 0x0FFF
        if name_length < 0x0FFF:
            name_end = offset + 62 + name_length
        else:
            name_end = payload.find(b"\x00", offset + 62)
        entry_size = name_end - offset + 1
        offset += (entry_size + 7) & ~7
    return payload[offset:]


class _RealRepo:
    """A throwaway real Git repository used as fixture and oracle."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True)
        _git(root, "init", "-q", ".")
        _git(root, "config", "core.autocrlf", "false")
        _git(root, "config", "user.email", "proof@hive")
        _git(root, "config", "user.name", "hive-proof")

    def write(self, relative: str, content: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")

    def seed(self) -> bytes:
        """Create a committed tree and return the resulting index bytes."""
        _git(self.root, "add", ".")
        _git(self.root, "commit", "-qm", "seed")
        return self.index_bytes()

    def index_bytes(self) -> bytes:
        return (self.root / ".git" / "index").read_bytes()

    def stage_with_git(self, *paths: str) -> None:
        _git(self.root, "add", *paths)

    def write_tree(self, index: Path | None = None) -> str:
        return _git(self.root, "write-tree", index=index).strip()

    def index_listing(self, index: Path | None = None) -> str:
        return _git(self.root, "ls-files", "--stage", index=index).strip()

    def publish_blob(self, relative: str) -> str:
        return _git(self.root, "hash-object", "-w", relative).strip()


def _hive_candidate(repo: _RealRepo, paths: tuple[str, ...], source_index: bytes, *, carry_tree: bool):
    """Build a Hive candidate. ``carry_tree`` reproduces the old, unsafe behavior."""
    observer = PosixGitStageObserver(repo.root)
    observed = observer.observe(list(paths))
    objects = []
    for path in paths:
        content = (repo.root / path).read_bytes()
        prepared, _ = prepare_loose_blob(repo.root, content)
        objects.append(prepared)
    plan = bind_stage_plan(GitStagePreparation(observed, paths), tuple(objects))
    candidate = DulwichGitIndexCodec().build_candidate(
        observed, paths, source_index_bytes=source_index, stage_plan=plan
    )
    payload = candidate.serialized
    if carry_tree:
        region = _extension_region(source_index)
        body = payload[:-20] + region
        payload = body + hashlib.sha1(body).digest()
    out = repo.root / ("carried.index" if carry_tree else "hive.index")
    out.write_bytes(payload)
    return candidate, out


@unittest.skipUnless(_DULWICH_AVAILABLE, _DULWICH_REASON)
@unittest.skipUnless(_GIT is not None, _GIT_REASON)
class TreeCacheSemanticProofTests(unittest.TestCase):
    def _seed_repo(self, tmp: str) -> _RealRepo:
        repo = _RealRepo(Path(tmp) / "repo")
        repo.write("root.txt", "root\n")
        repo.write("dir/a.txt", "alpha\n")
        repo.write("dir/nested/b.txt", "beta\n")
        source_index = repo.seed()
        # The whole point of this lane is that the source carries a real cache-tree.
        self.assertIn(b"TREE", source_index, "seed index must carry a TREE cache-tree extension")
        return repo

    def test_modified_tracked_file_does_not_retain_stale_tree_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._seed_repo(tmp)
            source_index = repo.index_bytes()
            repo.write("dir/a.txt", "alpha MODIFIED\n")
            repo.publish_blob("dir/a.txt")

            candidate, candidate_path = _hive_candidate(repo, ("dir/a.txt",), source_index, carry_tree=False)
            self.assertEqual(candidate.source_extensions, ("TREE",))
            self.assertNotIn(b"TREE", candidate.serialized)
            self.assertEqual(inspect_git_index_envelope(candidate.serialized).extensions, ())

            # Oracle: the tree Git itself produces for exactly this change.
            repo.stage_with_git("dir/a.txt")
            control_tree = repo.write_tree()
            candidate_tree = repo.write_tree(index=candidate_path)
            self.assertEqual(candidate_tree, control_tree)

            # Unrelated entries and full entry set must match the control too.
            self.assertEqual(
                repo.index_listing(index=candidate_path), repo.index_listing()
            )

    def test_untracked_added_file_does_not_retain_stale_tree_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._seed_repo(tmp)
            source_index = repo.index_bytes()
            repo.write("dir/added.txt", "added\n")
            repo.publish_blob("dir/added.txt")

            candidate, candidate_path = _hive_candidate(repo, ("dir/added.txt",), source_index, carry_tree=False)
            self.assertNotIn(b"TREE", candidate.serialized)

            repo.stage_with_git("dir/added.txt")
            control_tree = repo.write_tree()
            self.assertEqual(repo.write_tree(index=candidate_path), control_tree)
            self.assertEqual(repo.index_listing(index=candidate_path), repo.index_listing())

    def test_lane_detects_the_stale_tree_regression(self) -> None:
        """Negative control: the lane must fail if a stale TREE is carried forward."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._seed_repo(tmp)
            source_index = repo.index_bytes()
            repo.write("dir/a.txt", "alpha MODIFIED\n")
            repo.publish_blob("dir/a.txt")

            _candidate, carried_path = _hive_candidate(repo, ("dir/a.txt",), source_index, carry_tree=True)

            repo.stage_with_git("dir/a.txt")
            control_tree = repo.write_tree()
            carried_tree = repo.write_tree(index=carried_path)

            # Reproduces the defect: carrying the old cache-tree silently yields a
            # different, stale tree that still points at the pre-change blob.
            self.assertNotEqual(carried_tree, control_tree)
            self.assertIn(b"TREE", carried_path.read_bytes())

    def test_stale_carried_tree_keeps_the_old_blob_for_that_directory(self) -> None:
        """Characterize the defect precisely, so the guard has a stated reason."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._seed_repo(tmp)
            source_index = repo.index_bytes()
            old_blob = _git(repo.root, "rev-parse", "HEAD:dir/a.txt").strip()
            repo.write("dir/a.txt", "alpha MODIFIED\n")
            new_blob = repo.publish_blob("dir/a.txt")
            self.assertNotEqual(old_blob, new_blob)

            _candidate, carried_path = _hive_candidate(repo, ("dir/a.txt",), source_index, carry_tree=True)
            repo.stage_with_git("dir/a.txt")
            control_tree = repo.write_tree()
            carried_tree = repo.write_tree(index=carried_path)

            def subtree(tree: str) -> str:
                return _git(repo.root, "rev-parse", f"{tree}:dir").strip()

            # The carried candidate reuses the pre-change directory tree verbatim,
            # which is why the staged change disappears from the resulting tree.
            self.assertEqual(subtree(carried_tree), _git(repo.root, "rev-parse", "HEAD:dir").strip())
            self.assertNotEqual(subtree(carried_tree), subtree(control_tree))


if __name__ == "__main__":
    unittest.main()
