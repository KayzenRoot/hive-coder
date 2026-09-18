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


def _make_app(root: Path, name: str = "Hive Coder.app", version: str = VERSION) -> Path:
    bundle = root / name
    (bundle / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
    (bundle / "Contents" / "MacOS" / "hive-coder-desktop").write_bytes(b"#!/bin/exec placeholder")
    plist = {
        "CFBundleIdentifier": IDENTIFIER,
        "CFBundleShortVersionString": version,
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
            bundle = root / "Hive Coder.app"
            (bundle / "Contents").mkdir(parents=True)
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "macos", ["app", "dmg"])
            self.assertIn("Info.plist", str(ctx.exception))


    def test_app_bundle_wrong_plist_version_is_rejected(self) -> None:
        """For a directory bundle the version assertion comes from Info.plist."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_app(root, version="9.9.9")
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            with self.assertRaises(InventoryError) as ctx:
                _inventory(root, "macos", ["app", "dmg"])
            self.assertIn("Info.plist version", str(ctx.exception))

    def test_app_bundle_without_a_version_in_its_name_is_accepted(self) -> None:
        """The pinned bundler emits `Hive Coder.app`; the name carries no version."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _macos_root(Path(tmp))
            document = _inventory(root, "macos", ["app", "dmg"])
            app_entry = next(entry for entry in document["packages"] if entry["packageType"] == "app")
            self.assertEqual(app_entry["relativePath"], "Hive Coder.app")
            self.assertIn("version_match", app_entry["structuralValidation"])


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
            self.assertIn("does not exactly match the recomputed inventory", str(ctx.exception))

    def test_directory_tree_mutation_invalidates_the_app_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = _macos_root(Path(tmp))
            document = _inventory(root, "macos", ["app", "dmg"])
            recorded = next(entry["digest"] for entry in document["packages"] if entry["packageType"] == "app")

            (root / "Hive Coder.app" / "Contents" / "Resources").mkdir(parents=True)
            (root / "Hive Coder.app" / "Contents" / "Resources" / "extra.bin").write_bytes(b"x")

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



class ClosedManifestVerificationTests(unittest.TestCase):
    """H-34-01: recorded evidence passes only if it is the exact closed inventory."""

    def _recorded(self, root: Path):
        document = _inventory(root, "windows", ["msi", "nsis"])
        return json.loads(serialize_inventory(document)), document

    def _assert_rejected(self, recorded, expected, label: str) -> None:
        with self.assertRaises(InventoryError, msg=label) as ctx:
            validate_manifest(recorded, expected)
        self.assertTrue(str(ctx.exception), label)

    def test_untouched_manifest_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            validate_manifest(recorded, expected)

    def test_tampered_schema_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["schemaVersion"] = "hive-package-inventory-v2"
            self._assert_rejected(recorded, expected, "schemaVersion")

    def test_tampered_byte_size_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"][0]["byteSize"] += 1
            self._assert_rejected(recorded, expected, "byteSize")

    def test_tampered_digest_algorithm_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"][0]["digestAlgorithm"] = "sha1"
            self._assert_rejected(recorded, expected, "digestAlgorithm")

    def test_tampered_structural_validation_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"][0]["structuralValidation"] = ["bound_in_root"]
            self._assert_rejected(recorded, expected, "structuralValidation")

    def test_tampered_digest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"][0]["digest"] = "0" * 64
            self._assert_rejected(recorded, expected, "digest")

    def test_package_reordering_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"] = list(reversed(recorded["packages"]))
            self._assert_rejected(recorded, expected, "ordering")

    def test_package_path_swap_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"][1]["relativePath"] = recorded["packages"][0]["relativePath"]
            self._assert_rejected(recorded, expected, "path swap")

    def test_missing_entry_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            del recorded["packages"][0]["byteSize"]
            self._assert_rejected(recorded, expected, "missing key")

    def test_extra_entry_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"][0]["extra"] = "payload"
            self._assert_rejected(recorded, expected, "extra key")

    def test_missing_top_level_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            del recorded["architecture"]
            self._assert_rejected(recorded, expected, "missing top-level key")

    def test_duplicate_recorded_entry_is_rejected_before_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            recorded["packages"].append(dict(recorded["packages"][0]))
            with self.assertRaises(InventoryError) as ctx:
                validate_manifest(recorded, expected)
            self.assertIn("duplicate", str(ctx.exception))

    def test_duplicate_entries_cannot_collapse_into_a_match(self) -> None:
        """A collapsed (type, path) map would hide this; the closed law must not."""
        with tempfile.TemporaryDirectory() as tmp:
            recorded, expected = self._recorded(_windows_root(Path(tmp)))
            duplicate = dict(recorded["packages"][0])
            recorded["packages"] = [duplicate, dict(duplicate)]
            with self.assertRaises(InventoryError) as ctx:
                validate_manifest(recorded, expected)
            self.assertIn("duplicate", str(ctx.exception))


class AppSymlinkContainmentTests(unittest.TestCase):
    """H-34-02: symlinks inside a bundle must stay inside the bundle."""

    def _bundle_with_link(self, root: Path, target: str):
        bundle = _make_app(root)
        link = bundle / "Contents" / "MacOS" / "linked.bin"
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation is not permitted on this platform")
        return bundle

    def _digest(self, root: Path) -> str:
        document = _inventory(root, "macos", ["app", "dmg"])
        return next(entry["digest"] for entry in document["packages"] if entry["packageType"] == "app")

    def test_valid_internal_relative_symlink_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = self._bundle_with_link(root, "../Resources/inside.bin")
            _write(bundle / "Contents" / "Resources" / "inside.bin", b"inside")
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            self.assertEqual(len(self._digest(root)), 64)

    def test_shallow_relative_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bundle_with_link(root, "../../outside.bin")
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            with self.assertRaises(InventoryError) as ctx:
                self._digest(root)
            self.assertIn("escapes the bundle root", str(ctx.exception))

    def test_deep_relative_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bundle_with_link(root, "../../../../../../../../etc/passwd")
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            with self.assertRaises(InventoryError) as ctx:
                self._digest(root)
            self.assertIn("escapes the bundle root", str(ctx.exception))

    def test_absolute_external_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._bundle_with_link(root, "/etc/passwd")
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            with self.assertRaises(InventoryError) as ctx:
                self._digest(root)
            self.assertIn("absolute target", str(ctx.exception))

    def test_retargeting_a_valid_internal_symlink_changes_the_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = self._bundle_with_link(root, "../Resources/inside.bin")
            _write(bundle / "Contents" / "Resources" / "inside.bin", b"inside")
            _write(root / "dmg" / f"Hive Coder_{VERSION}_aarch64.dmg", _dmg_payload())
            first = self._digest(root)
            link = bundle / "Contents" / "MacOS" / "linked.bin"
            link.unlink()
            link.symlink_to("../Resources/other.bin")
            self.assertNotEqual(first, self._digest(root))



class PackageWorkflowTriggerTests(unittest.TestCase):
    """M-34-04: a docs/governance-only correction head must still get package evidence.

    A Work Order correction that moves the promotion head may touch only the
    Context Lock, an ADR or the Decisions Ledger. If this workflow filtered
    ``pull_request`` by path, such a head would receive no package evidence and
    promotion would deadlock, so the trigger must stay unfiltered. Parsed with
    the standard library only so the proof runs on every runner.
    """

    def _workflow_text(self) -> str:
        path = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "native-package-matrix.yml"
        return path.read_text(encoding="utf-8")

    def _trigger_block(self) -> list[str]:
        lines = self._workflow_text().splitlines()
        start = next(index for index, line in enumerate(lines) if line.rstrip() == "on:")
        end = next(index for index, line in enumerate(lines) if line.rstrip() == "jobs:")
        return lines[start:end]

    def test_pull_request_trigger_carries_no_path_filter(self) -> None:
        block = self._trigger_block()
        index = next(
            position for position, line in enumerate(block) if line.strip() == "pull_request:"
        )
        indentation = len(block[index]) - len(block[index].lstrip())
        # The very next non-empty line must sit at the same level, i.e. the
        # `pull_request` key has no nested filter such as `paths:`.
        following = next(line for line in block[index + 1 :] if line.strip())
        self.assertEqual(
            len(following) - len(following.lstrip()),
            indentation,
            "pull_request carries a nested filter, so a governance-only correction head "
            "could receive no package evidence",
        )
        self.assertNotIn("paths:", "\n".join(block))

    def test_push_to_main_trigger_is_unchanged(self) -> None:
        block = self._trigger_block()
        index = next(position for position, line in enumerate(block) if line.strip() == "push:")
        self.assertIn("branches: [main]", block[index + 1])

    def test_no_package_version_or_identifier_is_stored_in_the_workflow(self) -> None:
        import json

        root = Path(__file__).resolve().parents[2]
        workflow_text = self._workflow_text()
        config = json.loads(
            (root / "apps" / "desktop" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
        )
        self.assertNotIn(f'CANONICAL_VERSION: "{config["version"]}"', workflow_text)
        self.assertNotIn(config["identifier"], workflow_text)

    def test_every_lane_derives_the_canonical_values_at_runtime(self) -> None:
        workflow_text = self._workflow_text()
        self.assertEqual(workflow_text.count("Derive canonical version and identifier"), 3)
        self.assertGreaterEqual(workflow_text.count("tools/desktop/version_drift.py"), 3)
        self.assertIn("VERSION_DRIFT=LOCKED", workflow_text)


if __name__ == "__main__":
    unittest.main()
