from __future__ import annotations

import hashlib
import inspect
import io
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path

from hive_runtime.git_stage import GitStagePreparation, GitStageUnavailableError, GitStageUnsupportedRepositoryError
from hive_runtime.git_stage_contract import GitStageObservedState, GitStageWorktreeState
from hive_runtime.git_stage_index_codec import (
    ADMITTED_DULWICH_WHEEL_TAG,
    DULWICH_CANDIDATE_VERSION,
    DULWICH_CODEC_ID,
    INDEX_CODEC_CONTRACT,
    DulwichGitIndexCodec,
    GitIndexCandidate,
    UnavailableGitIndexCodec,
)
from hive_runtime.git_index_envelope import inspect_git_index_envelope
from hive_runtime.git_loose_object_transaction import prepare_loose_blob
from hive_runtime.git_stage_observer import PosixGitStageObserver
from hive_runtime.git_stage_plan import bind_stage_plan

try:  # pragma: no cover - exercised by CI, which installs the governed dependency
    import dulwich  # noqa: F401

    _DULWICH_AVAILABLE = True
    _DULWICH_REASON = ""
except ImportError:  # pragma: no cover
    _DULWICH_AVAILABLE = False
    _DULWICH_REASON = (
        "governed dependency dulwich==1.2.15 is not materialized in this interpreter; CI installs it via "
        "foundations/python-dependencies.requirements.txt and gates on tools/foundations/verify_python_dependencies.py"
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


# --- fixture builders -------------------------------------------------------


def entry(path: bytes, sha_hex: str, *, mode: int = 0o100644, size: int = 0, stage: int = 0) -> bytes:
    fixed = bytearray(62)
    fixed[24:28] = struct.pack(">I", mode)
    fixed[36:40] = struct.pack(">I", size)
    fixed[40:60] = bytes.fromhex(sha_hex)
    fixed[60:62] = struct.pack(">H", len(path) | ((stage & 0x3) << 12))
    raw = bytes(fixed) + path + b"\x00"
    return raw + b"\x00" * ((8 - (len(raw) % 8)) % 8)


def extension(signature: bytes, payload: bytes = b"") -> bytes:
    return signature + struct.pack(">I", len(payload)) + payload


def index_bytes(version: int = 2, entries: tuple[bytes, ...] = (), extensions: bytes = b"") -> bytes:
    payload = b"DIRC" + struct.pack(">II", version, len(entries)) + b"".join(entries) + extensions
    return payload + hashlib.sha1(payload).digest()


def _repo(root: Path, index: bytes | None) -> None:
    git = root / ".git"
    (git / "objects" / "info").mkdir(parents=True)
    (git / "objects" / "pack").mkdir()
    (git / "refs" / "heads").mkdir(parents=True)
    (git / "config").write_text("[core]\n repositoryformatversion = 0\n", encoding="ascii")
    (git / "HEAD").write_text("ref: refs/heads/main\n", encoding="ascii")
    (git / "refs" / "heads" / "main").write_text("2" * 40 + "\n", encoding="ascii")
    if index is not None:
        (git / "index").write_bytes(index)


def _write(root: Path, relative: str, content: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _blob_oid(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\x00" + content).hexdigest()


def _prepare(root: Path, paths: tuple[str, ...], observed_state: GitStageObservedState):
    objects = []
    for path in paths:
        content = (root / path).read_bytes()
        prepared, _ = prepare_loose_blob(root, content)
        objects.append(prepared)
    return bind_stage_plan(GitStagePreparation(observed_state, paths), objects)


def _tree(payload: bytes = b"fixture-tree-cache") -> bytes:
    return extension(b"TREE", payload)


@unittest.skipUnless(_DULWICH_AVAILABLE, _DULWICH_REASON)
class GitIndexCodecBoundaryTests(unittest.TestCase):
    """Data-only behaviour of the reviewed codec. Never publishes anything."""

    def test_contract_and_reviewed_identity_are_fixed(self) -> None:
        self.assertEqual(INDEX_CODEC_CONTRACT, "hive-git-index-codec-v1")
        self.assertEqual(DULWICH_CANDIDATE_VERSION, "1.2.15")
        self.assertEqual(DULWICH_CODEC_ID, "dulwich-1.2.15-pure-python-index-codec-v1")
        self.assertEqual(ADMITTED_DULWICH_WHEEL_TAG, "py3-none-any")

    def test_modified_file_is_staged_and_unrelated_entries_and_tree_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            untouched = b"keep/me.txt"
            changed = b"a.txt"
            untouched_oid = "c" * 40
            original = b"alpha\n"
            modified = b"alpha modified\n"
            _write(root, "keep/me.txt", b"keep\n")
            _write(root, "a.txt", modified)
            index = index_bytes(
                2,
                (
                    entry(changed, _blob_oid(original), size=len(original)),
                    entry(untouched, untouched_oid, size=5),
                ),
                _tree(),
            )
            _repo(root, index)

            state = PosixGitStageObserver(root).observe(["a.txt"])
            plan = _prepare(root, ("a.txt",), state)
            candidate = DulwichGitIndexCodec().build_candidate(
                state, ("a.txt",), source_index_bytes=index, stage_plan=plan
            )

            envelope = inspect_git_index_envelope(candidate.serialized)
            self.assertEqual(envelope.version, 2)
            self.assertEqual(envelope.entry_count, 2)
            self.assertEqual(envelope.extensions, ("TREE",))
            self.assertEqual(candidate.preserved_extensions, ("TREE",))

            from dulwich.index import read_index_dict_with_version

            entries, _, _ = read_index_dict_with_version(io.BytesIO(candidate.serialized))
            self.assertEqual(sorted(entries), [changed, untouched])
            staged = entries[changed]
            self.assertEqual(
                staged.sha.decode("ascii") if isinstance(staged.sha, bytes) else staged.sha, _blob_oid(modified)
            )
            self.assertEqual(staged.size, len(modified))
            preserved = entries[untouched]
            self.assertEqual(
                preserved.sha.decode("ascii") if isinstance(preserved.sha, bytes) else preserved.sha, untouched_oid
            )
            # The TREE extension region is preserved verbatim, byte for byte.
            self.assertIn(_tree(), candidate.serialized)

    def test_version_three_index_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = b"beta\n"
            _write(root, "b.txt", content)
            index = index_bytes(3, (entry(b"b.txt", _blob_oid(b"stale\n"), size=6),))
            _repo(root, index)
            state = PosixGitStageObserver(root).observe(["b.txt"])
            plan = _prepare(root, ("b.txt",), state)
            candidate = DulwichGitIndexCodec().build_candidate(
                state, ("b.txt",), source_index_bytes=index, stage_plan=plan
            )
            self.assertEqual(candidate.index_version, 3)
            self.assertEqual(inspect_git_index_envelope(candidate.serialized).version, 3)

    def test_untracked_path_is_added_in_deterministic_sorted_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "z.txt", b"zed\n")
            _write(root, "a.txt", b"ay\n")
            index = index_bytes(2, (entry(b"m.txt", "d" * 40, size=1),))
            _repo(root, index)
            state = PosixGitStageObserver(root).observe(["z.txt", "a.txt"])
            paths = tuple(item.path for item in state.worktree_states)
            plan = _prepare(root, paths, state)
            candidate = DulwichGitIndexCodec().build_candidate(
                state, paths, source_index_bytes=index, stage_plan=plan
            )
            from dulwich.index import read_index_dict_with_version

            entries, _, _ = read_index_dict_with_version(io.BytesIO(candidate.serialized))
            names = list(entries)
            self.assertEqual(names, sorted(names))
            self.assertEqual(names, [b"a.txt", b"m.txt", b"z.txt"])
            self.assertEqual(candidate.paths, ("a.txt", "z.txt"))

    def test_candidate_is_deterministic_and_metadata_matches_its_own_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "a.txt", b"deterministic\n")
            index = index_bytes(2, (entry(b"a.txt", "e" * 40, size=4),))
            _repo(root, index)
            state = PosixGitStageObserver(root).observe(["a.txt"])
            plan = _prepare(root, ("a.txt",), state)
            codec = DulwichGitIndexCodec()
            first = codec.build_candidate(state, ("a.txt",), source_index_bytes=index, stage_plan=plan)
            second = codec.build_candidate(state, ("a.txt",), source_index_bytes=index, stage_plan=plan)
            self.assertEqual(first.serialized, second.serialized)
            self.assertEqual(first.candidate_sha256, hashlib.sha256(first.serialized).hexdigest())
            self.assertEqual(first.candidate_bytes, len(first.serialized))
            self.assertEqual(first.source_index_sha256, state.index_sha256)

    def test_absent_index_produces_a_fresh_version_two_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "new.txt", b"brand new\n")
            _repo(root, None)
            state = PosixGitStageObserver(root).observe(["new.txt"])
            self.assertEqual(state.index_state, "absent")
            plan = _prepare(root, ("new.txt",), state)
            candidate = DulwichGitIndexCodec().build_candidate(state, ("new.txt",), stage_plan=plan)
            envelope = inspect_git_index_envelope(candidate.serialized)
            self.assertEqual(envelope.version, 2)
            self.assertEqual(envelope.entry_count, 1)
            self.assertEqual(candidate.preserved_extensions, ())

    def test_candidate_is_data_only_with_no_publication_surface(self) -> None:
        candidate = GitIndexCandidate("proof-codec", SHA_A, ("src/app.py",), b"DIRC-candidate")
        self.assertEqual(candidate.source_index_sha256, SHA_A)
        self.assertEqual(candidate.paths, ("src/app.py",))
        self.assertEqual(candidate.serialized, b"DIRC-candidate")
        self.assertEqual(candidate.candidate_bytes, len(b"DIRC-candidate"))
        self.assertEqual(candidate.candidate_sha256, hashlib.sha256(b"DIRC-candidate").hexdigest())
        for forbidden in ("publish", "permit_token", "write", "commit", "stage_paths"):
            self.assertFalse(hasattr(candidate, forbidden))

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


