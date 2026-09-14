from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from hive_runtime.errors import RuntimePreflightError
from hive_runtime.foundation_lock import expected_foundation_version


class FoundationLockTests(unittest.TestCase):
    def test_runtime_versions_come_from_canonical_lock(self) -> None:
        self.assertEqual(expected_foundation_version("openInterpreter"), "0.0.43")
        self.assertEqual(expected_foundation_version("cuaDriver"), "0.28.1")

    def test_unknown_foundation_fails_closed(self) -> None:
        with self.assertRaises(RuntimePreflightError):
            expected_foundation_version("not-a-foundation")

    def test_wrong_schema_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lock.json"
            path.write_text(json.dumps({"schemaVersion": "wrong", "foundations": {}}), encoding="utf-8")
            with self.assertRaises(RuntimePreflightError):
                expected_foundation_version("openInterpreter", path)


if __name__ == "__main__":
    unittest.main()
