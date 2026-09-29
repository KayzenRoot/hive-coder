"""HCODER-SEC-0001: reproducible, fail-closed build-time glib 0.18.5 backport.

Produces an UNTRACKED local Cargo [patch.crates-io] directory. Never performs a
runtime update, installs software, accepts caller URLs or weakens cargo audit.
The two upstream fix lines are the only changed original crate-source bytes.
The signed Debian source/patch provenance was verified by exact CI run
36591726532; this bootstrap independently pins the actual downloaded bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile
from urllib.parse import urlparse
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "apps/desktop/src-tauri/vendor/glib-0.18.5"
CRATE_URL = "https://static.crates.io/crates/glib/glib-0.18.5.crate"
DEBIAN_URL = (
    "https://deb.debian.org/debian/pool/main/r/rust-glib-0.18/"
    "rust-glib-0.18_0.18.5-7.debian.tar.xz"
)
CRATE_SHA256 = "233daaf6e83ae6a12a52055f568f9d7cf4671dabb78ff9560ab6da230ce00ee5"
DEBIAN_SHA256 = "9895cf4df3525224ee825477dc76c730566591528b9af9fc05c310706b61db5b"
PATCH_SHA256 = "9a3b06ad9a7d5d459d44ee5ab05557720992b8d214bfea14c5e9b4ae4f5702eb"
PATCH_NAME = "0007-glib-fix-UB-in-VariantStrIter-impl_get.patch"
PATCH_PATH = "debian/patches/" + PATCH_NAME
PATCH_TARGET = "src/variant_iter.rs"
RECEIPT_NAME = "HCODER-GLIB-PROVENANCE.json"
OLD_DECL = b"let p: *mut libc::c_char = std::ptr::null_mut();"
NEW_DECL = b"let mut p: *mut libc::c_char = std::ptr::null_mut();"
OLD_ARG = b"&p,"
NEW_ARG = b"&mut p,"
MAX_CRATE = 8_000_000
MAX_DEBIAN = 500_000
MAX_UNCOMPRESSED = 15_000_000
MAX_MEMBERS = 800


class ProvenanceError(RuntimeError):
    """Source or generated overlay failed a fail-closed identity check."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_bytes(data: bytes, expected: str, label: str, limit: int) -> bytes:
    if not data or len(data) > limit or digest(data) != expected:
        raise ProvenanceError(f"{label}: size or pinned SHA-256 mismatch")
    return data


def fetch(url: str, limit: int) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"static.crates.io", "deb.debian.org"}:
        raise ProvenanceError("unapproved source host or transport")
    with urlopen(url, timeout=45) as response:
        redirected = urlparse(response.geturl())
        if redirected.scheme != "https" or redirected.hostname not in {
            "static.crates.io", "deb.debian.org", "cdn-fastly.crates.io",
        }:
            raise ProvenanceError("source redirected to unapproved host")
        payload = response.read(limit + 1)
    if not payload or len(payload) > limit:
        raise ProvenanceError("source download missing or over bound")
    return payload


def safe_members(tf: tarfile.TarFile, *, prefix: str, max_total: int) -> list[tarfile.TarInfo]:
    members = tf.getmembers()
    if len(members) > MAX_MEMBERS:
        raise ProvenanceError("too many archive members")
    seen: set[str] = set()
    total = 0
    for item in members:
        name = item.name.removeprefix("./")
        p = PurePosixPath(name)
        if (
            not name or p.is_absolute() or ".." in p.parts or "\\" in name
            or (name != prefix and not name.startswith(prefix + "/"))
            or name in seen or len(name) > 256 or item.issym() or item.islnk()
            or item.isdev() or item.isfifo()
            or not (item.isfile() or item.isdir())
        ):
            raise ProvenanceError("unsafe or duplicated archive member: " + name)
        seen.add(name)
        if item.isfile():
            total += item.size
            if item.size > 2_000_000 or total > max_total:
                raise ProvenanceError("archive decompression bound exceeded")
    return members


def verified_debian_patch(data: bytes, *, expected: str = PATCH_SHA256) -> bytes:
    """Read exactly the pinned quilt patch without extracting or executing Debian code."""
    found: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:xz") as tf:
        for item in safe_members(tf, prefix="debian", max_total=MAX_UNCOMPRESSED):
            name = item.name.removeprefix("./")
            if item.isfile() and name in {"debian/patches/series", PATCH_PATH}:
                stream = tf.extractfile(item)
                if stream is None:
                    raise ProvenanceError("missing patch stream")
                found[name] = stream.read()
    if set(found) != {"debian/patches/series", PATCH_PATH}:
        raise ProvenanceError("missing pinned quilt series or security patch")
    series = found["debian/patches/series"].decode("utf-8").splitlines()
    names = [line.split()[0] for line in series if line.strip() and not line.lstrip().startswith("#")]
    if names.count(PATCH_NAME) != 1:
        raise ProvenanceError("security patch not uniquely listed in quilt series")
    patch = checked_bytes(found[PATCH_PATH], expected, "Debian security patch", 100_000)
    validate_security_patch(patch)
    return patch