@unittest.skipUnless(_DULWICH_AVAILABLE, _DULWICH_REASON)
class GitIndexCodecFailClosedTests(unittest.TestCase):
    """Unsupported envelopes and stale state must fail closed, never be guessed."""

    def _codec_inputs(self, root: Path, index: bytes, paths: tuple[str, ...]):
        state = PosixGitStageObserver(root).observe(list(paths))
        plan = _prepare(root, paths, state)
        return state, plan

    def test_rejects_conflict_sparse_split_mandatory_and_unproven_extensions(self) -> None:
        cases = {
            "conflict-stage": (2, (entry(b"a.txt", "f" * 40, stage=2),), b""),
            "split-index": (2, (), extension(b"link", b"x")),
            "sparse-index": (2, (), extension(b"sdir", b"x")),
            "mandatory": (2, (), extension(b"abcd", b"x")),
            "unproven-optional": (2, (), extension(b"UNKN", b"x")),
            "unsupported-version": (4, (), b""),
        }
        for label, (version, entries, extensions) in cases.items():
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _write(root, "a.txt", b"content\n")
                index = index_bytes(version, entries, extensions)
                _repo(root, index)
                state, plan = self._codec_inputs(root, index, ("a.txt",))
                with self.assertRaises(GitStageUnsupportedRepositoryError):
                    DulwichGitIndexCodec().build_candidate(
                        state, ("a.txt",), source_index_bytes=index, stage_plan=plan
                    )

    def test_rejects_source_index_bytes_that_do_not_match_the_approved_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "a.txt", b"content\n")
            index = index_bytes(2, (entry(b"a.txt", "f" * 40, size=8),))
            _repo(root, index)
            state, plan = self._codec_inputs(root, index, ("a.txt",))
            tampered = index_bytes(2, (entry(b"a.txt", "1" * 40, size=8),))
            with self.assertRaises(GitStageUnavailableError):
                DulwichGitIndexCodec().build_candidate(
                    state, ("a.txt",), source_index_bytes=tampered, stage_plan=plan
                )

    def test_rejects_stage_plan_built_for_a_different_head_or_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "a.txt", b"content\n")
            index = index_bytes(2, (entry(b"a.txt", "f" * 40, size=8),))
            _repo(root, index)
            state, _ = self._codec_inputs(root, index, ("a.txt",))

            prepared, _ = prepare_loose_blob(root, b"content\n")
            foreign = GitStageObservedState(
                state.repository_identity,
                "3" * 40,
                state.index_state,
                state.index_identity,
                state.index_sha256,
                state.worktree_states,
            )
            foreign_plan = bind_stage_plan(GitStagePreparation(foreign, ("a.txt",)), (prepared,))

            with self.assertRaises(GitStageUnavailableError):
                DulwichGitIndexCodec().build_candidate(
                    state, ("a.txt",), source_index_bytes=index, stage_plan=foreign_plan
                )

    def test_rejects_assume_valid_and_extended_flag_entries(self) -> None:
        for label, flags in (("assume-valid", 0x8001), ("extended", 0x4001)):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _write(root, "a.txt", b"content\n")
                raw = bytearray(entry(b"a.txt", "f" * 40, size=8))
                raw[60:62] = struct.pack(">H", flags)
                index = index_bytes(2, (bytes(raw),))
                _repo(root, index)
                state, plan = self._codec_inputs(root, index, ("a.txt",))
                with self.assertRaises(GitStageUnsupportedRepositoryError):
                    DulwichGitIndexCodec().build_candidate(
                        state, ("a.txt",), source_index_bytes=index, stage_plan=plan
                    )

    def test_rejects_staged_path_without_an_exact_stat_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "a.txt", b"content\n")
            index = index_bytes(2, (entry(b"a.txt", "f" * 40, size=8),))
            _repo(root, index)
            state, plan = self._codec_inputs(root, index, ("a.txt",))
            statless = GitStageObservedState(
                state.repository_identity,
                state.repository_head,
                state.index_state,
                state.index_identity,
                state.index_sha256,
                tuple(
                    GitStageWorktreeState(item.path, item.file_identity, item.content_sha256, item.content_bytes)
                    for item in state.worktree_states
                ),
            )
            with self.assertRaises(GitStageUnsupportedRepositoryError):
                DulwichGitIndexCodec().build_candidate(
                    statless, ("a.txt",), source_index_bytes=index, stage_plan=plan
                )

    def test_rejects_candidate_paths_that_do_not_match_the_stage_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "a.txt", b"content\n")
            _write(root, "b.txt", b"other\n")
            index = index_bytes(2, ())
            _repo(root, index)
            state = PosixGitStageObserver(root).observe(["a.txt", "b.txt"])
            plan = _prepare(root, ("a.txt", "b.txt"), state)
            with self.assertRaises(GitStageUnsupportedRepositoryError):
                DulwichGitIndexCodec().build_candidate(
                    state, ("a.txt",), source_index_bytes=index, stage_plan=plan
                )

    def test_default_codec_fails_closed_without_runtime_dependency(self) -> None:
        with self.assertRaises(GitStageUnavailableError):
            UnavailableGitIndexCodec().build_candidate(observed(), ["src/app.py"])

    def test_real_codec_requires_a_stage_plan_and_matching_paths(self) -> None:
        codec = DulwichGitIndexCodec()
        with self.assertRaises(GitStageUnavailableError):
            codec.build_candidate(observed(), ["src/app.py"])
        with self.assertRaises(GitStageUnsupportedRepositoryError):
            codec.build_candidate(observed(), [])
        with self.assertRaises(GitStageUnsupportedRepositoryError):
            codec.build_candidate(observed(), ["z.py", "a.py"])


