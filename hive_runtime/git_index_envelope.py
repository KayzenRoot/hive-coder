from __future__ import annotations

"""Dependency-free, read-only Git index envelope inspector.

This is not an index parser or writer. It validates the outer DIRC envelope so
unsupported/corrupt inputs fail closed before any future third-party codec is
allowed to see them. No filesystem, process, hook, filter, network or credential
operation exists in this module.
"""

import hashlib
import struct
from dataclasses import dataclass

from .git_stage import GitStageUnsupportedRepositoryError

INDEX_MAGIC = b"DIRC"
SUPPORTED_INDEX_VERSIONS = frozenset({2, 3})
MAX_INDEX_ENTRIES = 1_000_000
MIN_INDEX_BYTES = 12 + 20


@dataclass(frozen=True)
class GitIndexEnvelope:
    version: int
    entry_count: int
    sha1: str
    payload_bytes: int


def inspect_git_index_envelope(data: bytes) -> GitIndexEnvelope:
    if not isinstance(data, bytes):
        raise TypeError("Git index envelope input must be bytes")
    if len(data) < MIN_INDEX_BYTES:
        raise GitStageUnsupportedRepositoryError("Git index is truncated")
    if data[:4] != INDEX_MAGIC:
        raise GitStageUnsupportedRepositoryError("Git index signature is invalid")

    version, entry_count = struct.unpack(">II", data[4:12])
    if version not in SUPPORTED_INDEX_VERSIONS:
        raise GitStageUnsupportedRepositoryError("Git index version is outside the proven envelope")
    if entry_count > MAX_INDEX_ENTRIES:
        raise GitStageUnsupportedRepositoryError("Git index entry count exceeds governed ceiling")

    payload, checksum = data[:-20], data[-20:]
    actual = hashlib.sha1(payload).digest()  # Git index v2/v3 checksum is SHA-1 by format.
    if actual != checksum:
        raise GitStageUnsupportedRepositoryError("Git index checksum is invalid")

    return GitIndexEnvelope(version, entry_count, actual.hex(), len(payload))


__all__ = [
    "GitIndexEnvelope",
    "INDEX_MAGIC",
    "MAX_INDEX_ENTRIES",
    "MIN_INDEX_BYTES",
    "SUPPORTED_INDEX_VERSIONS",
    "inspect_git_index_envelope",
]
