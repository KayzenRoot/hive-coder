from __future__ import annotations

"""Revalidation-idempotence regression for the WO-0023 observation seam.

Observation must be a pure function of the repository state. If observing a file
changes the recorded state, then the very revalidation that is supposed to prove
"nothing changed" reports staleness on an untouched repository.

This lane runs on Windows, Linux and macOS deliberately. An earlier revision
captured file access time into the approved worktree state, which broke
revalidation on Linux and macOS while still passing on Windows, so the property
needs cross-platform coverage.
"""

import os
import tempfile
import unittest
from pathlib import Path

from hive_runtime.git_stage import GitStageUnavailableError
from hive_runtime.git_stage_observer import PosixGitStageObserver


def _repo(root: Path) -> None:
    git = root / ".git"
    (git / "objects" / "info").mkdir(parents=True)
    (git / "objects" / "pack").mkdir()
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii")
    (git / "refs" / "heads" / "main").write_text("2" * 40 + "\n", encoding="ascii")
    (git / "index").write_bytes(b"synthetic-index")


class GitStageRevalidationTests(unittest.TestCase):
    def _fixture(self, root: Path) -> PosixGitStageObserver:
        _repo(root)
        (root / "a.txt").write_bytes(b"worktree-v1")
        return PosixGitStageObserver(root)

    def test_observe_then_revalidate_immediately_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observer = self._fixture(root)
            approved = observer.observe(["a.txt"])
            observer.revalidate(approved)

    def test_repeated_observation_produces_equal_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observer = self._fixture(root)
            self.assertEqual(observer.observe(["a.txt"]), observer.observe(["a.txt"]))

    def test_revalidation_survives_repeated_reads_of_the_same_file(self) -> None:
        """Reading a file for its digest must not make the approved state stale."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observer = self._fixture(root)
            approved = observer.observe(["a.txt"])
            for _ in range(3):
                (root / "a.txt").read_bytes()
                observer.revalidate(approved)

    def test_observed_worktree_stat_carries_no_access_time(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            observer = self._fixture(root)
            stat = observer.observe(["a.txt"]).worktree_states[0].stat
            self.assertIsNotNone(stat)
            assert stat is not None
            self.assertNotIn("atime", stat.canonical())
            self.assertFalse(hasattr(stat, "atime_s"))

    def test_revalidation_still_rejects_real_staleness(self) -> None:
        """Positive control: the idempotence fix must not blunt stale detection."""
        for mutation in ("head", "index", "worktree", "content-same-size"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                observer = self._fixture(root)
                approved = observer.observe(["a.txt"])
                observer.revalidate(approved)
                git = root / ".git"
                if mutation == "head":
                    (git / "refs" / "heads" / "main").write_text("3" * 40 + "\n", encoding="ascii")
                elif mutation == "index":
                    (git / "index").write_bytes(b"synthetic-index-changed")
                elif mutation == "worktree":
                    (root / "a.txt").write_bytes(b"worktree-v2")
                else:
                    # Same length, different bytes: only the content digest can catch this.
                    (root / "a.txt").write_bytes(b"worktree-vX")
                with self.assertRaises(GitStageUnavailableError):
                    observer.revalidate(approved)

    def test_stat_is_captured_for_every_observed_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _repo(root)
            (root / "one.txt").write_bytes(b"one")
            (root / "two.txt").write_bytes(b"two")
            observer = PosixGitStageObserver(root)
            state = observer.observe(["one.txt", "two.txt"])
            for entry in state.worktree_states:
                with self.subTest(path=entry.path):
                    self.assertIsNotNone(entry.stat)
                    assert entry.stat is not None
                    self.assertEqual(entry.stat.size, entry.content_bytes)


if __name__ == "__main__":
    unittest.main()
