from __future__ import annotations

"""Adversarial tests for the release-provenance contract (HCODER-WO-0026 / DEC-030).

The negative proofs are the point of this lane. A release-provenance document that
is byte-tampered, wrongly attributed, mis-channeled, duplicate, extra, missing,
path-escaping, package-set-mismatched, impossibly-transitioned or that claims
signing, notarization, provenance or publication without an independent
verification result must fail closed. Each refusal below is written so that removing
the guard it tests makes the test fail: a guard that never fires is not a guard.
"""

import contextlib
import copy
import io
import json
import plistlib
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.desktop import release_provenance
from tools.desktop.package_inventory import build_inventory, serialize_inventory
from tools.desktop.release_provenance import (
    ATTESTATION_KEYS,
    DOCUMENT_KEYS,
    NOTARIZATION_KEYS,
    PACKAGE_KEYS,
    PUBLICATION_KEYS,
    SIGNING_KEYS,
    ProvenanceError,
    asset_set_digest,
    build_baseline,
    canonical_bytes,
    inventory_binding_digest,
    main,
    serialize_provenance,
    split_prerelease,
    validate_document,
    validate_transition,
    verify_against_inventory,
    version_matches_channel,
    publication_gate,
    assess_protection,
)

SOURCE_SHA = "a" * 40
STABLE_VERSION = "0.1.0"
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


def _field_names(payload: object) -> set[str]:
    """Every field name reachable in a document, at any depth."""
    if isinstance(payload, dict):
        return {key for name in payload for key in (name, *_field_names(payload[name]))}
    if isinstance(payload, list):
        return {name for item in payload for name in _field_names(item)}
    return set()


def _make_app(root: Path, version: str) -> Path:
    bundle = root / "Hive Coder.app"
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


def _inventory(platform: str, types: list[str], version: str = STABLE_VERSION, sha: str = SOURCE_SHA) -> dict:
    """Build a real CP-0025 inventory, so binding tests judge genuine upstream evidence."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "bundle"
        root.mkdir()
        if "app" in types:
            _make_app(root, version)
        for package_type in types:
            if package_type == "app":
                continue
            name = {
                "msi": f"Hive Coder_{version}_x64_en-US.msi",
                "nsis": f"Hive Coder_{version}_x64-setup.exe",
                "deb": f"hive-coder_{version}_amd64.deb",
                "appimage": f"Hive Coder_{version}_amd64.AppImage",
                "dmg": f"Hive Coder_{version}_aarch64.dmg",
            }[package_type]
            body = {"msi": MSI_MAGIC, "nsis": PE_MAGIC, "deb": AR_MAGIC, "appimage": ELF_MAGIC}.get(package_type, b"udif")
            payload = body + b"payload"
            if package_type == "dmg":
                payload = b"udif" + DMG_MAGIC + b"\x00" * 508
            _write(root / package_type / name, payload)
        return build_inventory(
            package_root=root,
            platform=platform,
            architecture="x86_64" if platform != "macos" else "arm64",
            source_sha=sha,
            canonical_version=version,
            expected_types=types,
            expected_identifier=IDENTIFIER if platform == "macos" else "",
        )


def _baseline(platform: str = "windows", types: list[str] | None = None, version: str = STABLE_VERSION) -> tuple[dict, dict]:
    types = types or {"windows": ["msi", "nsis"], "linux": ["deb", "appimage"], "macos": ["app", "dmg"]}[platform]
    inventory = _inventory(platform, types, version)
    return inventory, build_baseline(inventory_document=inventory, release_channel="stable")


def _identity() -> dict:
    return {
        "certificateFingerprint": "b" * 40,
        "certificateSubject": "CN=Hive Coder,O=Hive,C=BR",
        "timestampAuthority": "http://timestamp.acs.microsoft.com",
    }


_ATTEST_ID = {
    "signerWorkflow": "KayzenRoot/hive-coder@refs/tags/v0.1.0",
    "sourceRef": "refs/tags/v0.1.0",
    "runId": 12345,
    "bundleDigest": "d" * 64,
}


def _signed(inventory: dict, document: dict, *, status: str = "verified") -> dict:
    """Advance every package's signing state and account for the byte change it causes."""
    document = copy.deepcopy(document)
    upstream = {entry["packageType"]: entry for entry in inventory["packages"]}
    for entry in document["packages"]:
        if status in ("signed", "verified"):
            # Signing writes a signature into the artifact, so the released bytes differ.
            entry["releasedDigest"] = "c" * 64
            entry["byteSize"] = upstream[entry["packageType"]]["byteSize"] + 4096
            entry["signing"]["identity"] = _identity()
        if status == "verified":
            entry["signing"]["verification"] = "passed"
        entry["signing"]["status"] = status
        if status in ("unavailable", "unsigned-candidate"):
            entry["signing"]["identity"] = None
            entry["signing"]["verification"] = "none"
            entry["releasedDigest"] = entry["unsignedDigest"]
            entry["byteSize"] = upstream[entry["packageType"]]["byteSize"]
        if document["platform"] == "macos" and status == "verified":
            entry["notarization"] = {"status": "verified", "verification": "passed", "reason": ""}
        elif document["platform"] == "macos" and status == "signed":
            entry["notarization"] = {"status": "stapled", "verification": "none", "reason": ""}
    return document


def _attested(document: dict, *, status: str = "verified") -> dict:
    document = copy.deepcopy(document)
    attestation = document["attestation"]
    if status == "unavailable":
        attestation.update(
            {"status": "unavailable", "verification": "none", "signerWorkflow": "", "sourceRef": "", "runId": 0, "bundleDigest": ""}
        )
        return document
    attestation.update({"status": status, "verification": "passed" if status == "verified" else "none", **_ATTEST_ID})
    return document


def _published(inventory: dict, document: dict, *, status: str = "published") -> dict:
    document = copy.deepcopy(document)
    document["publication"] = {
        "status": status,
        "releaseId": 987654 if status != "not-published" else 0,
        "releaseTag": "v0.1.0" if status != "not-published" else "",
        "assetSetDigest": asset_set_digest(document["packages"]) if status == "published" else "",
    }
    return document


def _full_release(platform: str = "windows") -> tuple[dict, dict]:
    """A document that should genuinely clear the publication gate: the positive control."""
    inventory, document = _baseline(platform)
    document = _signed(inventory, document, status="verified")
    document = _attested(document, status="verified")
    return inventory, _published(inventory, document, status="staged")