def validate_security_patch(patch: bytes) -> None:
    """Allow only the two security-critical old/new source-line pairs."""
    text = patch.decode("utf-8")
    if (
        text.count("diff --git ") != 1
        or "diff --git a/src/variant_iter.rs b/src/variant_iter.rs" not in text
        or "fn impl_get(&self, i: usize)" not in text
        or "ffi::g_variant_get_child(" not in text
    ):
        raise ProvenanceError("patch includes unknown file or missing upstream function")
    # Only actual diff additions/deletions; exclude +++/--- headers.
    changed = [
        line[0] + line[1:].strip() for line in text.splitlines()
        if (line.startswith("+") and not line.startswith("+++"))
        or (line.startswith("-") and not line.startswith("---"))
    ]
    required = [
        "-let p: *mut libc::c_char = std::ptr::null_mut();",
        "+let mut p: *mut libc::c_char = std::ptr::null_mut();",
        "-&p,",
        "+&mut p,",
    ]
    if sorted(changed) != sorted(required):
        raise ProvenanceError("patch changes more than the upstream two-line fix")


def extract_registry_crate(data: bytes, root: Path) -> Path:
    """Bounded, no-symlink extraction of hash-pinned original crates.io source."""
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        for item in safe_members(tf, prefix="glib-0.18.5", max_total=MAX_UNCOMPRESSED):
            name = item.name.removeprefix("./")
            dest = root.joinpath(*PurePosixPath(name).parts)
            if item.isdir():
                dest.mkdir(parents=True, exist_ok=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            stream = tf.extractfile(item)
            if stream is None:
                raise ProvenanceError("original source archive member unreadable")
            raw = stream.read()
            if len(raw) != item.size:
                raise ProvenanceError("original source archive member truncated")
            # All destination paths are derived from validated relative archive names.
            with dest.open("xb") as out:
                out.write(raw)
    result = root / "glib-0.18.5"
    if not (result / "Cargo.toml").is_file():
        raise ProvenanceError("pinned source has no Cargo manifest")
    return result


def patched_variant(original: bytes) -> bytes:
    """Prove and make exactly the audited two-line Rust pointer fix."""
    if original.count(OLD_DECL) != 1 or original.count(OLD_ARG) != 1:
        raise ProvenanceError("registry glib does not match unique vulnerable preimage")
    start = original.index(b"fn impl_get(&self, i: usize)")
    end = original.find(b"\n    }\n", start)
    if end < 0 or OLD_DECL not in original[start:end] or OLD_ARG not in original[start:end]:
        raise ProvenanceError("security hunk outside expected VariantStrIter::impl_get")
    fixed = original.replace(OLD_DECL, NEW_DECL, 1).replace(OLD_ARG, NEW_ARG, 1)
    if fixed.count(NEW_DECL) != 1 or fixed.count(NEW_ARG) != 1:
        raise ProvenanceError("security fix not uniquely applied")
    return fixed


def manifest(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ProvenanceError("generated source contains symlink")
        if path.is_file():
            name = path.relative_to(root).as_posix()
            if name == RECEIPT_NAME:
                continue
            result[name] = digest(path.read_bytes())
    if not result:
        raise ProvenanceError("source archive empty")
    return result


def assert_equal_tree(expected: Path, actual: Path) -> None:
    if actual.is_symlink() or not actual.is_dir():
        raise ProvenanceError("existing overlay is not a trusted directory")
    want, got = manifest(expected), manifest(actual)
    if want != got:
        raise ProvenanceError("existing patched overlay is stale or modified")
    if (expected / RECEIPT_NAME).read_bytes() != (actual / RECEIPT_NAME).read_bytes():
        raise ProvenanceError("existing overlay provenance receipt mismatch")


def prepare(crate_bytes: bytes, debian_bytes: bytes, *, vendor: Path = VENDOR,
            verify_only: bool = False) -> None:
    checked_bytes(crate_bytes, CRATE_SHA256, "crates.io glib 0.18.5", MAX_CRATE)
    checked_bytes(debian_bytes, DEBIAN_SHA256, "Debian glib 0.18.5-7", MAX_DEBIAN)
    patch = verified_debian_patch(debian_bytes)
    parent = vendor.parent
    if parent.is_symlink() or vendor.is_symlink():
        raise ProvenanceError("symlink at generated vendor path")
    parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".hcoder-glib-staging-", dir=parent))
    try:
        crate = extract_registry_crate(crate_bytes, temporary)
        target = crate / PATCH_TARGET
        original = target.read_bytes()
        fixed = patched_variant(original)
        target.write_bytes(fixed)
        receipt = {
            "contract": "hcoder-glib-backport-provenance-v1",
            "crate": "glib", "version": "0.18.5",
            "crate_sha256": CRATE_SHA256,
            "debian_archive_sha256": DEBIAN_SHA256,
            "debian_quilt_patch": PATCH_NAME,
            "debian_patch_sha256": PATCH_SHA256,
            "original_variant_sha256": digest(original),
            "patched_variant_sha256": digest(fixed),
            "source_files": manifest(crate),
            "signed_dsc_evidence": "HCODER-SEC-0001 / PR #102 / 36591726532",
        }
        (crate / RECEIPT_NAME).write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8"
        )
        if vendor.exists():
            assert_equal_tree(crate, vendor)
        elif verify_only:
            raise ProvenanceError("required local patched crate has not been bootstrapped")
        else:
            os.replace(crate, vendor)
        print("GLIB_PROVENANCE=PINNED_SOURCE_AND_VERIFIED_TWO_LINE_PATCH")
        print("LOCKED_GLIB_CRATE_SHA256=" + CRATE_SHA256)
        print("DEBIAN_PATCH_SHA256=" + PATCH_SHA256)
        print("VENDOR_SOURCE_PATH=" + str(vendor))
        print("VENDOR_TREE_FILES=" + str(len(receipt["source_files"])))
        print("GENERATED_GLIB_ONLY_PATCH=PASS")
    finally:
        shutil.rmtree(temporary)


