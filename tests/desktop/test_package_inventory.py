from __future__ import annotations

"""Adversarial tests for the deterministic package inventory (HCODER-WO-0025).

The negative proofs are the point of this lane: a package set that is missing,
duplicated, unexpected, empty, wrongly versioned, wrongly attributed, escaping
the bounded root or byte-mutated must fail closed. The manifest must also be
byte-stable regardless of discovery order.
"""

import json
import os
import plistlib
import tempfile
import unittest
from pathlib import Path

from tools.desktop.package_inventory import (
    DIGEST_ALGORITHM,
    DOCUMENT_KEYS,
    ENTRY_KEYS,
    SCHEMA_VERSION,
    InventoryError,
    build_inventory,
    serialize_inventory,
    validate_manifest,
)

SOURCE_SHA = "a" * 40
VERSION = "0.1.0"
IDENTIFIER = "dev.hive.coder"

MSI_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
PE_MAGIC = b"MZ"
AR_MAGIC = b"!<arch>\n"
ELF_MAGIC = b"\x7fELF"
DMG_MAGIC = b"koly"


def _write(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _dmg_payload(body: bytes = b"udif") -> bytes:
    """A UDIF-shaped file: payload followed by a 512-byte trailer beginning 'koly'."""
    return body + DMG_MAGIC + b"\x00" * 508


def _make_app(root: Path, name: str = f"Hive Coder_{VERSION}_aarch64.app") -> Path:
    bundle = root / name
    (bundle / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
    (bundle / "Contents" / "MacOS" / "hive-coder-desktop").write_bytes(b"#!/bin/exec placeholder")
    plist = {
        "CFBundleIdentifier": IDENTIFIER,
        "CFBundleShortVersionString": VERSION,
        "CFBundleExecutable": "hive-coder-desktop",
        "CFBundleName": "Hive Coder",
    }
    (bundle / "Contents" / "Info.plist").write_bytes(plistlib.dumps(plist))
    return bundle


def _windows_root(root: Path) -> Path:
    _write(root / "msi" / f"Hive Coder_{VERSION}_x64_en-US.msi", MSI_MAGIC + b"payload")
    _write(root / "nsis" / f"Hive Coder_{VERSION}_x64-setup.exe", PE_MAGIC + b"payload")
    return root


def _linux_root(root: Path) -> Path:
    _write(root / "deb" / f"hive-coder_{VERSION}_amd64.deb", AR_MAGIC + b"payload")
    _write(root / "appimage" / f"Hive Coder_{VERSION}_amd64.AppImage", ELF_MAGIC + b"payload")
    return root


def _macos_root(root: Path) -> Path:
    _make_app(root)
    _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
    return root


def _inventory(root: Path, platform: str, types: list[str], version: str = VERSION, sha: str = SOURCE_SHA):
    return build_inventory(
        package_root=root,
        platform=platform,
        architecture="x86_64",
        source_sha=sha,
        canonical_version=version,
        expected_types=types,
        expected_identifier=IDENTIFIER if platform == "macos" else "",
    )


class ValidInventoryTests(unittest.TestCase):
    def test_windows_inventory_is_closed_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            document = _inventory(root, "windows", ["msi", "nsis"])
            self.assertEqual(tuple(document.keys()), DOCUMENT_KEYS)
            self.assertEqual(document["schemaVersion"], SCHEMA_VERSION)
            self.assertEqual([entry["packageType"] for entry in document["packages"]], ["msi", "nsis"])
            for entry in document["packages"]:
                self.assertEqual(tuple(entry.keys()), ENTRY_KEYS)
                self.assertEqual(entry["digestAlgorithm"], DIGEST_ALGORITHM)
                self.assertEqual(len(entry["digest"]), 64)
                self.assertIn("format_magic", entry["structuralValidation"])
                self.assertIn("version_match", entry["structuralValidation"])
            self.assertEqual(serialize_inventory(document), serialize_inventory(document))

    def test_macos_inventory_uses_tree_digest_for_the_app_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _macos_root(Path(tmp))
            document = _inventory(root, "macos", ["app", "dmg"])
            app_entry = next(entry for entry in document["packages"] if entry["packageType"] == "app")
            dmg_entry = next(entry for entry in document["packages"] if entry["packageType"] == "dmg")
            self.assertIn("tree_digest", app_entry["structuralValidation"])
            self.assertIn("info_plist", app_entry["structuralValidation"])
            self.assertIn("expected_executable", app_entry["structuralValidation"])
            self.assertNotIn("tree_digest", dmg_entry["structuralValidation"])
            self.assertGreater(app_entry["byteSize"], 0)

    def test_linux_inventory_covers_deb_and_appimage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _linux_root(Path(tmp))
            document = _inventory(root, "linux", ["deb", "appimage"])
            self.assertEqual([entry["packageType"] for entry in document["packages"]], ["appimage", "deb"])

    def test_digests_are_integrity_evidence_not_signing(self) -> None:
        """The inventory must never claim publisher authenticity."""
        import tools.desktop.package_inventory as module

        text = Path(module.__file__).read_text(encoding="utf-8").lower()
        for claim in ("signing", "publisher-authenticity", "not a publisher-authenticity proof"):
            self.assertIn(claim.replace("not a ", ""), text)
        self.assertIn("integrity", text)
        self.assertNotIn("signed by", text)


class RejectionTests(unittest.TestCase):
    def test_missing_expected_package_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "nsis" / f"Hive Coder_{VERSION}_x64-setup.exe", PE_MAGIC + b"payload")
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"])
            self.assertIn("missing expected package type: msi", str(ctx.exception))

    def test_duplicate_package_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            _write(root / "msi" / f"Hive Coder_{VERSION}_x64_dup.msi", MSI_MAGIC + b"second")
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"])
            self.assertIn("duplicate package type", str(ctx.exception))

    def test_unexpected_extra_package_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            _write(root / "extra" / f"Hive Coder_{VERSION}_x64.dmg", _dmg_payload())
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"])
            self.assertIn("unexpected package type", str(ctx.exception))

    def test_zero_size_file_package_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "msi" / f"Hive Coder_{VERSION}_x64_en-US.msi", b"")
            _write(root / "nsis" / f"Hive Coder_{VERSION}_x64-setup.exe", PE_MAGIC + b"payload")
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"])
            self.assertIn("empty", str(ctx.exception))

    def test_wrong_canonical_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"], version="9.9.9")
            self.assertIn("canonical version", str(ctx.exception))

    def test_foreign_version_token_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Carries the canonical version *and* a different version token.
            _write(root / "msi" / f"Hive Coder_{VERSION}_9.9.9_x64.msi", MSI_MAGIC + b"payload")
            _write(root / "nsis" / f"Hive Coder_{VERSION}_x64-setup.exe", PE_MAGIC + b"payload")
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"])
            self.assertIn("non-canonical version", str(ctx.exception))

    def test_wrong_source_sha_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"], sha="not-a-sha")
            self.assertIn("sourceSha", str(ctx.exception))

    def test_format_magic_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write(root / "msi" / f"Hive Coder_{VERSION}_x64_en-US.msi", b"NOT-AN-OLE-FILE")
            _write(root / "nsis" / f"Hive Coder_{VERSION}_x64-setup.exe", PE_MAGIC + b"payload")
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "nsis"])
            self.assertIn("format magic", str(ctx.exception))

    def test_absolute_and_traversal_relative_paths_are_rejected(self) -> None:
        from tools.desktop.package_inventory import _validate_relative

        for value in ("/etc/passwd", "\\windows\\system32", "C:/temp/x.msi", "../escape.msi", "a/../../b.msi"):
            with self.subTest(relative=value):
                with self.assertRaises(InventoryError):
                    _validate_relative(value)

    def test_symlink_escaping_the_root_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            outside = Path(tmp).parent / f"hive-outside-{os.getpid()}.msi"
            _write(outside, MSI_MAGIC + b"outside")
            link = root / "msi" / "link.msi"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation is not permitted on this platform")
            try:
                with self.assertRaises(InventoryError) as ctx:
                    _inventory(root, "windows", ["msi", "nsis"])
                self.assertIn("escapes the bounded package root", str(ctx.exception))
            finally:
                link.unlink(missing_ok=True)
                outside.unlink(missing_ok=True)

    def test_artifact_outside_bounded_root_is_never_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp)
            bounded = outer / "bundle"
            _windows_root(bounded)
            # A lookalike sitting outside the declared root must not satisfy the type.
            _write(outer / "stray-msi" / f"Hive Coder_{VERSION}_x64_en-US.msi", MSI_MAGIC + b"outside-lookalike")
            for artifact in sorted((bounded / "msi").iterdir()):
                artifact.unlink()
            with self.assertRaises(InventoryError) as ctx:
                _inventory(bounded, "windows", ["msi", "nsis"])
            self.assertIn("missing expected package type: msi", str(ctx.exception))

    def test_unknown_package_type_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "snap"])
            self.assertIn("unknown package type", str(ctx.exception))

    def test_package_type_from_another_platform_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "windows", ["msi", "deb"])
            self.assertIn("not produced on platform", str(ctx.exception))

    def test_app_bundle_without_info_plist_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / f"Hive Coder_{VERSION}_aarch64.app"
            (bundle / "Contents").mkdir(parents=True)
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "macos", ["app", "dmg"])
            self.assertIn("Info.plist", str(ctx.exception))