class BaselineDocumentTests(unittest.TestCase):
    def test_baseline_is_closed_and_deterministic(self) -> None:
        inventory, document = _baseline("windows")
        self.assertEqual(tuple(document.keys()), DOCUMENT_KEYS)
        self.assertEqual(document["schemaVersion"], "hive-release-provenance-v1")
        self.assertEqual(tuple(document["packages"][0].keys()), PACKAGE_KEYS)
        self.assertEqual(tuple(document["packages"][0]["signing"].keys()), SIGNING_KEYS)
        self.assertEqual(tuple(document["packages"][0]["notarization"].keys()), NOTARIZATION_KEYS)
        self.assertEqual(tuple(document["attestation"].keys()), ATTESTATION_KEYS)
        self.assertEqual(tuple(document["publication"].keys()), PUBLICATION_KEYS)
        self.assertEqual(
            serialize_provenance(document),
            serialize_provenance(build_baseline(inventory_document=inventory, release_channel="stable")),
        )

    def test_baseline_records_only_the_honest_unsigned_state(self) -> None:
        for platform, reason in (("windows", "platform-windows"), ("linux", "platform-linux"), ("macos", "unsigned-artifact")):
            with self.subTest(platform=platform):
                inventory, document = _baseline(platform)
                verify_against_inventory(document, inventory)
                for entry in document["packages"]:
                    self.assertEqual(entry["signing"]["status"], "unsigned-candidate")
                    self.assertIsNone(entry["signing"]["identity"])
                    self.assertEqual(entry["releasedDigest"], entry["unsignedDigest"])
                    self.assertEqual(entry["notarization"]["reason"], reason)
                self.assertEqual(document["attestation"]["status"], "unavailable")
                self.assertEqual(document["publication"]["status"], "not-published")

    def test_build_mode_cannot_emit_any_claim(self) -> None:
        """The emit path is an admission tool, not a claim-minting tool."""
        import inspect

        signature = inspect.signature(build_baseline)
        self.assertEqual({"inventory_document", "release_channel"}, set(signature.parameters))
        source = inspect.getsource(build_baseline)
        emitted = set(re.findall(r'"status": "([a-z-]+)"', source))
        self.assertEqual({"unsigned-candidate", "not-applicable", "unavailable", "not-published"}, emitted)

    def test_inventory_binding_digest_is_over_canonical_inventory_bytes(self) -> None:
        inventory, document = _baseline("linux")
        self.assertEqual(
            document["inventory"]["digest"],
            inventory_binding_digest(inventory),
        )
        self.assertEqual(inventory_binding_digest(inventory), __import__("hashlib").sha256(serialize_inventory(inventory).encode("utf-8")).hexdigest())


class ChannelCoherenceTests(unittest.TestCase):
    def test_channel_shape_matches_the_typescript_contract(self) -> None:
        cases = {
            ("0.1.0", "stable"): True,
            ("1.0.0", "stable"): True,
            ("1.0.0-beta.1", "beta"): True,
            ("1.0.0-beta.1+build.9", "beta"): True,
            ("1.0.0-dev.2", "dev"): True,
            ("1.0.0", "beta"): False,
            ("1.0.0-beta.1", "stable"): False,
            ("1.0.0-beta.1", "dev"): False,
            ("1.0.0-BETA.1", "beta"): False,
            ("1.0.0-Beta.1", "beta"): False,
            ("1.0.0-betaonly", "beta"): False,
            ("1.0.0+build.1", "stable"): True,
        }
        for (version, channel), expected in cases.items():
            with self.subTest(version=version, channel=channel):
                self.assertIs(version_matches_channel(version, channel), expected)

    def test_split_prerelease_strips_build_metadata_first(self) -> None:
        self.assertEqual(split_prerelease("1.0.0-alpha+001"), "alpha")
        self.assertEqual(split_prerelease("1.0.0+001"), None)
        self.assertEqual(split_prerelease("1.0.0"), None)
        self.assertEqual(split_prerelease("1.0.0-beta.1"), "beta.1")

    def test_wrong_channel_for_the_version_is_rejected(self) -> None:
        inventory = _inventory("windows", ["msi", "nsis"], version=STABLE_VERSION)
        with self.assertRaises(ProvenanceError) as ctx:
            build_baseline(inventory_document=inventory, release_channel="dev")
        self.assertIn("does not belong to releaseChannel", str(ctx.exception))

    def test_stable_shaped_version_on_beta_channel_is_rejected(self) -> None:
        _, document = _baseline("windows")
        with self.assertRaises(ProvenanceError):
            validate_document({**document, "releaseChannel": "beta"})


class SchemaClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory, self.document = _baseline("windows")

    def _assert_refused(self, document: dict, fragment: str) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn(fragment, str(ctx.exception))

    def test_unknown_top_level_key_is_rejected(self) -> None:
        tampered = dict(self.document)
        tampered["signature"] = "MFIA"
        self._assert_refused(tampered, "not the exact closed schema")

    def test_reordered_keys_are_rejected(self) -> None:
        items = list(self.document.items())
        reordered = dict([items[1], items[0]] + items[2:])
        self.assertNotEqual(tuple(reordered.keys()), tuple(self.document.keys()))
        self._assert_refused(reordered, "not the exact closed schema")

    def test_missing_key_is_rejected(self) -> None:
        tampered = {key: value for key, value in self.document.items() if key != "publication"}
        self._assert_refused(tampered, "not the exact closed schema")

    def test_wrong_schema_version_is_rejected(self) -> None:
        self._assert_refused({**self.document, "schemaVersion": "hive-release-provenance-v2"}, "schemaVersion")

    def test_unknown_channel_value_is_rejected(self) -> None:
        self._assert_refused({**self.document, "releaseChannel": "nightly"}, "releaseChannel")

    def test_unknown_signing_state_is_rejected(self) -> None:
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["signing"]["status"] = "trusted"
        self._assert_refused({**self.document, "packages": packages}, "signing.status")

    def test_non_object_document_is_rejected(self) -> None:
        self._assert_refused(["not", "an", "object"], "is not a JSON object")

    def test_boolean_cannot_satisfy_an_integer_field(self) -> None:
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["byteSize"] = True
        self._assert_refused({**self.document, "packages": packages}, "byteSize")

    def test_unordered_packages_are_rejected_for_determinism(self) -> None:
        packages = list(reversed(self.document["packages"]))
        self._assert_refused({**self.document, "packages": packages}, "ordered by (packageType, relativePath)")


