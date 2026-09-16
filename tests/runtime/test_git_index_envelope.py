from __future__ import annotations

import hashlib
import struct
import unittest

from hive_runtime.git_index_envelope import inspect_git_index_envelope
from hive_runtime.git_stage import GitStageUnsupportedRepositoryError


def index_fixture(version: int = 2, entries: int = 0, body: bytes = b"") -> bytes:
    payload = b"DIRC" + struct.pack(">II", version, entries) + body
    return payload + hashlib.sha1(payload).digest()


class GitIndexEnvelopeTests(unittest.TestCase):
    def test_accepts_checksum_valid_v2_and_v3_outer_envelopes(self) -> None:
        for version in (2, 3):
            with self.subTest(version=version):
                data = index_fixture(version)
                envelope = inspect_git_index_envelope(data)
                self.assertEqual(envelope.version, version)
                self.assertEqual(envelope.entry_count, 0)
                self.assertEqual(envelope.sha1, hashlib.sha1(data[:-20]).hexdigest())

    def test_rejects_truncated_wrong_magic_and_bad_checksum(self) -> None:
        cases = [b"", b"DIRC", b"NOPE" + index_fixture()[4:]]
        damaged = bytearray(index_fixture()); damaged[-1] ^= 0x01; cases.append(bytes(damaged))
        for data in cases:
            with self.subTest(length=len(data)):
                with self.assertRaises(GitStageUnsupportedRepositoryError):
                    inspect_git_index_envelope(data)

    def test_rejects_unproven_versions_including_v4(self) -> None:
        for version in (0, 1, 4, 5, 0xFFFFFFFF):
            with self.subTest(version=version):
                with self.assertRaises(GitStageUnsupportedRepositoryError):
                    inspect_git_index_envelope(index_fixture(version))

    def test_rejects_governance_entry_count_ceiling_before_codec(self) -> None:
        with self.assertRaises(GitStageUnsupportedRepositoryError):
            inspect_git_index_envelope(index_fixture(2, 1_000_001))

    def test_inspector_is_bytes_only_and_has_no_publication_surface(self) -> None:
        with self.assertRaises(TypeError):
            inspect_git_index_envelope(bytearray(index_fixture()))  # type: ignore[arg-type]
        envelope = inspect_git_index_envelope(index_fixture())
        self.assertFalse(hasattr(envelope, "publish"))
        self.assertFalse(hasattr(envelope, "permit_token"))
        self.assertFalse(hasattr(envelope, "path"))


if __name__ == "__main__":
    unittest.main()
