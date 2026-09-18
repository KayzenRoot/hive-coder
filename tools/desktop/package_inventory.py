"""Deterministic package inventory and structural validator (HCODER-WO-0025).

This tool discovers generated Hive Coder package artifacts inside **one explicit
bounded root**, verifies their portable structure, and emits a deterministic
JSON inventory. It is standard-library only, offline, read-only with respect to
the package root, and deterministic: the same discovered artifact set always
yields byte-identical manifest output regardless of filesystem enumeration order.

What a digest does and does not mean
------------------------------------
``digest`` is a SHA-256 over exact bytes (or, for a directory bundle, over a
documented sorted-tree encoding). It proves **byte identity / integrity for
evidence transport** between the runner and the reviewer. It is **not** signing,
**not** a publisher-authenticity proof, and **not** a notarization or trust
statement. Packages produced by this pipeline are deliberately unsigned internal
evidence.

Directory bundles
-----------------
A macOS ``.app`` is a directory, so it never carries a plain file hash. It is
hashed with a documented **sorted-tree digest**: entries are walked
deterministically, each contributes one NUL-delimited record
``relative_path \0 entry_type \0 byte_size \0 entry_digest`` followed by a
newline, records are concatenated in sorted order, and the tree digest is the
SHA-256 of that concatenation. Symlinks contribute ``l`` with their link target
as the entry digest so a retargeted symlink changes the tree digest.

Schema (closed)
---------------
``hive-package-inventory-v1`` has exactly these keys::

    schemaVersion, sourceSha, canonicalVersion, platform, architecture, packages

and each package entry has exactly these keys::

    packageType, relativePath, byteSize, digestAlgorithm, digest, structuralValidation

``structuralValidation`` is a sorted list drawn from a closed vocabulary of the
portable checks that passed for that entry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "hive-package-inventory-v1"
DIGEST_ALGORITHM = "sha256"

DOCUMENT_KEYS = ("schemaVersion", "sourceSha", "canonicalVersion", "platform", "architecture", "packages")
ENTRY_KEYS = ("packageType", "relativePath", "byteSize", "digestAlgorithm", "digest", "structuralValidation")

#: Package types this validator understands, mapped to the platform that produces them.
KNOWN_PACKAGE_TYPES: dict[str, str] = {
    "msi": "windows",
    "nsis": "windows",
    "app": "macos",
    "dmg": "macos",
    "deb": "linux",
    "appimage": "linux",
}

#: Closed vocabulary of portable structural checks recorded per entry.
STRUCTURAL_CHECKS = (
    "bound_in_root",
    "format_magic",
    "nonzero_size",
    "path_relative",
    "version_match",
    "info_plist",
    "expected_executable",
    "tree_digest",
)

#: A version token as it appears in a generated package file name.
VERSION_TOKEN = re.compile(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?")
SOURCE_SHA = re.compile(r"^[0-9a-f]{40}$")

MSI_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"  # OLE2 / compound file
PE_MAGIC = b"MZ"
AR_MAGIC = b"!<arch>\n"  # Debian archive
ELF_MAGIC = b"\x7fELF"  # AppImage
DMG_TRAILER_SIGNATURE = b"koly"  # UDIF trailer at the end of a .dmg


class InventoryError(Exception):
    """Raised when the discovered artifact set is not a valid inventory."""


@dataclass(frozen=True)
class PackageSpec:
    """What one package type is expected to look like on disk."""

    package_type: str
    is_directory: bool
    expected_magic: bytes | None
    file_suffix: str = ""


SPECS: dict[str, PackageSpec] = {
    "msi": PackageSpec("msi", False, MSI_MAGIC, ".msi"),
    "nsis": PackageSpec("nsis", False, PE_MAGIC, ".exe"),
    "dmg": PackageSpec("dmg", False, DMG_TRAILER_SIGNATURE, ".dmg"),
    "deb": PackageSpec("deb", False, AR_MAGIC, ".deb"),
    "appimage": PackageSpec("appimage", False, ELF_MAGIC, ".appimage"),
    "app": PackageSpec("app", True, None, ".app"),
}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def validate_link_target(bundle_root: Path, link_parent: Path, target: str) -> str:
    """Prove a link target stays inside ``bundle_root``; return the target string.

    An absolute target is refused even when it happens to resolve inside the
    bundle, because an absolute link is not portable evidence. A relative target
    is normalized lexically against the symlink's own directory — never
    followed — and the resulting destination must remain inside the bundle root,
    so both a shallow ``../`` escape and a deep ``../../..`` escape are refused.
    The target string is returned unchanged, so retargeting a valid internal link
    still changes the tree digest.

    The decision is pure path arithmetic so it can be tested without creating
    real symlinks, on every platform.
    """
    if os.path.isabs(target):
        raise InventoryError(f"bundle symlink has an absolute target: {link_parent} -> {target}")
    resolved = Path(os.path.normpath(os.path.join(str(link_parent), target)))
    if not resolved.is_relative_to(bundle_root):
        raise InventoryError(f"bundle symlink escapes the bundle root: {link_parent} -> {target}")
    return target


def _symlink_target(bundle_root: Path, link_path: Path) -> str:
    """Containment-checked target of a real symlink on disk."""
    return validate_link_target(bundle_root, link_path.parent, os.readlink(link_path))


def tree_digest(root: Path) -> str:
    """Deterministic sorted-tree digest of a directory bundle.

    Records are ``relative_path \\0 entry_type \\0 byte_size \\0 entry_digest``,
    sorted by relative POSIX path, concatenated, and SHA-256 hashed. ``entry_type``
    is ``f`` for a regular file, ``d`` for a directory and ``l`` for a symlink
    (whose entry digest is its link target, after the containment proof above).
    Only regular files, directories and symlinks are permitted; any other entry
    type is refused.
    """
    bundle_root = root.resolve()
    records: list[str] = []
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        directory_names.sort()
        file_names.sort()
        current_path = Path(current)
        entries = [(name, "d") for name in directory_names] + [(name, "f") for name in file_names]
        for name, kind in entries:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                target = _symlink_target(bundle_root, path)
                records.append(f"{relative}\0l\0{len(target.encode())}\0{target}")
            elif path.is_dir():
                records.append(f"{relative}\0d\0{0}\0")
            elif path.is_file():
                records.append(f"{relative}\0f\0{path.stat().st_size}\0{_sha256_file(path)}")
            else:
                raise InventoryError(f"unsupported entry type inside bundle: {relative}")
    records.sort()
    return _sha256_bytes(("".join(record + "\n" for record in records)).encode())


def _check_types(package_type: str) -> PackageSpec:
    spec = SPECS.get(package_type)
    if spec is None:
        raise InventoryError(f"unknown package type: {package_type}")
    return spec


def _validate_relative(relative: str) -> None:
    if relative.startswith("/") or relative.startswith("\\") or re.match(r"^[A-Za-z]:", relative):
        raise InventoryError(f"absolute path is not allowed: {relative}")
    parts = Path(relative).parts
    if ".." in parts:
        raise InventoryError(f"path traversal is not allowed: {relative}")


def _discover(package_root: Path, package_type: str) -> list[Path]:
    """Collect matching artifacts for one type, bounded to ``package_root``."""
    spec = _check_types(package_type)
    matches: list[Path] = []
    for current, directory_names, file_names in os.walk(package_root, followlinks=False):
        directory_names.sort()
        file_names.sort()
        current_path = Path(current)
        for name in directory_names + file_names:
            candidate = current_path / name
            if candidate.is_symlink():
                # A symlinked artifact is only acceptable when it resolves inside the root.
                resolved = candidate.resolve()
                if not resolved.is_relative_to(package_root):
                    raise InventoryError(f"symlink escapes the bounded package root: {candidate}")
            if spec.is_directory:
                if name.endswith(spec.file_suffix) and candidate.is_dir():
                    matches.append(candidate)
            elif candidate.is_file() and candidate.suffix.lower() == spec.file_suffix:
                matches.append(candidate)
    return sorted(matches)


def _version_from_name(name: str, canonical_version: str) -> None:
    """Require the package name to carry the canonical version and no other version."""
    tokens = VERSION_TOKEN.findall(name)
    if canonical_version not in tokens:
        raise InventoryError(f"package name does not carry canonical version {canonical_version}: {name}")
    foreign = sorted({token for token in tokens if token != canonical_version})
    if foreign:
        raise InventoryError(f"package name carries a non-canonical version {foreign}: {name}")


def _app_checks(bundle: Path, canonical_version: str, expected_identifier: str) -> list[str]:
    """Portable structural checks for a macOS ``.app`` directory bundle."""
    checks = ["bound_in_root", "path_relative", "tree_digest"]
    info_plist = bundle / "Contents" / "Info.plist"
    if not info_plist.is_file():
        raise InventoryError(f"bundle is missing Contents/Info.plist: {bundle.name}")
    try:
        plist = plistlib.loads(info_plist.read_bytes())
    except Exception as exc:  # noqa: BLE001 - any plist failure is a structural refusal
        raise InventoryError(f"Info.plist is not readable: {bundle.name}: {type(exc).__name__}") from exc
    if not isinstance(plist, dict):
        raise InventoryError(f"Info.plist is not a dictionary: {bundle.name}")
    for key in ("CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleExecutable"):
        if not plist.get(key):
            raise InventoryError(f"Info.plist is missing {key}: {bundle.name}")
    if plist["CFBundleShortVersionString"] != canonical_version:
        raise InventoryError(
            f"Info.plist version {plist['CFBundleShortVersionString']!r} != canonical {canonical_version!r}"
        )
    if expected_identifier and plist["CFBundleIdentifier"] != expected_identifier:
        raise InventoryError(
            f"Info.plist identifier {plist['CFBundleIdentifier']!r} != expected {expected_identifier!r}"
        )
    checks.append("info_plist")
    executable = bundle / "Contents" / "MacOS" / str(plist["CFBundleExecutable"])
    if not executable.is_file():
        raise InventoryError(f"bundle executable is missing: {executable.name}")
    checks.append("expected_executable")
    # A macOS bundle's version lives in Info.plist (checked above), not in the
    # directory name: the pinned bundler names the bundle after the product
    # ("Hive Coder.app"), so the name carries no version to match.
    checks.append("version_match")
    return sorted(checks)


def _file_checks(path: Path, package_type: str, canonical_version: str) -> list[str]:
    """Portable structural checks for a single-file package."""
    spec = _check_types(package_type)
    checks = ["bound_in_root", "path_relative"]
    size = path.stat().st_size
    if size <= 0:
        raise InventoryError(f"file package is empty: {path.name}")
    checks.append("nonzero_size")
    if spec.expected_magic is not None:
        with path.open("rb") as handle:
            head = handle.read(len(spec.expected_magic))
        if spec.expected_magic == DMG_TRAILER_SIGNATURE:
            with path.open("rb") as handle:
                handle.seek(-512, os.SEEK_END)
                head = handle.read(4)
        if not head.startswith(spec.expected_magic):
            raise InventoryError(f"{package_type} artifact does not carry the expected format magic: {path.name}")
        checks.append("format_magic")
    _version_from_name(path.name, canonical_version)
    checks.append("version_match")
    return sorted(checks)


def build_inventory(
    *,
    package_root: Path,
    platform: str,
    architecture: str,
    source_sha: str,
    canonical_version: str,
    expected_types: list[str],
    expected_identifier: str = "",
) -> dict[str, Any]:
    """Discover, validate and describe the artifact set under ``package_root``."""
    if not SOURCE_SHA.match(source_sha):
        raise InventoryError(f"sourceSha must be a 40-character lowercase hex SHA: {source_sha!r}")
    if not expected_types:
        raise InventoryError("at least one expected package type is required")
    if len(set(expected_types)) != len(expected_types):
        raise InventoryError("expected package types contain duplicates")
    for package_type in expected_types:
        _check_types(package_type)
        if KNOWN_PACKAGE_TYPES[package_type] != platform:
            raise InventoryError(f"package type {package_type} is not produced on platform {platform}")
    if not package_root.is_dir():
        raise InventoryError(f"package root does not exist: {package_root}")

    resolved_root = package_root.resolve()
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()

    for package_type in sorted(expected_types):
        matches = _discover(resolved_root, package_type)
        if not matches:
            raise InventoryError(f"missing expected package type: {package_type}")
        if len(matches) > 1:
            names = ", ".join(sorted(match.name for match in matches))
            raise InventoryError(f"duplicate package type {package_type}: {names}")
        artifact = matches[0]
        if not artifact.resolve().is_relative_to(resolved_root):
            raise InventoryError(f"artifact resolves outside the bounded package root: {artifact}")
        relative = artifact.relative_to(resolved_root).as_posix()
        _validate_relative(relative)
        if relative in seen:
            raise InventoryError(f"duplicate artifact path: {relative}")
        seen.add(relative)

        spec = _check_types(package_type)
        if spec.is_directory:
            if not artifact.is_dir():
                raise InventoryError(f"{package_type} artifact is not a directory bundle: {relative}")
            checks = _app_checks(artifact, canonical_version, expected_identifier)
            digest = tree_digest(artifact)
            byte_size = sum(
                path.stat().st_size
                for path in artifact.rglob("*")
                if path.is_file() and not path.is_symlink()
            )
        else:
            checks = _file_checks(artifact, package_type, canonical_version)
            digest = _sha256_file(artifact)
            byte_size = artifact.stat().st_size

        entries.append(
            {
                "packageType": package_type,
                "relativePath": relative,
                "byteSize": byte_size,
                "digestAlgorithm": DIGEST_ALGORITHM,
                "digest": digest,
                "structuralValidation": checks,
            }
        )

    # Anything that looks like a package artifact but was not expected means the
    # lane produced a different set than it declared, which must fail closed.
    known_suffixes = {spec.file_suffix for spec in SPECS.values()}
    expected_suffixes = {_check_types(package_type).file_suffix for package_type in expected_types}
    present_suffixes: set[str] = set()
    for current, directory_names, file_names in os.walk(resolved_root, followlinks=False):
        present_suffixes.update(Path(name).suffix.lower() for name in directory_names if Path(name).suffix)
        present_suffixes.update(Path(name).suffix.lower() for name in file_names if Path(name).suffix)
    for suffix in sorted((present_suffixes & known_suffixes) - expected_suffixes):
        raise InventoryError(f"unexpected package type present in the package root: {suffix}")

    entries.sort(key=lambda entry: (entry["packageType"], entry["relativePath"]))
    return {
        "schemaVersion": SCHEMA_VERSION,
        "sourceSha": source_sha,
        "canonicalVersion": canonical_version,
        "platform": platform,
        "architecture": architecture,
        "packages": entries,
    }


def serialize_inventory(document: dict[str, Any]) -> str:
    """Canonical serialization: declared key order, sorted entries, trailing newline."""
    if tuple(document.keys()) != DOCUMENT_KEYS:
        raise InventoryError(f"inventory document keys are not the closed schema: {sorted(document.keys())}")
    for entry in document["packages"]:
        if tuple(entry.keys()) != ENTRY_KEYS:
            raise InventoryError(f"inventory entry keys are not the closed schema: {sorted(entry.keys())}")
    return json.dumps(document, indent=2, ensure_ascii=True, sort_keys=False) + "\n"


def _validate_closed_document(document: Any, *, label: str) -> None:
    """Require an object that is exactly the closed inventory schema.

    Presence and order of the declared keys are both enforced, entries must be
    closed entry dictionaries, and duplicate ``(packageType, relativePath)``
    pairs are refused **before** any comparison so no dictionary collapse can
    hide them.
    """
    if not isinstance(document, dict):
        raise InventoryError(f"{label} is not a JSON object")
    if tuple(document.keys()) != DOCUMENT_KEYS:
        raise InventoryError(
            f"{label} keys are not the exact closed schema (expected {list(DOCUMENT_KEYS)})"
        )
    if document["schemaVersion"] != SCHEMA_VERSION:
        raise InventoryError(f"{label} schemaVersion {document['schemaVersion']!r} != {SCHEMA_VERSION!r}")
    packages = document["packages"]
    if not isinstance(packages, list):
        raise InventoryError(f"{label} packages must be a list")
    seen: set[tuple[str, str]] = set()
    for entry in packages:
        if not isinstance(entry, dict):
            raise InventoryError(f"{label} package entry is not a JSON object")
        if tuple(entry.keys()) != ENTRY_KEYS:
            raise InventoryError(
                f"{label} package entry keys are not the exact closed schema (expected {list(ENTRY_KEYS)})"
            )
        if not isinstance(entry["structuralValidation"], list) or not all(
            isinstance(item, str) for item in entry["structuralValidation"]
        ):
            raise InventoryError(f"{label} structuralValidation must be a list of strings")
        identity = (entry["packageType"], entry["relativePath"])
        if identity in seen:
            raise InventoryError(f"{label} records duplicate package entry: {identity[0]} {identity[1]}")
        seen.add(identity)


def validate_manifest(document: Any, expected: dict[str, Any]) -> None:
    """Accept recorded evidence only if it is exactly the recomputed inventory.

    Both the recorded document and the expected inventory are validated as closed
    schemas, then compared by canonical serialization. That compares package
    count, package order, every evidence-significant entry field
    (``packageType``, ``relativePath``, ``byteSize``, ``digestAlgorithm``,
    ``digest``, ``structuralValidation``) and every document field
    (``sourceSha``, ``canonicalVersion``, ``platform``, ``architecture``) in one
    exact operation, so a tampered or lossy recording cannot pass.
    """
    _validate_closed_document(document, label="recorded manifest")
    _validate_closed_document(expected, label="recomputed inventory")
    for key in ("sourceSha", "canonicalVersion", "platform", "architecture"):
        if document[key] != expected[key]:
            raise InventoryError(f"manifest {key} mismatch: {document[key]!r} != {expected[key]!r}")
    if serialize_inventory(document) != serialize_inventory(expected):
        raise InventoryError(
            "recorded manifest does not exactly match the recomputed inventory "
            "(package count, order, byte size, digest algorithm, digest or structural validation differs)"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hive Coder deterministic package inventory (read-only)")
    parser.add_argument("--package-root", type=Path, required=True, help="bounded root holding generated packages")
    parser.add_argument("--platform", required=True, choices=sorted(set(KNOWN_PACKAGE_TYPES.values())))
    parser.add_argument("--architecture", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--canonical-version", required=True)
    parser.add_argument("--expected-types", required=True, help="comma-separated package types produced by the lane")
    parser.add_argument("--expected-identifier", default="", help="expected macOS bundle identifier, when known")
    parser.add_argument("--json-out", type=Path, default=None, help="write the manifest to this path")
    parser.add_argument("--verify", type=Path, default=None, help="recompute and compare against this manifest")
    args = parser.parse_args(argv)

    try:
        expected_types = [item.strip() for item in args.expected_types.split(",") if item.strip()]
        document = build_inventory(
            package_root=args.package_root,
            platform=args.platform,
            architecture=args.architecture,
            source_sha=args.source_sha,
            canonical_version=args.canonical_version,
            expected_types=expected_types,
            expected_identifier=args.expected_identifier,
        )
        payload = serialize_inventory(document)
        if args.verify is not None:
            recorded = json.loads(args.verify.read_text(encoding="utf-8"))
            validate_manifest(recorded, document)
            print("PACKAGE_INVENTORY_VERIFY=MATCH")
        if args.json_out is not None:
            args.json_out.write_text(payload, encoding="utf-8")
        sys.stdout.write(payload)
        return 0
    except InventoryError as exc:
        print(f"PACKAGE_INVENTORY=INVALID\nREASON={exc}")
        return 2
    except OSError as exc:
        print(f"PACKAGE_INVENTORY=INVALID\nREASON=io:{type(exc).__name__}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
