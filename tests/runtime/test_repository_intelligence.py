from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from hive_runtime.expert_common import BenchmarkDimension
from hive_runtime.expert_context import CodeTruthMap, TruthFact
from hive_runtime.orchestration import DigitalTwinNode, ProjectDigitalTwin
from hive_runtime.repository_intelligence import (
    ExpertiseCapsuleExtension,
    GenomePulseMiner,
    RepoDNAIndexer,
    RepositoryFileRecord,
    RepositorySnapshot,
    TruthWeave,
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class RepoDNAIndexerTests(unittest.TestCase):
    def make_repo(self, root: Path) -> None:
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "docs").mkdir()
        (root / "src" / "api.py").write_text("import json\nfrom pathlib import Path\nVALUE = 1\n", encoding="utf-8")
        (root / "tests" / "test_api.py").write_text("from src import api\n", encoding="utf-8")
        (root / "docs" / "README.md").write_text("# Example\n", encoding="utf-8")
        (root / "package.json").write_text('{"dependencies":{"alpha":"1.0.0"}}', encoding="utf-8")
        (root / ".env").write_text("SECRET=do-not-index\n", encoding="utf-8")
        (root / ".npmrc").write_text("//registry/:_authToken=do-not-index\n", encoding="utf-8")
        (root / "image.png").write_bytes(b"\x89PNG\x00binary")

    def test_snapshot_is_deterministic_and_secret_binary_files_are_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.make_repo(root)
            indexer = RepoDNAIndexer()
            first = indexer.scan(root, repository_id="demo")
            second = indexer.scan(root, repository_id="demo")
            self.assertEqual(first.snapshot.fingerprint(), second.snapshot.fingerprint())
            paths = {item.path for item in first.snapshot.files}
            self.assertNotIn(".env", paths)
            self.assertNotIn(".npmrc", paths)
            self.assertNotIn("image.png", paths)
            self.assertIn("src/api.py", paths)
            self.assertEqual(tuple(sorted(paths)), tuple(item.path for item in first.snapshot.files))

    def test_indexer_skips_file_symlink_and_never_imports_repository_code(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as outside:
            root = Path(tmp); self.make_repo(root)
            marker = Path(outside) / "executed.txt"
            dangerous = root / "src" / "danger.py"
            dangerous.write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text('boom')\n",
                encoding="utf-8",
            )
            outside_file = Path(outside) / "outside.py"
            outside_file.write_text("VALUE=9\n", encoding="utf-8")
            link = root / "external-link.py"
            try:
                os.symlink(outside_file, link)
            except (OSError, NotImplementedError):
                link = None
            indexed = RepoDNAIndexer().scan(root, repository_id="demo")
            self.assertFalse(marker.exists())
            if link is not None:
                self.assertNotIn("external-link.py", {item.path for item in indexed.snapshot.files})

    def test_root_symlink_is_rejected_when_platform_supports_it(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as parent:
            root = Path(tmp)
            (root / "api.py").write_text("VALUE=1\n", encoding="utf-8")
            link = Path(parent) / "repo-link"
            try:
                os.symlink(root, link, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlink unavailable on this platform")
            with self.assertRaises(ValueError):
                RepoDNAIndexer().scan(link)

    def test_resource_ceilings_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "large.py").write_text("x" * 2048, encoding="utf-8")
            with self.assertRaises(RuntimeError):
                RepoDNAIndexer(max_file_bytes=1024, max_total_bytes=4096).scan(root)

    def test_snapshot_rejects_unsafe_or_noncanonical_direct_paths(self):
        for path in ("../escape.py", "src\\api.py", "C:/escape.py"):
            record = RepositoryFileRecord(path, sha("x"), 1, "python", "source")
            with self.assertRaises(ValueError, msg=path):
                RepositorySnapshot("demo", (record,)).fingerprint()

    def test_indexed_text_mapping_is_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "api.py").write_text("VALUE=1\n", encoding="utf-8")
            indexed = RepoDNAIndexer().scan(root)
            with self.assertRaises(TypeError):
                indexed.texts["api.py"] = "VALUE=2\n"


