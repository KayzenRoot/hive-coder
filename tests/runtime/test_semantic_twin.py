from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from hive_runtime.repository_intelligence import RepoDNAIndexer
from hive_runtime.semantic_twin import (
    DependencyCortex, SemanticTwinBuilder, compare_semantic_twins,
)


class SemanticTwinTests(unittest.TestCase):
    def make_repo(self, root: Path, *, body: str | None = None) -> None:
        (root / "app.py").write_text(body or '''
from fastapi import FastAPI
import json
app = FastAPI()

def helper(value):
    result = value
    return result

@app.get("/health")
def health():
    payload = helper("ok")
    return payload
''', encoding="utf-8")
        (root / "user.schema.json").write_text('{"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","properties":{"id":{"type":"string"},"name":{"type":"string"}}}', encoding="utf-8")

    def test_semantic_twin_extracts_static_symbols_routes_schema_and_dataflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.make_repo(root)
            indexed = RepoDNAIndexer().scan(root, repository_id="semantic-fixture")
            twin = SemanticTwinBuilder().build(indexed)
            kinds = {node.kind for node in twin.nodes.values()}
            relations = {edge.relation for edge in twin.edges.values()}
            self.assertTrue({"file", "module", "symbol", "dependency", "route", "schema", "schema_property", "data_symbol"}.issubset(kinds))
            self.assertTrue({"imports", "calls", "exposes", "declares", "reads", "writes"}.issubset(relations))
            self.assertEqual(twin.repository_snapshot_digest, indexed.snapshot.fingerprint())
            self.assertEqual(twin.fingerprint(), SemanticTwinBuilder().build(indexed).fingerprint())

    def test_indexed_code_is_parsed_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            marker = root / "SHOULD_NOT_EXIST"
            (root / "evil.py").write_text(f'open(r"{marker}", "w").write("owned")\n', encoding="utf-8")
            indexed = RepoDNAIndexer().scan(root, repository_id="no-exec")
            SemanticTwinBuilder().build(indexed)
            self.assertFalse(marker.exists())

    def test_semantic_twin_changes_when_repository_semantics_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.make_repo(root)
            old = SemanticTwinBuilder().build(RepoDNAIndexer().scan(root, repository_id="drift"))
            self.make_repo(root, body='import os\ndef changed():\n    return os.getcwd()\n')
            new = SemanticTwinBuilder().build(RepoDNAIndexer().scan(root, repository_id="drift"))
            drift = compare_semantic_twins(old, new)
            self.assertTrue(drift.changed)
            self.assertNotEqual(old.fingerprint(), new.fingerprint())

    def test_dependency_cortex_is_bounded_and_requires_known_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.make_repo(root)
            twin = SemanticTwinBuilder().build(RepoDNAIndexer().scan(root, repository_id="cortex"))
            cortex = DependencyCortex(twin)
            root_id = next(iter(twin.nodes))
            impact = cortex.impact({root_id}, depth=4, max_nodes=12)
            self.assertIn(root_id, impact)
            self.assertLessEqual(len(impact), 12)
            with self.assertRaises(ValueError): cortex.impact({"missing"})

    def test_semantic_mappings_are_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); self.make_repo(root)
            twin = SemanticTwinBuilder().build(RepoDNAIndexer().scan(root, repository_id="immutable"))
            with self.assertRaises(TypeError):
                twin.nodes["x"] = next(iter(twin.nodes.values()))  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