def emit_original_registry_audit_lock(destination: Path) -> None:
    """Reconstruct exact original registry glib identity in runner TEMP ONLY.

    The canonical committed patch lock intentionally uses local source. Cargo-audit
    skips path packages in its ordinary scan, so retain a separate, fail-closed
    original-registry advisory scan rather than misreport a clean dependency set.
    """
    lock = ROOT / "apps/desktop/src-tauri/Cargo.lock"
    text = lock.read_text(encoding="utf-8")
    prefix = '[[package]]\nname = "glib"\nversion = "0.18.5"\n'
    original = (
        prefix
        + 'source = "registry+https://github.com/rust-lang/crates.io-index"\n'
        + f'checksum = "{CRATE_SHA256}"\n'
    )
    if text.count(prefix) != 1 or original in text:
        raise ProvenanceError("cannot reconstruct uniquely from exact local glib lock")
    target = destination.resolve()
    if target.is_relative_to(ROOT.resolve()):
        raise ProvenanceError("original advisory lock must be runner temp, not tracked source")
    target.parent.mkdir(parents=True, exist_ok=True)
    # No open-ended registry resolution: restore exactly two original lock lines.
    restored = text.replace(prefix, original, 1)
    with target.open("x", encoding="utf-8") as out:
        out.write(restored)
    print("UNPATCHED_GLIB_SHADOW_AUDIT_LOCK=EXACT_REGISTRY_SOURCE_ONLY")


def check_unpatched_registry_advisory(path: Path) -> None:
    """Require RustSec to report the known registry advisory, never silently hide it."""
    report = json.loads(path.read_text(encoding="utf-8"))
    unsound = report.get("warnings", {}).get("unsound", [])
    matched = [
        warning for warning in unsound
        if warning.get("advisory", {}).get("id") == "RUSTSEC-2024-0429"
        and warning.get("package", {}).get("name") == "glib"
        and warning.get("package", {}).get("version") == "0.18.5"
    ]
    if len(matched) != 1 or report.get("settings", {}).get("ignore") != []:
        raise ProvenanceError("original registry RustSec unsoundness warning not visible")
    if report.get("vulnerabilities", {}).get("count", 0) != 0:
        raise ProvenanceError("new registry graph vulnerability requires security review")
    print("REGISTRY_GLIB_ADVISORY_VISIBILITY=RUSTSEC-2024-0429")
    print("PATCHED_GLIB_ADVISORY_STATUS=VERSION_ONLY_BACKPORT_REVIEW_REQUIRED")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crate-archive", type=Path, help="offline, SHA-checked archive")
    parser.add_argument("--debian-archive", type=Path, help="offline, SHA-checked archive")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--emit-original-audit-lock", type=Path)
    parser.add_argument("--check-original-audit-json", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.emit_original_audit_lock:
            emit_original_registry_audit_lock(args.emit_original_audit_lock)
            return 0
        if args.check_original_audit_json:
            check_unpatched_registry_advisory(args.check_original_audit_json)
            return 0
        crate = args.crate_archive.read_bytes() if args.crate_archive else fetch(CRATE_URL, MAX_CRATE)
        debian = (
            args.debian_archive.read_bytes() if args.debian_archive
            else fetch(DEBIAN_URL, MAX_DEBIAN)
        )
        prepare(crate, debian, verify_only=args.verify_only)
        return 0
    except (OSError, ValueError, tarfile.TarError, ProvenanceError) as exc:
        print("GLIB_PROVENANCE=REJECTED: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