class TruthWeaveTests(unittest.TestCase):
    def indexed(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "src").mkdir()
        (root / "src" / "api.py").write_text("import json\nimport os\n", encoding="utf-8")
        (root / "package.json").write_text('{"dependencies":{"alpha":"1.0.0"}}', encoding="utf-8")
        return tmp, RepoDNAIndexer().scan(root, repository_id="demo")

    def test_truthweave_extracts_verified_file_import_and_manifest_facts(self):
        tmp, indexed = self.indexed()
        try:
            weave = TruthWeave(indexed)
            truth = weave.truth_map()
            predicates = {fact.predicate for fact in truth.query((), verified_only=True)}
            self.assertIn("file_content", predicates)
            self.assertIn("imports", predicates)
            self.assertIn("declares_dependency", predicates)
            self.assertEqual(len(weave.facts()), len(truth.query((), verified_only=True)))
        finally:
            tmp.cleanup()

    def test_tampered_fact_cannot_reuse_truthweave_provenance(self):
        tmp, indexed = self.indexed()
        try:
            weave = TruthWeave(indexed)
            original = weave.facts()[0]
            forged = replace(original, object_digest=sha("forged"))
            self.assertFalse(weave.verify(forged))
            truth = CodeTruthMap((forged,), weave.verify)
            self.assertFalse(truth.is_verified(forged.fact_id))
        finally:
            tmp.cleanup()

    def test_same_size_source_change_changes_snapshot_and_fact_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); (root / "src").mkdir()
            source = root / "src" / "api.py"
            source.write_text("VALUE=1\n", encoding="utf-8")
            first = RepoDNAIndexer().scan(root, repository_id="demo")
            first_weave = TruthWeave(first)
            source.write_text("VALUE=2\n", encoding="utf-8")
            second = RepoDNAIndexer().scan(root, repository_id="demo")
            self.assertNotEqual(first.snapshot.fingerprint(), second.snapshot.fingerprint())
            second_weave = TruthWeave(second)
            old_fact = next(f for f in first_weave.facts() if f.predicate == "file_content")
            self.assertFalse(second_weave.verify(old_fact))


class GenomePulseTests(unittest.TestCase):
    def build_pulse(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name); (root / "src").mkdir(); (root / "tests").mkdir()
        (root / "src" / "api.py").write_text("import json\n", encoding="utf-8")
        (root / "tests" / "test_api.py").write_text("from src import api\n", encoding="utf-8")
        first = RepoDNAIndexer().scan(root, repository_id="demo")
        truth = TruthWeave(first).truth_map()
        twin = ProjectDigitalTwin((
            DigitalTwinNode("api", "service"),
            DigitalTwinNode("tests", "tests", ("api",)),
        ))
        pulse = GenomePulseMiner().mine(twin, truth, {"api": "src", "tests": "tests"}, critical_nodes={"api"})
        return tmp, root, truth, twin, pulse

    def test_genomepulse_binds_verified_repository_footprint_and_detects_drift(self):
        tmp, root, truth, twin, pulse = self.build_pulse()
        try:
            self.assertEqual(pulse.covered_nodes, ("api", "tests"))
            self.assertTrue(pulse.fact_to_invariants)
            self.assertEqual(pulse.genome.detect_drift(twin, truth), tuple())
            (root / "src" / "api.py").write_text("import os\n", encoding="utf-8")
            changed_truth = TruthWeave(RepoDNAIndexer().scan(root, repository_id="demo")).truth_map()
            self.assertIn("genome.api", pulse.genome.detect_drift(twin, changed_truth))
        finally:
            tmp.cleanup()

    def test_genomepulse_fact_binding_map_is_immutable(self):
        tmp, _root, _truth, _twin, pulse = self.build_pulse()
        try:
            fact_id = next(iter(pulse.fact_to_invariants))
            with self.assertRaises(TypeError):
                pulse.fact_to_invariants[fact_id] = ("genome.fake",)
        finally:
            tmp.cleanup()

    def test_genomepulse_rejects_unsafe_path_binding(self):
        fact = TruthFact("fact.one", "src/api.py", "file_content", sha("x"), sha("p"), frozenset({"repository"}))
        truth = CodeTruthMap((fact,), lambda _fact: True)
        twin = ProjectDigitalTwin((DigitalTwinNode("api", "service"),))
        for prefix in ("../src", "src\\nested", "C:/src"):
            with self.assertRaises(ValueError, msg=prefix):
                GenomePulseMiner().mine(twin, truth, {"api": prefix})

    def test_unverified_fact_cannot_seed_genomepulse(self):
        fact = TruthFact("fact.one", "src/api.py", "file_content", sha("x"), sha("p"), frozenset({"repository"}))
        truth = CodeTruthMap((fact,), lambda _fact: False)
        twin = ProjectDigitalTwin((DigitalTwinNode("api", "service"),))
        with self.assertRaises(ValueError):
            GenomePulseMiner().mine(twin, truth, {"api": "src"})


class ExpertiseExtensionTests(unittest.TestCase):
    def test_language_framework_extension_is_descriptive_and_fingerprinted(self):
        extension = ExpertiseCapsuleExtension(
            "python.fastapi.review", "1.0.0", sha("base"),
            frozenset({"python"}), frozenset({"fastapi"}),
            ("validate async boundaries",), ("dependency injection lifetime",),
            frozenset({BenchmarkDimension.CODE_REVIEW, BenchmarkDimension.SECURITY}),
            sha("provenance"),
        )
        first = extension.fingerprint()
        changed = replace(extension, frameworks=frozenset({"django"}))
        self.assertNotEqual(first, changed.fingerprint())
        self.assertFalse(hasattr(extension, "permission"))
        self.assertFalse(hasattr(extension, "competence_level"))


if __name__ == "__main__":
    unittest.main()