@unittest.skipUnless(_DULWICH_AVAILABLE, _DULWICH_REASON)
class GitIndexCodecAuthorityIsolationTests(unittest.TestCase):
    """The codec path must not reach porcelain, GitFile, shell, hooks, filters or network.

    The static check parses the module AST so that documentation may *describe*
    forbidden behaviour without the test being satisfied or defeated by comments.
    """

    FORBIDDEN_IMPORT_ROOTS = (
        "subprocess",
        "socket",
        "ssl",
        "urllib",
        "urllib3",
        "requests",
        "http",
        "ftplib",
        "smtplib",
        "dulwich.client",
        "dulwich.porcelain",
        "dulwich.repo",
        "dulwich.server",
    )

    FORBIDDEN_NAMES = ("GitFile", "porcelain", "Popen", "urlopen", "system", "popen")

    FORBIDDEN_MODULES = (
        "urllib3",
        "dulwich.client",
        "dulwich.porcelain",
        "dulwich.repo",
        "dulwich.server",
        "socket",
        "ssl",
        "subprocess",
    )

    def test_codec_ast_reaches_no_executable_or_network_extension_point(self) -> None:
        import ast

        from hive_runtime import git_stage_index_codec as module

        tree = ast.parse(inspect.getsource(module))
        imported: list[str] = []
        names: list[str] = []
        attributes: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported.append(node.module)
            elif isinstance(node, ast.Name):
                names.append(node.id)
            elif isinstance(node, ast.Attribute):
                attributes.append(node.attr)

        for root in self.FORBIDDEN_IMPORT_ROOTS:
            with self.subTest(import_root=root):
                self.assertFalse(
                    [name for name in imported if name == root or name.startswith(root + ".")],
                    f"codec must not import {root}",
                )
        for name in self.FORBIDDEN_NAMES:
            with self.subTest(name=name):
                self.assertNotIn(name, names)
                self.assertNotIn(name, attributes)

    def test_building_a_candidate_imports_no_forbidden_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root, "a.txt", b"isolated\n")
            index = index_bytes(2, (entry(b"a.txt", "f" * 40, size=9),))
            _repo(root, index)
            state = PosixGitStageObserver(root).observe(["a.txt"])
            plan = _prepare(root, ("a.txt",), state)
            before = set(sys.modules)
            DulwichGitIndexCodec().build_candidate(state, ("a.txt",), source_index_bytes=index, stage_plan=plan)
            introduced = set(sys.modules) - before
            for name in self.FORBIDDEN_MODULES:
                with self.subTest(module=name):
                    self.assertNotIn(name, introduced)

    def test_importing_the_observer_and_codec_needs_no_client_surface(self) -> None:
        from hive_runtime import git_stage_index_codec as module

        self.assertFalse(hasattr(module, "porcelain"))
        self.assertFalse(hasattr(module, "GitFile"))
        self.assertFalse(hasattr(module, "Repo"))


if __name__ == "__main__":
    unittest.main()