class MutationAndDeterminismTests(unittest.TestCase):
    def test_one_byte_mutation_invalidates_the_recorded_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            document = _inventory(root, "windows", ["msi", "nsis"])
            payload = serialize_inventory(document)

            target = root / "msi" / f"Hive Coder_{VERSION}_x64_en-US.msi"
            mutated = bytearray(target.read_bytes())
            mutated[-1] ^= 0xFF
            target.write_bytes(bytes(mutated))

            recomputed = _inventory(root, "windows", ["msi", "nsis"])
            self.assertNotEqual(serialize_inventory(recomputed), payload)
            with self.assertRaises(InventoryError) as ctx:
                validate_manifest(json.loads(payload), recomputed)
            self.assertIn("digests do not match", str(ctx.exception))

    def test_directory_tree_mutation_invalidates_the_app_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _macos_root(Path(tmp))
            document = _inventory(root, "macos", ["app", "dmg"])
            recorded = next(entry["digest"] for entry in document["packages"] if entry["packageType"] == "app")

            (root / f"Hive Coder_{VERSION}_aarch64.app" / "Contents" / "Resources").mkdir(parents=True)
            (root / f"Hive Coder_{VERSION}_aarch64.app" / "Contents" / "Resources" / "extra.bin").write_bytes(b"x")

            mutated = _inventory(root, "macos", ["app", "dmg"])
            changed = next(entry["digest"] for entry in mutated["packages"] if entry["packageType"] == "app")
            self.assertNotEqual(recorded, changed)

    def test_discovery_order_does_not_change_manifest_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _linux_root(Path(tmp))
            first = serialize_inventory(_inventory(root, "linux", ["deb", "appimage"]))
            second = serialize_inventory(_inventory(root, "linux", ["appimage", "deb"]))
            self.assertEqual(first, second)

            # Recreate the same artifact set in the opposite creation order.
            other = Path(tmp) / "second"
            _write(other / "appimage" / f"Hive Coder_{VERSION}_amd64.AppImage", ELF_MAGIC + b"payload")
            _write(other / "deb" / f"hive-coder_{VERSION}_amd64.deb", AR_MAGIC + b"payload")
            third = serialize_inventory(_inventory(other, "linux", ["deb", "appimage"]))
            self.assertEqual(first.replace(str(root), "ROOT"), third.replace(str(other), "ROOT"))

    def test_manifest_verification_accepts_an_unchanged_artifact_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            document = _inventory(root, "windows", ["msi", "nsis"])
            validate_manifest(json.loads(serialize_inventory(document)), document)

    def test_manifest_environment_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _windows_root(Path(tmp))
            document = _inventory(root, "windows", ["msi", "nsis"])
            recorded = json.loads(serialize_inventory(document))
            recorded["sourceSha"] = "b" * 40
            with self.assertRaises(InventoryError) as ctx:
                validate_manifest(recorded, document)
            self.assertIn("mismatch", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