class BoundAndShapeTests(unittest.TestCase):
    """Every field bound and shape rule must actually refuse, not merely exist."""

    def setUp(self) -> None:
        self.inventory, self.document = _baseline("windows")

    def _refused(self, document: dict, fragment: str) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn(fragment, str(ctx.exception))

    def test_field_types_are_not_coerced(self) -> None:
        for key, value in (("sourceSha", 1234), ("canonicalVersion", ["0.1.0"]), ("architecture", None)):
            with self.subTest(key=key):
                self._refused({**self.document, key: value}, "must be a string")
        self._refused(
            {**self.document, "inventory": {"digest": 5, "packageCount": 2}},
            "must be a string",
        )

    def test_oversized_field_values_are_refused(self) -> None:
        self._refused({**self.document, "canonicalVersion": "1" * 129}, "at most 128 characters")
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["relativePath"] = "msi/" + "a" * 512
        self._refused({**self.document, "packages": packages}, "relativePath exceeds 512 characters")
        signed = _signed(self.inventory, self.document, status="signed")
        signed["packages"][0]["signing"]["identity"]["certificateSubject"] = "C" * 257
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(signed)
        self.assertIn("certificateSubject must be a string of at most 256 characters", str(ctx.exception))

    def test_malformed_identifier_shapes_are_refused(self) -> None:
        for key, value in (("sourceSha", "abc"), ("architecture", "x86 64")):
            with self.subTest(key=key):
                self._refused({**self.document, key: value}, "does not match the closed shape")
        self._refused(
            {**self.document, "inventory": {"digest": "z" * 64, "packageCount": 2}},
            "does not match the closed shape",
        )
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["unsignedDigest"] = "0.1.0"
        self._refused({**self.document, "packages": packages}, "does not match the closed shape")

    def test_package_list_shape_is_closed(self) -> None:
        self._refused({**self.document, "packages": []}, "must be a non-empty list")
        self._refused({**self.document, "packages": "msi"}, "must be a non-empty list")
        nine = list(self.document["packages"]) * 5
        self._refused({**self.document, "packages": nine[:9], "inventory": {"digest": self.document["inventory"]["digest"], "packageCount": 9}}, "exceeds the closed ceiling of 8 entries")

    def test_relative_path_shape_is_closed(self) -> None:
        for value, fragment in (("", "non-empty string"), ("msi\\hive.msi", "POSIX separators")):
            packages = copy.deepcopy(self.document["packages"])
            packages[0]["relativePath"] = value
            with self.subTest(value=value):
                self._refused({**self.document, "packages": packages}, fragment)

    def test_a_version_that_is_not_strict_semver_is_refused(self) -> None:
        self._refused({**self.document, "canonicalVersion": "1.0"}, "is not a valid")

    def test_booleans_are_not_integers(self) -> None:
        self._refused({**self.document, "inventory": {"digest": self.document["inventory"]["digest"], "packageCount": True}}, "packageCount must be an integer")
        self._refused({**self.document, "attestation": {"status": "unavailable", "verification": "none", "signerWorkflow": "", "sourceRef": "", "runId": True, "bundleDigest": ""}}, "runId must be an integer")

    def test_upstream_inventory_must_be_an_object(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(self.document, ["not", "an", "object"])
        self.assertIn("upstream inventory is not a JSON object", str(ctx.exception))
        with self.assertRaises(ProvenanceError) as ctx:
            build_baseline(inventory_document="not-an-inventory", release_channel="stable")
        self.assertIn("upstream inventory is not a JSON object", str(ctx.exception))

    def test_a_non_inventory_document_cannot_be_bound(self) -> None:
        broken = copy.deepcopy(self.inventory)
        broken["packages"][0].pop("digest")
        with self.assertRaises(ProvenanceError) as ctx:
            build_baseline(inventory_document=broken, release_channel="stable")
        self.assertIn("not a valid hive-package-inventory-v1 document", str(ctx.exception))


class PathAndSetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory, self.document = _baseline("windows")

    def _first_path(self, document: dict) -> str:
        return document["packages"][0]["relativePath"]

    def test_traversal_path_is_rejected(self) -> None:
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["relativePath"] = "../outside/msi.pkg"
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document({**self.document, "packages": packages})
        self.assertIn("path traversal", str(ctx.exception))

    def test_absolute_posix_path_is_rejected(self) -> None:
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["relativePath"] = "/etc/passwd"
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document({**self.document, "packages": packages})
        self.assertIn("absolute path", str(ctx.exception))

    def test_foreign_drive_letter_path_is_rejected_on_any_platform(self) -> None:
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["relativePath"] = "C:\\packages\\hive.msi"
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document({**self.document, "packages": packages})
        self.assertIn("absolute path", str(ctx.exception))

    def test_unc_path_is_rejected(self) -> None:
        packages = copy.deepcopy(self.document["packages"])
        packages[0]["relativePath"] = "\\\\share\\hive.msi"
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document({**self.document, "packages": packages})
        self.assertIn("absolute path", str(ctx.exception))

    def test_duplicate_package_type_is_rejected(self) -> None:
        packages = list(self.document["packages"])
        packages.append(dict(packages[0]))
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document({**self.document, "packages": packages, "inventory": {"digest": self.document["inventory"]["digest"], "packageCount": 3}})
        self.assertIn("duplicate package entry", str(ctx.exception))

    def test_extra_package_not_in_the_inventory_is_rejected(self) -> None:
        """The upstream set comparison must be able to fire, so it is proved under a wider type table.

        ``hive-package-inventory-v1`` produces exactly two package types per platform today, and
        ``packageCount`` plus the binding digest already refuse a missing or duplicated entry, so a
        substitutable third type is the only route to this guard. Reaching it by extension rather
        than by deleting the check keeps the guard non-vacuous for the day the matrix grows.
        """
        with patch.dict(release_provenance.KNOWN_PACKAGE_TYPES, {"msix": "windows"}):
            tampered = copy.deepcopy(self.document)
            tampered["packages"][1]["packageType"] = "msix"
            with self.assertRaises(ProvenanceError) as ctx:
                verify_against_inventory(tampered, self.inventory)
        self.assertIn("package set does not match", str(ctx.exception))

    def test_missing_package_entry_is_rejected(self) -> None:
        tampered = {**self.document, "packages": [self.document["packages"][0]]}
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(tampered, self.inventory)
        self.assertIn("does not match the bound inventory packageCount", str(ctx.exception))

    def test_wrong_package_type_for_the_platform_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.document)
        tampered["packages"][0]["packageType"] = "dmg"
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(tampered)
        self.assertIn("not produced on platform", str(ctx.exception))


class BindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory, self.document = _baseline("linux")

    def test_tampered_upstream_inventory_digest_is_detected(self) -> None:
        tampered = copy.deepcopy(self.inventory)
        tampered["packages"][0]["digest"] = "f" * 64
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(self.document, tampered)
        self.assertIn("does not match the canonical bytes", str(ctx.exception))

    def test_wrong_source_sha_is_detected(self) -> None:
        """A document that keeps the binding but names another commit is refused by the comparison."""
        tampered = copy.deepcopy(self.document)
        tampered["sourceSha"] = "b" * 40
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(tampered, self.inventory)
        self.assertIn("sourceSha mismatch", str(ctx.exception))

    def test_a_document_built_from_other_evidence_fails_the_digest_first(self) -> None:
        """Rebinding to a different inventory is caught before any field comparison, by the digest."""
        other = _inventory("linux", ["deb", "appimage"], sha="b" * 40)
        foreign = build_baseline(inventory_document=other, release_channel="stable")
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(foreign, self.inventory)
        self.assertIn("does not match the canonical bytes", str(ctx.exception))

    def test_wrong_version_is_detected(self) -> None:
        tampered = copy.deepcopy(self.document)
        tampered["canonicalVersion"] = "0.9.9"
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(tampered, self.inventory)
        self.assertIn("canonicalVersion mismatch", str(ctx.exception))

    def test_unsigned_released_digest_mismatch_is_tampering_not_an_unsigned_release(self) -> None:
        tampered = copy.deepcopy(self.document)
        tampered["packages"][0]["releasedDigest"] = "e" * 64
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(tampered, self.inventory)
        self.assertIn("bytes changed without a signing account", str(ctx.exception))

    def test_unsigned_byte_size_mismatch_is_detected(self) -> None:
        tampered = copy.deepcopy(self.document)
        tampered["packages"][0]["byteSize"] += 1
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(tampered, self.inventory)
        self.assertIn("byteSize does not match", str(ctx.exception))

    def test_unsigned_digest_must_equal_the_inventory_digest(self) -> None:
        tampered = copy.deepcopy(self.document)
        tampered["packages"][0]["unsignedDigest"] = "9" * 64
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(tampered, self.inventory)
        self.assertIn("unsignedDigest does not match", str(ctx.exception))

    def test_a_renamed_artifact_is_detected_against_the_upstream_inventory(self) -> None:
        tampered = copy.deepcopy(self.document)
        tampered["packages"][0]["relativePath"] = "deb/renamed.deb"
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(tampered, self.inventory)
        self.assertIn("relativePath does not match the upstream inventory", str(ctx.exception))

    def test_signed_bytes_may_change_but_must_still_descend_from_the_inventory(self) -> None:
        """Proved on Windows: a Linux entry cannot hold a signing account at all, by design."""
        windows_inventory, windows = _baseline("windows")
        document = _signed(windows_inventory, windows, status="signed")
        verify_against_inventory(document, windows_inventory)
        self.assertNotEqual(document["packages"][0]["releasedDigest"], document["packages"][0]["unsignedDigest"])
        self.assertNotEqual(document["packages"][0]["byteSize"], windows_inventory["packages"][0]["byteSize"])

    def test_signed_bytes_from_a_foreign_inventory_are_still_refused(self) -> None:
        windows_inventory, windows = _baseline("windows")
        document = _signed(windows_inventory, windows, status="signed")
        other_inventory = _inventory("windows", ["msi", "nsis"], sha="c" * 40)
        with self.assertRaises(ProvenanceError) as ctx:
            verify_against_inventory(document, other_inventory)
        self.assertIn("does not match the canonical bytes", str(ctx.exception))


class StateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory, self.document = _baseline("macos")

    def _mutate(self, signing=None, notarization=None, attestation=None, publication=None) -> dict:
        document = copy.deepcopy(self.document)
        if signing is not None:
            document["packages"][0]["signing"].update(signing)
        if notarization is not None:
            document["packages"][0]["notarization"].update(notarization)
        if attestation is not None:
            document["attestation"].update(attestation)
        if publication is not None:
            document["publication"].update(publication)
        return document

    def test_signing_success_without_verification_evidence_is_rejected(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(signing={"status": "verified", "identity": _identity()}))
        self.assertIn("requires an independent passed verification result", str(ctx.exception))

    def test_signed_state_without_identity_is_rejected(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(signing={"status": "signed"}))
        self.assertIn("requires a public identity object", str(ctx.exception))

    def test_unsigned_state_cannot_carry_identity(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(signing={"identity": _identity()}))
        self.assertIn("unrepresentable before any signing occurs", str(ctx.exception))

    def test_unsigned_state_cannot_carry_a_verification_result(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(signing={"verification": "failed"}))
        self.assertIn("unsigned state must not carry a verification result", str(ctx.exception))

    def test_a_failed_signing_verification_must_stay_at_signed(self) -> None:
        """A failure cannot be dressed up as a verified state by editing the status."""
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(
                self._mutate(signing={"status": "verified", "verification": "failed", "identity": _identity()})
            )
        self.assertIn("failed verification cannot coexist", str(ctx.exception))

    def test_a_passed_result_must_be_recorded_as_verified(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(signing={"status": "signed", "identity": _identity(), "verification": "passed"}))
        self.assertIn("must be recorded as verified", str(ctx.exception))

    def test_private_key_material_is_unrepresentable(self) -> None:
        document = self._mutate(signing={"status": "signed", "identity": {**_identity(), "privateKey": "secret"}})
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("not the exact closed schema", str(ctx.exception))

    def test_notarization_cannot_be_stapled_onto_an_unsigned_artifact(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(notarization={"status": "stapled", "reason": ""}))
        self.assertIn("cannot staple a ticket to an unsigned artifact", str(ctx.exception))

    def test_notarization_verified_requires_verification(self) -> None:
        document = self._mutate(
            signing={"status": "verified", "verification": "passed", "identity": _identity()},
            notarization={"status": "verified", "verification": "none", "reason": ""},
        )
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("notarization success requires", str(ctx.exception))

    def test_notarization_failure_must_be_recorded_as_a_failure(self) -> None:
        document = self._mutate(
            signing={"status": "verified", "verification": "passed", "identity": _identity()},
            notarization={"status": "failed", "verification": "passed", "reason": ""},
        )
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("must be recorded with a failed verification", str(ctx.exception))

    def test_notarization_on_windows_is_rejected(self) -> None:
        inventory, windows = _baseline("windows")
        document = copy.deepcopy(windows)
        document["packages"][0]["notarization"] = {"status": "verified", "verification": "passed", "reason": ""}
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("has no notarization state to hold", str(ctx.exception))

    def test_not_applicable_reason_is_a_closed_enum(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(notarization={"reason": "we-ran-out-of-time"}))
        self.assertIn("not-applicable reason", str(ctx.exception))

    def test_not_applicable_notarization_cannot_carry_a_verification_result(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(notarization={"verification": "failed"}))
        self.assertIn("not-applicable notarization must not carry a verification result", str(ctx.exception))

    def test_an_active_notarization_state_cannot_carry_a_reason(self) -> None:
        document = self._mutate(
            signing={"status": "verified", "verification": "passed", "identity": _identity()},
            notarization={"status": "stapled", "verification": "none"},
        )
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("must not carry a not-applicable reason", str(ctx.exception))

    def test_a_passed_notarization_result_must_be_recorded_as_verified(self) -> None:
        document = self._mutate(
            signing={"status": "verified", "verification": "passed", "identity": _identity()},
            notarization={"status": "stapled", "verification": "passed", "reason": ""},
        )
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("a passed verification result must be recorded as verified", str(ctx.exception))

    def test_attestation_identity_shapes_are_closed(self) -> None:
        cases = {
            "signerWorkflow": ("hive-coder@refs/tags/v0.1.0", "signerWorkflow does not match"),
            "sourceRef": ("tags/v0.1.0", "sourceRef does not match"),
            "bundleDigest": ("not-a-digest", "bundleDigest must be a 64-character"),
        }
        for key, (value, fragment) in cases.items():
            with self.subTest(key=key):
                with self.assertRaises(ProvenanceError) as ctx:
                    validate_document(
                        self._mutate(attestation={"status": "generated", "verification": "none", **{**_ATTEST_ID, key: value}})
                    )
                self.assertIn(fragment, str(ctx.exception))

    def test_unavailable_attestation_cannot_carry_a_verification_result(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(attestation={"verification": "failed"}))
        self.assertIn("unavailable attestation must not carry a verification result", str(ctx.exception))

    def test_attestation_verified_without_verification_is_rejected(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(attestation={"status": "verified"}))
        self.assertIn("attestation success requires", str(ctx.exception))

    def test_attestation_generated_requires_full_identity(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(attestation={"status": "generated"}))
        self.assertIn("requires signerWorkflow", str(ctx.exception))

    def test_attestation_passed_result_must_be_recorded_as_verified(self) -> None:
        """An achieved verification is a state, not an attribute of a lower one."""
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(
                self._mutate(attestation={"status": "generated", "verification": "passed", **_ATTEST_ID})
            )
        self.assertIn("must be recorded as verified, not generated", str(ctx.exception))

    def test_failed_attestation_verification_stays_visible_at_generated(self) -> None:
        document = self._mutate(attestation={"status": "generated", "verification": "failed", **_ATTEST_ID})
        validate_document(document)
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(attestation={"status": "verified", "verification": "failed", **_ATTEST_ID}))
        self.assertIn("failed attestation verification cannot coexist", str(ctx.exception))

    def test_unavailable_attestation_cannot_carry_identity(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(attestation={"runId": 42}))
        self.assertIn("must not carry identity fields", str(ctx.exception))

    def test_publication_without_exact_identity_is_rejected(self) -> None:
        document = self._mutate(publication={"status": "published", "releaseId": 1, "releaseTag": "v0.1.0"})
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("artifact-set identity digest", str(ctx.exception))

    def test_publication_claim_over_the_wrong_artifact_set_is_rejected(self) -> None:
        document = self._mutate(publication={"status": "published", "releaseId": 1, "releaseTag": "v0.1.0", "assetSetDigest": "1" * 64})
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("does not match the released artifact set", str(ctx.exception))

    def test_not_published_state_cannot_carry_release_identity(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(self._mutate(publication={"releaseTag": "v0.1.0"}))
        self.assertIn("must not carry release identity", str(ctx.exception))

    def test_staged_publication_requires_exact_identity(self) -> None:
        for release_id, tag, fragment in (
            (0, "v0.1.0", "requires an exact release id and tag"),
            (7, "", "requires an exact release id and tag"),
            (7, "v 0.1.0", "releaseTag does not match the closed shape"),
        ):
            with self.subTest(release_id=release_id, tag=tag):
                document = self._mutate(
                    publication={"status": "staged", "releaseId": release_id, "releaseTag": tag, "assetSetDigest": ""}
                )
                with self.assertRaises(ProvenanceError) as ctx:
                    validate_document(document)
                self.assertIn(fragment, str(ctx.exception))

    def test_staged_publication_may_not_pin_an_artifact_set_it_has_not_released(self) -> None:
        """A staged release names an id and a tag; only a published one fixes an artifact set."""
        document = self._mutate(
            publication={"status": "staged", "releaseId": 7, "releaseTag": "v0.1.0", "assetSetDigest": "1" * 64}
        )
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("staged state must not yet assert an artifact-set identity digest", str(ctx.exception))

    def test_linux_cannot_claim_publisher_authenticity(self) -> None:
        inventory, linux = _baseline("linux")
        document = _signed(inventory, linux, status="verified")
        with self.assertRaises(ProvenanceError) as ctx:
            validate_document(document)
        self.assertIn("claims publisher authenticity on linux", str(ctx.exception))


class GateTests(unittest.TestCase):
    def test_positive_control_a_fully_verified_windows_release_is_admitted(self) -> None:
        """Without this, every DENY assertion below could pass because the gate denies anything."""
        inventory, document = _full_release("windows")
        self.assertEqual(publication_gate(document, inventory), [])

    def test_provenance_attestation_is_never_publisher_signing(self) -> None:
        """Verified build provenance must not clear a publisher-signing requirement."""
        inventory, document = _baseline("windows")
        document = _attested(document, status="verified")
        reasons = publication_gate(document, inventory)
        self.assertNotIn("build-provenance-attestation-unverified", reasons)
        self.assertEqual(["publisher-signing-unverified:msi", "publisher-signing-unverified:nsis"], reasons)

    def test_unsigned_baseline_is_denied_with_every_missing_claim_named(self) -> None:
        inventory, document = _baseline("windows")
        reasons = publication_gate(document, inventory)
        self.assertEqual(
            [
                "build-provenance-attestation-unverified",
                "publisher-signing-unverified:msi",
                "publisher-signing-unverified:nsis",
            ],
            reasons,
        )

    def test_macos_requires_platform_trust_not_just_a_signature(self) -> None:
        inventory, document = _baseline("macos")
        document = _attested(_signed(inventory, document, status="signed"), status="verified")
        reasons = publication_gate(document, inventory)
        self.assertTrue(any(reason.startswith("publisher-signing-unverified") for reason in reasons), reasons)
        self.assertTrue(any(reason.startswith("platform-trust-unverified") for reason in reasons), reasons)

    def test_linux_admits_on_provenance_and_integrity_without_a_fake_signature(self) -> None:
        inventory, document = _baseline("linux")
        document = _attested(document, status="verified")
        self.assertEqual(publication_gate(document, inventory), [])

    def test_already_published_release_is_immutable(self) -> None:
        inventory, document = _full_release("windows")
        document = _published(inventory, document, status="published")
        self.assertIn("already-published-immutable", publication_gate(document, inventory))

    def test_a_published_set_cannot_be_swapped_after_the_fact(self) -> None:
        """The recorded artifact-set identity is what pins released bytes."""
        inventory, document = _full_release("windows")
        tampered = _published(inventory, document, status="published")
        tampered["packages"][0]["releasedDigest"] = "3" * 64
        with self.assertRaises(ProvenanceError) as ctx:
            publication_gate(tampered, inventory)
        self.assertIn("does not match the released artifact set", str(ctx.exception))

    def test_an_unsigned_set_cannot_be_swapped_before_signing_exists(self) -> None:
        inventory, document = _baseline("windows")
        tampered = copy.deepcopy(document)
        tampered["packages"][0]["unsignedDigest"] = "3" * 64
        with self.assertRaises(ProvenanceError) as ctx:
            publication_gate(tampered, inventory)
        self.assertIn("unsignedDigest does not match", str(ctx.exception))


class TransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory, self.document = _baseline("windows")
        self.signed = _signed(self.inventory, self.document, status="signed")
        self.verified = _signed(self.inventory, self.document, status="verified")
        self.attested = _attested(self.verified, status="generated")

    def test_honest_forward_progression_is_legal(self) -> None:
        """The full ladder the pipeline is meant to walk, asserted legal step by step."""
        fully_attested = _attested(self.verified, status="verified")
        staged = _published(self.inventory, fully_attested, status="staged")
        validate_transition(self.document, self.signed)
        validate_transition(self.signed, self.verified)
        validate_transition(self.verified, self.attested)
        validate_transition(self.attested, fully_attested)
        validate_transition(fully_attested, staged)

    def test_regression_is_refused(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.verified, self.signed)
        self.assertIn("regression", str(ctx.exception))

    def test_skipping_a_state_is_refused(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.document, self.verified)
        self.assertIn("skips", str(ctx.exception))
        self.assertIn("'signed'", str(ctx.exception))

    def test_immutable_identity_fields_cannot_be_rewritten(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.document, {**copy.deepcopy(self.signed), "sourceSha": "b" * 40})
        self.assertIn("sourceSha is immutable", str(ctx.exception))

    def test_rebinding_to_other_packaging_evidence_is_a_new_release(self) -> None:
        other_inventory = _inventory("windows", ["msi", "nsis"], sha="c" * 40)
        other_document = build_baseline(inventory_document=other_inventory, release_channel="stable")
        tampered = {**copy.deepcopy(self.signed), "inventory": other_document["inventory"]}
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.document, tampered)
        self.assertIn("inventory.digest is immutable", str(ctx.exception))

    def test_unsigned_digest_account_stays_honest(self) -> None:
        tampered = copy.deepcopy(self.signed)
        tampered["packages"][0]["unsignedDigest"] = "4" * 64
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.document, tampered)
        self.assertIn("unsignedDigest is immutable", str(ctx.exception))

    def test_renamed_released_artifact_is_immutable(self) -> None:
        tampered = copy.deepcopy(self.signed)
        tampered["packages"][0]["relativePath"] = "msi/renamed.msi"
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.document, tampered)
        self.assertIn("relativePath is immutable", str(ctx.exception))

    def test_a_failed_signing_verification_cannot_be_walked_past(self) -> None:
        failed = copy.deepcopy(self.signed)
        failed["packages"][0]["signing"]["verification"] = "failed"
        validate_document(failed)
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(failed, self.verified)
        self.assertIn("cannot escape a failed signing verification", str(ctx.exception))

    def test_a_failed_signing_verification_cannot_be_forgotten(self) -> None:
        """Rewinding the result to ``none`` while the status stands still is not a repair."""
        failed = copy.deepcopy(self.signed)
        failed["packages"][0]["signing"]["verification"] = "failed"
        forgetful = copy.deepcopy(failed)
        for entry in forgetful["packages"]:
            entry["signing"]["verification"] = "none"
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(failed, forgetful)
        self.assertIn("cannot escape a failed signing verification", str(ctx.exception))

    def test_transition_to_an_identical_document_is_a_no_op(self) -> None:
        """Standing still is legal: an unchanged record rewinds nothing and escapes nothing."""
        validate_transition(self.verified, copy.deepcopy(self.verified))

    def test_released_package_set_is_immutable(self) -> None:
        tampered = copy.deepcopy(self.signed)
        tampered["packages"] = tampered["packages"][:1]
        # The count is adjusted so the rewrite cannot be caught by the cheaper internal check:
        # this proves the set comparison itself, which is what refuses a dropped artifact.
        tampered["inventory"]["packageCount"] = 1
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.document, tampered)
        self.assertIn("released package set is immutable", str(ctx.exception))

    def test_released_bytes_cannot_be_swapped_under_a_held_signing_state(self) -> None:
        tampered = copy.deepcopy(self.verified)
        tampered["packages"][0]["releasedDigest"] = "5" * 64
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.verified, tampered)
        self.assertIn("releasedDigest is immutable once a signing account exists", str(ctx.exception))

    def test_a_swapped_certificate_is_not_the_same_release(self) -> None:
        tampered = copy.deepcopy(self.verified)
        tampered["packages"][0]["signing"]["identity"]["certificateFingerprint"] = "9" * 40
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.verified, tampered)
        self.assertIn("signing identity is immutable once asserted", str(ctx.exception))

    def test_repointing_the_attested_build_is_refused(self) -> None:
        tampered = copy.deepcopy(self.attested)
        tampered["attestation"]["runId"] = 999
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(self.attested, tampered)
        self.assertIn("attestation runId is immutable", str(ctx.exception))

    def test_failed_notarization_is_terminal(self) -> None:
        """Terminal means no forward edge: a redo is a new release, never a repair of this record."""
        mac_inventory, mac_document = _baseline("macos")
        failed = _signed(mac_inventory, mac_document, status="verified")
        failed["packages"][0]["notarization"] = {"status": "failed", "verification": "failed", "reason": ""}
        validate_document(failed)
        escape = copy.deepcopy(failed)
        escape["packages"][0]["notarization"] = {"status": "verified", "verification": "passed", "reason": ""}
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(failed, escape)
        self.assertIn("cannot escape a failed notarization", str(ctx.exception))

    def test_verified_notarization_cannot_fall_to_failed(self) -> None:
        mac_inventory, mac_document = _baseline("macos")
        verified = _signed(mac_inventory, mac_document, status="verified")
        regress = copy.deepcopy(verified)
        regress["packages"][0]["notarization"] = {"status": "failed", "verification": "failed", "reason": ""}
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(verified, regress)
        self.assertIn("cannot move from verified to failed", str(ctx.exception))

    def test_a_published_document_is_terminal(self) -> None:
        published = _published(self.inventory, _attested(self.verified, status="verified"), status="published")
        again = copy.deepcopy(published)
        with self.assertRaises(ProvenanceError) as ctx:
            validate_transition(published, again)
        self.assertIn("published release is immutable and cannot be transitioned", str(ctx.exception))


