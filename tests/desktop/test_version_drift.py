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
    MAX_CORE_IDENTIFIER,
    MAX_VERSION_CHARS,
    VERSION_CONTRACT,
    MirrorObservation,
    evaluate_version_drift,
    is_valid_version,
)

ROOT = Path(__file__).resolve().parents[2]

# Shared with the product TypeScript suite: one acceptance set, two languages.
# See apps/desktop/src/contracts/version.test.ts.
PARITY_VECTORS_PATH = ROOT / "apps" / "desktop" / "src" / "contracts" / "semverParityVectors.json"
PARITY_VECTORS = json.loads(PARITY_VECTORS_PATH.read_text(encoding="utf-8"))


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

    def test_accepts_core_identifiers_up_to_the_toolchain_bound(self) -> None:
        """Core identifiers are bounded by the narrowest declared mirror consumer.

        Cargo's Rust SemVer accepts up to u64::MAX, but npm's node-semver rejects a
        core component above ``Number.MAX_SAFE_INTEGER``, so the profile follows
        npm: every accepted version must be parseable by every mirror.
        """
        for value in (
            "9007199254740990.0.0",
            "9007199254740991.0.0",
            "0.9007199254740991.0",
            "0.0.9007199254740991",
            "9007199254740991.9007199254740991.9007199254740991",
        ):
            with self.subTest(version=value):
                self.assertTrue(is_valid_version(value))

    def test_rejects_core_identifiers_past_the_toolchain_bound(self) -> None:
        for value in (
            "9007199254740992.0.0",
            "9007199254740993.0.0",
            "0.9007199254740992.0",
            "0.0.9007199254740992",
            "9007199254740992.9007199254740992.9007199254740992",
        ):
            with self.subTest(version=value):
                self.assertFalse(is_valid_version(value))

    def test_rejects_core_values_only_a_wider_consumer_would_accept(self) -> None:
        """The u64 range is wider than the profile, so it is not the bound."""
        for value in (
            "18446744073709551615.0.0",
            "18446744073709551616.0.0",
            "123456789012345678901234567890.0.0",
            "1.123456789012345678901234567890.0",
            "1.0.123456789012345678901234567890",
            "1" + "0" * 123 + ".0.0",
        ):
            with self.subTest(version=value[:32]):
                self.assertFalse(is_valid_version(value))

    def test_core_bound_is_exact_string_logic_without_integer_width_dependence(self) -> None:
        """No int/float coercion: the bound holds regardless of platform width."""
        bound = int(MAX_CORE_IDENTIFIER)
        for candidate in ("0", "1", "9007199254740990", MAX_CORE_IDENTIFIER, str(bound - 1)):
            with self.subTest(version=candidate):
                self.assertTrue(is_valid_version(f"{candidate}.0.0"))
        for candidate in (str(bound + 1), str(bound + 2), str(bound + 10**20), str(2**64)):
            with self.subTest(version=candidate):
                self.assertFalse(is_valid_version(f"{candidate}.0.0"))
        # A core identifier with a leading zero is malformed regardless of value.
        self.assertFalse(is_valid_version("09007199254740991.0.0"))

    def test_numeric_prerelease_identifiers_are_not_core_bounded(self) -> None:
        """No consuming surface imposes a lower bound on prerelease identifiers."""
        for value in (
            "1.0.0-9007199254740993",
            "1.0.0-beta.9007199254740993",
            "1.0.0-123456789012345678901234567890",
        ):
            with self.subTest(version=value):
                self.assertTrue(is_valid_version(value))

    def test_rejects_a_trailing_line_terminator(self) -> None:
        """A trailing newline must not be accepted: the product parser refuses it.

        `re.match` with a `$` anchor accepts a final LF, which would let this gate
        report LOCKED for a version the product TypeScript parser rejects.
        """
        for value in (
            "1.2.3\n",
            "1.2.3\n\n",
            "1.2.3\r",
            "1.2.3\r\n",
            "1.2.3\u2028",
            "1.2.3\u2029",
            "0.1.0\n",
            "1.2.3-beta.1\n",
        ):
            with self.subTest(version=repr(value)):
                self.assertFalse(is_valid_version(value))

    def test_rejects_unicode_decimal_digits(self) -> None:
        """Python's `\\d` matches Unicode digits; JavaScript's does not.

        The pattern therefore uses explicit ASCII `[0-9]` classes so both sides
        accept exactly the same set.
        """
        for value in ("1.0.0-1\u0660", "\u0661.0.0", "\u0661.2.3", "1.0.\u0660", "\u0661\u0662.\u0663.\u0664"):
            with self.subTest(version=repr(value)):
                self.assertFalse(is_valid_version(value))

    def test_enforces_the_declared_profile_boundaries(self) -> None:
        # Length boundary, built from legal non-core content.
        prefix = "1.0.0-alpha."
        at_boundary = prefix + "b" * (MAX_VERSION_CHARS - len(prefix))
        over_boundary = prefix + "b" * (MAX_VERSION_CHARS + 1 - len(prefix))
        self.assertEqual(len(at_boundary), MAX_VERSION_CHARS)
        self.assertEqual(len(over_boundary), MAX_VERSION_CHARS + 1)
        self.assertTrue(is_valid_version(at_boundary))
        self.assertFalse(is_valid_version(over_boundary))
        # Core bound, at and past the toolchain limit.
        self.assertTrue(is_valid_version(f"{MAX_CORE_IDENTIFIER}.0.0"))
        self.assertFalse(is_valid_version(f"{int(MAX_CORE_IDENTIFIER) + 1}.0.0"))

    def test_agrees_with_the_shared_cross_language_parity_vectors(self) -> None:
        """The single executable statement of TypeScript/Python acceptance parity.

        Both suites read this file, so the two implementations cannot drift into
        different acceptance sets without one of them failing.
        """
        self.assertEqual(PARITY_VECTORS["contract"], VERSION_CONTRACT)
        self.assertEqual(PARITY_VECTORS["profile"]["maxVersionChars"], MAX_VERSION_CHARS)
        self.assertEqual(PARITY_VECTORS["profile"]["coreMax"], MAX_CORE_IDENTIFIER)
        self.assertEqual(PARITY_VECTORS["profile"]["law"], "toolchain-compatible bounded SemVer 2.0.0")
        accepted = PARITY_VECTORS["accepted"]
        rejected = PARITY_VECTORS["rejected"]
        self.assertGreater(len(accepted), 0)
        self.assertGreater(len(rejected), 0)
        for value in accepted:
            with self.subTest(accepted=value):
                self.assertTrue(is_valid_version(value))
        for value in rejected:
            with self.subTest(rejected=repr(value)):
                self.assertFalse(is_valid_version(value))

    def test_locked_canonical_version_implies_product_parser_acceptance(self) -> None:
        """Python may never report LOCKED for a version the product parser rejects.

        Within the declared profile the acceptance sets are identical, so every
        version this gate accepts is a version TypeScript accepts. The shared
        vector file pins that equality from both sides.
        """
        accepted = PARITY_VECTORS["accepted"]
        for canonical in accepted:
            with self.subTest(canonical=canonical):
                report = evaluate_version_drift(canonical, _mirrors(canonical, canonical))
                self.assertEqual(report.status, "LOCKED")
                self.assertIn(canonical, accepted)
        for canonical in PARITY_VECTORS["rejected"]:
            with self.subTest(canonical=repr(canonical)):
                if not isinstance(canonical, str):
                    continue
                report = evaluate_version_drift(canonical, _mirrors(canonical, canonical))
                self.assertEqual(report.status, "INVALID")
                self.assertEqual(report.reason, "malformed_canonical_version")

    def test_a_trailing_newline_can_never_reach_locked(self) -> None:
        report = evaluate_version_drift("0.1.0\n", _mirrors("0.1.0\n", "0.1.0\n"))
        self.assertEqual(report.status, "INVALID")
        self.assertEqual(report.reason, "malformed_canonical_version")


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
