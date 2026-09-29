"""Adversarial offline tests for HCODER-SEC-0001's build-time glib source guard."""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
import importlib.util

MODULE = Path(__file__).resolve().parents[2] / "tools/desktop/bootstrap_glib_patch.py"
spec = importlib.util.spec_from_file_location("hcoder_glib_bootstrap", MODULE)
assert spec and spec.loader
glib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(glib)

ORIGINAL = (
    b"impl<'a> VariantStrIter<'a> {\n"
    b"    fn impl_get(&self, i: usize) -> &'a str {\n"
    b"        unsafe {\n"
    b"            let p: *mut libc::c_char = std::ptr::null_mut();\n"
    b"            ffi::g_variant_get_child(\n"
    b"                self.variant.to_glib_none().0,\n"
    b"                i,\n"
    b"                &p,\n"
    b"            );\n"
    b"        }\n"
    b"    }\n"
    b"}\n"
)

PATCH = (
    "Subject: fix UB in VariantStrIter::impl_get\n"
    "---\n"
    " src/variant_iter.rs | 4 ++--\n"
    " 1 file changed, 2 insertions(+), 2 deletions(-)\n"
    "diff --git a/src/variant_iter.rs b/src/variant_iter.rs\n"
    "--- a/src/variant_iter.rs\n"
    "+++ b/src/variant_iter.rs\n"
    "@@ -117,13 +117,13 @@ impl<'a> VariantStrIter<'a> {\n"
    "     fn impl_get(&self, i: usize) -> &'a str {\n"
    "         unsafe {\n"
    "-            let p: *mut libc::c_char = std::ptr::null_mut();\n"
    "+            let mut p: *mut libc::c_char = std::ptr::null_mut();\n"
    "             ffi::g_variant_get_child(\n"
    "-                &p,\n"
    "+                &mut p,\n"
).encode()


def tar_bytes(entries: list[tuple[str, bytes | None, bytes | None]], mode: str) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode=mode) as tar:
        for name, data, special in entries:
            member = tarfile.TarInfo(name)
            if special == b"symlink":
                member.type = tarfile.SYMTYPE
                member.linkname = "/etc/passwd"
            elif data is None:
                member.type = tarfile.DIRTYPE
            else:
                member.size = len(data)
            tar.addfile(member, None if data is None else io.BytesIO(data))
    return output.getvalue()