class LadderPrimitiveTests(unittest.TestCase):
    """``_advance`` is shared by four ladders, so its own precondition must refuse, not crash."""

    def test_a_state_outside_the_ladder_is_a_refusal_not_a_value_error(self) -> None:
        from tools.desktop.release_provenance import _advance

        with self.assertRaises(ProvenanceError) as ctx:
            _advance("failed", "verified", release_provenance.NOTARIZATION_LADDER, label="notarization")
        self.assertIn("leaves the closed ladder", str(ctx.exception))

    def test_a_terminal_state_stands_still_rather_than_leaving_the_ladder(self) -> None:
        """``failed`` is outside the advance ladder, so holding it must not read as an unknown state."""
        from tools.desktop.release_provenance import _advance

        _advance("failed", "failed", release_provenance.NOTARIZATION_LADDER, label="notarization")


class CliTests(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    def test_verify_and_gate_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory, document = _baseline("windows")
            inv_path = Path(tmp) / "inv.json"
            doc_path = Path(tmp) / "prov.json"
            inv_path.write_text(serialize_inventory(inventory), encoding="utf-8")
            doc_path.write_text(serialize_provenance(document), encoding="utf-8")
            code, out = self._run(["--verify", "--provenance", str(doc_path), "--inventory", str(inv_path)])
            self.assertEqual(0, code)
            self.assertIn("RELEASE_PROVENANCE=VALID", out)
            code, out = self._run(["--gate", "--provenance", str(doc_path), "--inventory", str(inv_path)])
            self.assertEqual(2, code)
            self.assertIn("RELEASE_GATE=DENY", out)
            self.assertIn("REASON=", out)

    def test_refusal_never_prints_a_value_that_could_be_a_secret(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory, document = _baseline("windows")
            tampered = copy.deepcopy(document)
            tampered["packages"][0]["signing"]["status"] = "verified"
            tampered["packages"][0]["signing"]["identity"] = {"privateKey": "hunter2", **_identity()}
            doc_path = Path(tmp) / "prov.json"
            inv_path = Path(tmp) / "inv.json"
            doc_path.write_bytes(canonical_bytes(tampered))
            inv_path.write_text(serialize_inventory(inventory), encoding="utf-8")
            code, out = self._run(["--verify", "--provenance", str(doc_path), "--inventory", str(inv_path)])
            self.assertEqual(2, code)
            self.assertIn("REASON=", out)
            for forbidden in ("hunter2", "privateKey", "timestamp.acs.microsoft.com", "CN=Hive Coder"):
                self.assertNotIn(forbidden, out)

    def test_oversized_and_malformed_input_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            junk = Path(tmp) / "junk.json"
            junk.write_text("{not json", encoding="utf-8")
            inv_path = Path(tmp) / "inv.json"
            inv_path.write_text("{}", encoding="utf-8")
            code, out = self._run(["--verify", "--provenance", str(junk), "--inventory", str(inv_path)])
            self.assertEqual(2, code)
            self.assertIn("not valid JSON", out)

    def test_channel_gate_uses_the_canonical_version_source(self) -> None:
        code, out = self._run(["--channel-gate", "--release-channel", "stable"])
        self.assertEqual(0, code, out)
        self.assertIn("RELEASE_CHANNEL=COHERENT", out)
        code, out = self._run(["--channel-gate", "--release-channel", "dev"])
        self.assertEqual(2, code)
        self.assertIn("RELEASE_CHANNEL=INCOHERENT", out)

    def test_a_drifting_or_versionless_source_is_never_admitted_to_a_channel(self) -> None:
        """`--channel-gate` reads the live source, so a broken source cannot pass.

        The two arms are separate because they are different failures: a source that
        disagrees with itself, and a source that is coherent but names no version.
        """
        cases = {
            "DRIFT": "canonical version drift is DRIFT",
            "INVALID": "canonical version drift is INVALID",
        }
        for status, reason in cases.items():
            with self.subTest(status=status):
                report = SimpleNamespace(status=status, canonicalVersion=STABLE_VERSION)
                with patch("tools.desktop.version_drift.inspect", return_value=report):
                    code, out = self._run(["--channel-gate", "--release-channel", "stable"])
                self.assertEqual(2, code)
                self.assertIn("RELEASE_CHANNEL=INCOHERENT", out)
                self.assertIn(reason, out)

    def test_a_locked_source_that_names_no_version_is_incoherent_too(self) -> None:
        report = SimpleNamespace(status="LOCKED", canonicalVersion=None)
        with patch("tools.desktop.version_drift.inspect", return_value=report):
            code, out = self._run(["--channel-gate", "--release-channel", "stable"])
        self.assertEqual(2, code)
        self.assertIn("REASON=the version source reports no canonical version to bind", out)

    def test_build_emits_the_baseline_to_stdout_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory, document = _baseline("windows")
            inv_path = Path(tmp) / "inv.json"
            out_path = Path(tmp) / "prov.json"
            inv_path.write_text(serialize_inventory(inventory), encoding="utf-8")
            code, out = self._run(
                ["--build", "--inventory", str(inv_path), "--release-channel", "stable", "--json-out", str(out_path)]
            )
            self.assertEqual(0, code, out)
            self.assertEqual(serialize_provenance(document), out)
            self.assertEqual(out, out_path.read_text(encoding="utf-8"))

    def test_transition_mode_judges_two_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            inventory, document = _baseline("windows")
            before_path = Path(tmp) / "before.json"
            after_path = Path(tmp) / "after.json"
            before_path.write_text(serialize_provenance(document), encoding="utf-8")
            after_path.write_text(serialize_provenance(_signed(inventory, document, status="signed")), encoding="utf-8")
            code, out = self._run(["--transition", "--before", str(before_path), "--after", str(after_path)])
            self.assertEqual(0, code, out)
            self.assertIn("RELEASE_TRANSITION=LEGAL", out)
            code, out = self._run(["--transition", "--before", str(after_path), "--after", str(before_path)])
            self.assertEqual(2, code)
            self.assertIn("RELEASE_PROVENANCE=INVALID", out)
            self.assertIn("regression", out)

    def test_incomplete_invocations_fail_closed(self) -> None:
        cases = {
            "--build": ["--build"],
            "--channel-gate": ["--channel-gate"],
            "--transition": ["--transition"],
            "--verify": ["--verify"],
            "--gate": ["--gate"],
        }
        for mode, argv in cases.items():
            with self.subTest(mode=mode):
                code, out = self._run(argv)
                self.assertEqual(2, code)
                self.assertIn("REASON=", out)

    def test_oversized_input_is_rejected_before_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            huge = Path(tmp) / "huge.json"
            huge.write_bytes(b'{"sourceSha": "' + b"a" * 40 + b", " + b"x" * 400_000)
            inv_path = Path(tmp) / "inv.json"
            inv_path.write_text(serialize_inventory(_inventory("windows", ["msi", "nsis"])), encoding="utf-8")
            code, out = self._run(["--verify", "--provenance", str(huge), "--inventory", str(inv_path)])
            self.assertEqual(2, code)
            self.assertIn("exceeds the closed ceiling", out)


class EnvironmentProtectionTests(unittest.TestCase):
    """Naming an environment is not protection; only an enforced, unbypassable gate is.

    The two refusal shapes below are the real shapes observed on public repository
    environments during this Work Order: one environment with no protection rules at
    all, and one with required reviewers that admins may still bypass and whose
    reviewers may approve their own release. Both must be rejected, because a probe
    that accepted either would turn a typo into an unprotected release path.
    """

    @staticmethod
    def _reviewer(name: str = "owner-a") -> dict[str, object]:
        return {"type": "User", "reviewer": {"login": name, "id": 1}}

    def _record(self, **overrides: object) -> dict[str, object]:
        record: dict[str, object] = {
            "name": "hive-release-signing",
            "can_admins_bypass": False,
            "protection_rules": [
                {
                    "type": "required_reviewers",
                    "prevent_self_review": True,
                    "reviewers": [self._reviewer()],
                }
            ],
        }
        record.update(overrides)
        return record

    def _reasons(self, record: dict[str, object]) -> list[str]:
        return assess_protection(record)["reasons"]

    def test_a_record_that_is_not_an_object_is_the_wrong_shape_not_an_empty_gate(self) -> None:
        """A JSON array parses, is iterable and would otherwise read as "no fields"."""
        for record in ([], ["name"], "hive-release-signing", 7, None):
            with self.subTest(record=record):
                with self.assertRaises(ProvenanceError) as ctx:
                    assess_protection(record)
                self.assertIn("not a JSON object", str(ctx.exception))

    def test_an_enforced_non_bypassable_review_rule_is_a_gate(self) -> None:
        verdict = assess_protection(self._record(), expected_name="hive-release-signing")
        self.assertEqual([], verdict["reasons"])
        self.assertTrue(verdict["protected"])

    def test_environment_without_protection_rules_is_not_a_gate(self) -> None:
        reasons = self._reasons(self._record(protection_rules=[]))
        self.assertIn("protection-rules-absent", reasons)
        self.assertIn("required-reviewers-rule-absent", reasons)

    def test_admin_bypass_defeats_the_gate(self) -> None:
        reasons = self._reasons(self._record(can_admins_bypass=True))
        self.assertIn("admins-can-bypass-protection", reasons)

    def test_self_approval_defeats_the_gate(self) -> None:
        rules = [{"type": "required_reviewers", "prevent_self_review": False, "reviewers": [self._reviewer()]}]
        self.assertIn("self-review-permitted", self._reasons(self._record(protection_rules=rules)))

    def test_a_reviewer_rule_with_no_reviewers_is_not_a_gate(self) -> None:
        rules = [{"type": "required_reviewers", "prevent_self_review": True, "reviewers": []}]
        self.assertIn("required-reviewer-count-below-one", self._reasons(self._record(protection_rules=rules)))

    def test_reviewer_stubs_that_carry_no_identity_are_not_counted(self) -> None:
        rules = [
            {
                "type": "required_reviewers",
                "prevent_self_review": True,
                "reviewers": [{"type": "User"}, {"reviewer": None}, "junk"],
            }
        ]
        self.assertIn("required-reviewer-count-below-one", self._reasons(self._record(protection_rules=rules)))

    def test_an_unrecognised_rule_type_is_not_review_protection(self) -> None:
        rules = [{"type": "some_future_rule", "reviewers": [self._reviewer()]}]
        reasons = self._reasons(self._record(protection_rules=rules))
        self.assertIn("required-reviewers-rule-absent", reasons)

    def test_missing_judged_fields_fail_closed_rather_than_defaulting_secure(self) -> None:
        for key in ("name", "can_admins_bypass", "protection_rules"):
            record = self._record()
            del record[key]
            with self.assertRaises(ProvenanceError, msg=key) as ctx:
                assess_protection(record)
            self.assertIn("lacks judged fields", str(ctx.exception))

    def test_an_implicit_boolean_is_refused(self) -> None:
        for value in ("false", 0, None, "true", 1):
            with self.assertRaises(ProvenanceError, msg=repr(value)):
                assess_protection(self._record(can_admins_bypass=value))

    def test_malformed_containers_are_refused(self) -> None:
        with self.assertRaises(ProvenanceError):
            assess_protection([])
        with self.assertRaises(ProvenanceError):
            assess_protection(self._record(protection_rules="required_reviewers"))
        with self.assertRaises(ProvenanceError):
            assess_protection(self._record(protection_rules=[{"type": "required_reviewers", "prevent_self_review": True}]))
        with self.assertRaises(ProvenanceError):
            assess_protection(self._record(name="x" * 256))

    def test_foreign_fields_are_tolerated_because_the_platform_authors_them(self) -> None:
        """A provenance document is closed; a platform record gains fields over time.

        Judged fields stay exact. Unknown additions must not make the probe unable to
        read a real gate, which would break every release on an upstream API change.
        """
        record = self._record(id=42, node_id="ENv_1", html_url="https://example.invalid", created_at="2026-01-01T00:00:00Z")
        self.assertEqual([], assess_protection(record)["reasons"])

    def test_a_record_for_another_environment_is_not_evidence_for_this_one(self) -> None:
        with self.assertRaises(ProvenanceError) as ctx:
            assess_protection(self._record(name="hive-dev-deploy"), expected_name="hive-release-signing")
        self.assertIn("does not match the environment being probed", str(ctx.exception))

    def test_reasons_are_deduplicated_and_ordered(self) -> None:
        rules = [
            {"type": "required_reviewers", "prevent_self_review": False, "reviewers": []},
            {"type": "required_reviewers", "prevent_self_review": False, "reviewers": []},
        ]
        reasons = self._reasons(self._record(can_admins_bypass=True, protection_rules=rules))
        self.assertEqual(
            ["admins-can-bypass-protection", "required-reviewer-count-below-one", "self-review-permitted"],
            reasons,
        )

    def test_observed_public_environment_shapes_both_refuse(self) -> None:
        """Non-vacuity from life: 'the environment exists' must never read as protected."""
        bare = {"name": "copilot", "can_admins_bypass": True, "protection_rules": []}
        reviewed = {
            "name": "npm-publish",
            "can_admins_bypass": True,
            "protection_rules": [
                {"type": "required_reviewers", "prevent_self_review": False, "reviewers": [self._reviewer("thboop")]}
            ],
        }
        self.assertEqual(
            ["admins-can-bypass-protection", "protection-rules-absent", "required-reviewers-rule-absent"],
            assess_protection(bare)["reasons"],
        )
        self.assertEqual(
            ["admins-can-bypass-protection", "self-review-permitted"],
            assess_protection(reviewed)["reasons"],
        )


class EnvironmentProtectionCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = Path(self._dir.name)

    def _run(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(argv)
        return code, buffer.getvalue()

    def _record_path(self, payload: object) -> str:
        path = self.root / "environment.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return str(path)

    def test_a_real_gate_exits_zero_and_names_the_environment(self) -> None:
        record = EnvironmentProtectionTests()._record()
        code, out = self._run(
            ["--environment-protection", "--environment-record", self._record_path(record), "--environment-name", "hive-release-signing"]
        )
        self.assertEqual(0, code)
        self.assertIn("RELEASE_PROTECTION=PROTECTED", out)
        self.assertIn("ENVIRONMENT=hive-release-signing", out)
        self.assertNotIn("UNPROVEN_BECAUSE", out)

    def test_an_unprotected_environment_exits_non_zero_with_reasons(self) -> None:
        record = EnvironmentProtectionTests()._record(can_admins_bypass=True, protection_rules=[])
        code, out = self._run(["--environment-protection", "--environment-record", self._record_path(record)])
        self.assertEqual(2, code)
        self.assertIn("RELEASE_PROTECTION=UNPROTECTED", out)
        self.assertIn("UNPROVEN_BECAUSE=admins-can-bypass-protection", out)

    def test_an_unreadable_record_reads_as_unproven_not_as_invalid_provenance(self) -> None:
        code, out = self._run(
            ["--environment-protection", "--environment-record", str(self.root / "absent.json")]
        )
        self.assertEqual(2, code)
        self.assertIn("RELEASE_PROTECTION=UNPROVEN", out)
        self.assertNotIn("RELEASE_PROVENANCE=INVALID", out)

    def test_the_mode_requires_the_record_it_judges(self) -> None:
        code, out = self._run(["--environment-protection"])
        self.assertEqual(2, code)
        self.assertIn("--environment-protection requires --environment-record", out)


class OfflineLawTests(unittest.TestCase):
    """The validator must stay a judge, not become a release actor."""

    def test_module_imports_no_network_credential_or_execution_surface(self) -> None:
        import inspect

        import tools.desktop.release_provenance as module

        source = inspect.getsource(module)
        for forbidden in ("urllib", "http", "socket", "subprocess", "requests", "secrets", "shutil", "cosign", "codesign", "signtool"):
            self.assertNotIn(forbidden, source)

    def test_no_field_in_the_contract_can_hold_secret_material(self) -> None:
        secret_like = {"privatekey", "password", "token", "secret", "p12", "key", "pin", "credential"}
        for keys in (SIGNING_KEYS, PUBLICATION_KEYS, ATTESTATION_KEYS, NOTARIZATION_KEYS, PACKAGE_KEYS, DOCUMENT_KEYS):
            for key in keys:
                self.assertNotIn(key.lower(), secret_like, key)
        from tools.desktop.release_provenance import SIGNING_IDENTITY_KEYS

        self.assertEqual(("certificateFingerprint", "certificateSubject", "timestampAuthority"), SIGNING_IDENTITY_KEYS)

    def test_serialize_inventory_is_reused_rather_than_a_second_packaging_model(self) -> None:
        import inspect

        import tools.desktop.release_provenance as module

        self.assertIn("serialize_inventory", inspect.getsource(module))

    def test_document_carries_no_time_value(self) -> None:
        """``timestampAuthority`` names a timestamp authority; no field holds a moment."""
        inventory, document = _baseline("windows")
        signed = _signed(inventory, document, status="verified")
        names = _field_names(signed)
        self.assertIn("timestampAuthority", names)
        time_valued = {name for name in names if name.endswith("At") or name.lower() in {"timestamp", "time", "date", "datetime"}}
        self.assertEqual(set(), time_valued)
        self.assertIsNone(re.search(r"\d{4}-\d{2}-\d{2}", canonical_bytes(signed).decode("ascii")))


if __name__ == "__main__":
    unittest.main()
