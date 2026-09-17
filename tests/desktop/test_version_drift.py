from __future__ import annotations

"""Contract tests for the product-version drift verifier (HCODER-WO-0024).

Negative proofs are the point of this lane: malformed SemVer and manifest drift
must fail closed, and the verifier must never mutate anything.
"""

import json
import tempfile
import unittest
from pathlib import Path

from tools.desktop.version_drift import (
    CANONICAL_SOURCE,
    MirrorObservation,
    evaluate_version_drift,
    is_valid_version,
)


def _mirrors(cargo: str | None, npm: str | None) -> tuple[MirrorObservation, ...]:
    return (
        MirrorObservation(path="apps/desktop/src-tauri/Cargo.toml", version=cargo),
        MirrorObservation(path="apps/desktop/package.json", version=npm),
    )


class SemVerLawTests(unittest.TestCase):
    def test_accepts_strict_semver_forms(self) -> None:
        for value in ("0.1.0", "1.0.0", "24.18.0", "1.2.3-beta.1", "1.2.3-dev.4", "1.2.3-rc.1+build.9"):
            with self.subTest(version=value):
                self.assertTrue(is_valid_version(value))

    def test_rejects_malformed_versions(self) -> None:
        invalid = (
            "",
            "1",
            "1.2",
            "1.2.3.4",
            "v1.2.3",
            "01.2.3",
            "1.02.3",
            "1.2.03",
            "1.2.3-",
            "1.2.3+",
            "1.2.3-01",
            "1.2.3 ",
            " 1.2.3",
            "1.2.3-beta..1",
            "1.2.3-β",
            "x" * 129,
        )
        for value in invalid:
            with self.subTest(version=value[:16]):
                self.assertFalse(is_valid_version(value))

    def test_rejects_non_string_and_none(self) -> None:
        for value in (None, 1, 1.0, ["1.2.3"], {"version": "1.2.3"}):
            with self.subTest(value=type(value).__name__):
                self.assertFalse(is_valid_version(value))  # type: ignore[arg-type]


class VersionDriftLawTests(unittest.TestCase):
    def test_matching_manifests_are_locked(self) -> None:
        report = evaluate_version_drift("0.1.0", _mirrors("0.1.0", "0.1.0"))
        self.assertEqual(report.status, "LOCKED")
        self.assertIsNone(report.reason)
        self.assertEqual(report.offendingPaths, ())
        self.assertEqual(report.canonicalSource, CANONICAL_SOURCE)
        self.assertEqual(report.sideEffects, "NONE")

    def test_missing_canonical_version_fails_closed(self) -> None:
        report = evaluate_version_drift(None, _mirrors("0.1.0", "0.1.0"))
        self.assertEqual(report.status, "INVALID")
        self.assertEqual(report.reason, "missing_canonical_version")
        self.assertEqual(report.offendingPaths, (CANONICAL_SOURCE,))

    def test_malformed_canonical_version_fails_closed(self) -> None:
        report = evaluate_version_drift("v0.1", _mirrors("0.1.0", "0.1.0"))
        self.assertEqual(report.status, "INVALID")
        self.assertEqual(report.reason, "malformed_canonical_version")

    def test_mirror_drift_is_detected_and_named(self) -> None:
        report = evaluate_version_drift("0.1.0", _mirrors("0.2.0", "0.1.0"))
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(report.reason, "mirror_drift")
        self.assertEqual(report.offendingPaths, ("apps/desktop/src-tauri/Cargo.toml",))

    def test_both_mirrors_drifting_are_both_named(self) -> None:
        report = evaluate_version_drift("0.1.0", _mirrors("1.0.0", "2.0.0"))
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(len(report.offendingPaths), 2)

    def test_missing_mirror_version_is_drift_not_silence(self) -> None:
        report = evaluate_version_drift("0.1.0", _mirrors(None, "0.1.0"))
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(report.reason, "missing_mirror_version")

    def test_malformed_mirror_version_is_distinguished_from_drift(self) -> None:
        report = evaluate_version_drift("0.1.0", _mirrors("0.1", "0.1.0"))
        self.assertEqual(report.status, "DRIFT")
        self.assertEqual(report.reason, "malformed_mirror_version")

    def test_a_newer_but_different_version_is_still_drift(self) -> None:
        """Mirrors must be equal, not merely plausible."""
        report = evaluate_version_drift("0.1.0", _mirrors("0.1.1", "0.1.0"))
        self.assertEqual(report.status, "DRIFT")

    def test_report_is_json_serializable_and_has_no_side_effects(self) -> None:
        report = evaluate_version_drift("0.1.0", _mirrors("0.1.0", "0.1.0"))
        payload = json.dumps(report.as_dict())
        self.assertIn("hive-version-drift-doctor-v1", payload)
        self.assertIn("NONE", payload)


class LiveRepositoryDriftTests(unittest.TestCase):
    def test_live_manifests_are_not_drifted(self) -> None:
        """The repository's real manifests must satisfy the canonical law."""
        from tools.desktop.version_drift import inspect

        report = inspect()
        self.assertEqual(report.status, "LOCKED", msg=f"reason={report.reason} offending={report.offendingPaths}")
        self.assertEqual(report.canonicalVersion, "0.1.0")

    def test_verifier_does_not_mutate_manifests(self) -> None:
        from tools.desktop.version_drift import CARGO_MANIFEST, PACKAGE_MANIFEST, TAURI_CONFIG, inspect

        before = {path: path.read_bytes() for path in (TAURI_CONFIG, CARGO_MANIFEST, PACKAGE_MANIFEST)}
        inspect()
        after = {path: path.read_bytes() for path in (TAURI_CONFIG, CARGO_MANIFEST, PACKAGE_MANIFEST)}
        self.assertEqual(before, after)

    def test_reader_helpers_fail_closed_on_broken_input(self) -> None:
        from tools.desktop.version_drift import _read_cargo_version, _read_json_version

        with tempfile.TemporaryDirectory() as tmp:
            broken_json = Path(tmp) / "package.json"
            broken_json.write_text("{ not json", encoding="utf-8")
            version, error = _read_json_version(broken_json)
            self.assertIsNone(version)
            self.assertEqual(error, "invalid_json")

            wrong_shape = Path(tmp) / "shape.json"
            wrong_shape.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            version, error = _read_json_version(wrong_shape)
            self.assertIsNone(version)
            self.assertEqual(error, "invalid_json")

            broken_toml = Path(tmp) / "Cargo.toml"
            broken_toml.write_text("[package\nversion=", encoding="utf-8")
            version, error = _read_cargo_version(broken_toml)
            self.assertIsNone(version)
            self.assertEqual(error, "invalid_toml")

            no_package = Path(tmp) / "Empty.toml"
            no_package.write_text("[dependencies]\n", encoding="utf-8")
            version, error = _read_cargo_version(no_package)
            self.assertIsNone(version)
            self.assertEqual(error, "invalid_toml")

    def test_module_imports_no_network_or_process_surface(self) -> None:
        import ast
        import inspect as pyinspect

        from tools.desktop import version_drift

        tree = ast.parse(pyinspect.getsource(version_drift))
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
        forbidden = ("subprocess", "socket", "ssl", "urllib", "urllib3", "requests", "http")
        for root in forbidden:
            with self.subTest(module=root):
                self.assertFalse([name for name in imported if name == root or name.startswith(root + ".")])


if __name__ == "__main__":
    unittest.main()