class GlibProvenanceTests(unittest.TestCase):
    def test_upstream_two_line_hunk_only(self) -> None:
        glib.validate_security_patch(PATCH)
        patched = glib.patched_variant(ORIGINAL)
        self.assertEqual(patched.count(glib.NEW_DECL), 1)
        self.assertEqual(patched.count(glib.NEW_ARG), 1)
        self.assertEqual(patched.replace(glib.NEW_DECL, glib.OLD_DECL, 1)
                         .replace(glib.NEW_ARG, glib.OLD_ARG, 1), ORIGINAL)

    def test_extra_code_change_rejected(self) -> None:
        for tamper in (PATCH + b"+    unsafe { let _ = 1; }\n",
                       PATCH.replace(b"diff --git a/src/variant_iter.rs b/src/variant_iter.rs",
                                     b"diff --git a/src/foo.rs b/src/foo.rs"),
                       PATCH.replace(b"&mut p,", b"&p,")):
            with self.subTest(tamper=tamper[-50:]):
                with self.assertRaises(glib.ProvenanceError):
                    glib.validate_security_patch(tamper)

    def test_patched_or_nonmatching_preimage_rejected(self) -> None:
        patched = glib.patched_variant(ORIGINAL)
        for bad in (patched, ORIGINAL.replace(b"&p,", b"&other,"), b"fn impl_get(&self, i: usize)"):
            with self.subTest(preimage=bad[:30]):
                with self.assertRaises(glib.ProvenanceError):
                    glib.patched_variant(bad)

    def test_debian_quilt_series_and_patch_must_match(self) -> None:
        official = [
            ("debian/", None, None),
            ("debian/patches/", None, None),
            ("debian/patches/series", (glib.PATCH_NAME + "\n").encode(), None),
            (glib.PATCH_PATH, PATCH, None),
        ]
        data = tar_bytes(official, "w:xz")
        self.assertEqual(glib.verified_debian_patch(
            data, expected=hashlib.sha256(PATCH).hexdigest()), PATCH)
        for modified in (
            official[:-1],
            [*official[:2], ("debian/patches/series", b"other.patch\n", None), official[-1]],
        ):
            with self.subTest(modified=modified):
                with self.assertRaises(glib.ProvenanceError):
                    glib.verified_debian_patch(
                        tar_bytes(modified, "w:xz"),
                        expected=hashlib.sha256(PATCH).hexdigest())

    def test_debian_archive_rejects_links_and_traversal(self) -> None:
        for name, special in (
            ("debian/patches/../../etc/passwd", None),
            ("debian/patches/link", b"symlink"),
            ("../debian/patches/series", None),
        ):
            entries = [(name, b"x", special)]
            with self.subTest(name=name):
                with self.assertRaises(glib.ProvenanceError):
                    glib.verified_debian_patch(
                        tar_bytes(entries, "w:xz"),
                        expected=hashlib.sha256(PATCH).hexdigest())

    def test_duplicate_archive_member_rejected(self) -> None:
        data = tar_bytes([
            ("glib-0.18.5/Cargo.toml", b"[package]\nname=\"glib\"\n", None),
            ("glib-0.18.5/Cargo.toml", b"malicious", None),
        ], "w:gz")
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(glib.ProvenanceError):
                glib.extract_registry_crate(data, Path(folder))

    def test_original_source_extract_is_bounded_and_no_symlinks(self) -> None:
        good = tar_bytes([
            ("glib-0.18.5/", None, None),
            ("glib-0.18.5/Cargo.toml", b"[package]\nname=\"glib\"\n", None),
            ("glib-0.18.5/src/", None, None),
            ("glib-0.18.5/src/variant_iter.rs", ORIGINAL, None),
        ], "w:gz")
        with tempfile.TemporaryDirectory() as folder:
            source = glib.extract_registry_crate(good, Path(folder))
            self.assertEqual((source / glib.PATCH_TARGET).read_bytes(), ORIGINAL)
        for bad in (
            tar_bytes([("glib-0.18.5/src/../escape", b"bad", None)], "w:gz"),
            tar_bytes([("glib-0.18.5/symlink", b"bad", b"symlink")], "w:gz"),
            tar_bytes([("glib-0.18.5/large", b"x" * 2_000_001, None)], "w:gz"),
        ):
            with tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(glib.ProvenanceError):
                    glib.extract_registry_crate(bad, Path(folder))

    def test_existing_vendor_modification_refused(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            expected, actual = Path(folder) / "expected", Path(folder) / "actual"
            for root in (expected, actual):
                root.mkdir()
                (root / "Cargo.toml").write_text("[package]\nname=\"glib\"\n")
                (root / "src").mkdir()
                (root / glib.PATCH_TARGET).write_bytes(glib.patched_variant(ORIGINAL))
                (root / glib.RECEIPT_NAME).write_text('{"signed": "synthetic test only"}')
            glib.assert_equal_tree(expected, actual)
            (actual / glib.PATCH_TARGET).write_bytes(ORIGINAL)
            with self.assertRaises(glib.ProvenanceError):
                glib.assert_equal_tree(expected, actual)

    def test_pin_or_transport_failure_refused(self) -> None:
        with self.assertRaises(glib.ProvenanceError):
            glib.checked_bytes(b"tampered", glib.CRATE_SHA256, "test", glib.MAX_CRATE)
        for url in ("http://static.crates.io/x", "https://example.com/crate",
                    "file:///tmp/glib.crate"):
            with self.assertRaises(glib.ProvenanceError):
                glib.fetch(url, 1)


if __name__ == "__main__":
    unittest.main()
