from __future__ import annotations

"""Dependency-free, read-only Git index v2/v3 safety inspector.

The inspector validates the DIRC envelope, ordinary entry framing and extension
surface before a future third-party codec can receive index bytes. It never
writes files and has no process, hook, filter, network or credential surface.
"""

import hashlib
import struct
from dataclasses import dataclass

from .git_stage import GitStageUnsupportedRepositoryError

INDEX_MAGIC = b"DIRC"
SUPPORTED_INDEX_VERSIONS = frozenset({2, 3})
MAX_INDEX_ENTRIES = 1_000_000
MIN_INDEX_BYTES = 12 + 20
ENTRY_FIXED_BYTES = 62
EXTENSION_HEADER_BYTES = 8
KNOWN_SAFE_OPTIONAL_EXTENSIONS = frozenset({b"TREE"})
FORBIDDEN_EXTENSIONS = frozenset({b"link", b"sdir"})


@dataclass(frozen=True)
class GitIndexEnvelope:
    version: int
    entry_count: int
    sha1: str
    payload_bytes: int
    extensions: tuple[str, ...] = ()


def _entry_end(payload: bytes, offset: int, version: int) -> int:
    del version  # v2/v3 share the same pathname framing for this bounded inspector.
    if offset + ENTRY_FIXED_BYTES > len(payload):
        raise GitStageUnsupportedRepositoryError("Git index entry is truncated")
    flags = struct.unpack(">H", payload[offset + 60 : offset + 62])[0]
    stage = (flags >> 12) & 0x3
    if stage != 0:
        raise GitStageUnsupportedRepositoryError("conflicted Git index entries are unsupported")
    name_length = flags & 0x0FFF
    name_start = offset + ENTRY_FIXED_BYTES
    if name_length < 0x0FFF:
        name_end = name_start + name_length
        if name_end >= len(payload) or payload[name_end] != 0:
            raise GitStageUnsupportedRepositoryError("Git index pathname framing is invalid")
    else:
        name_end = payload.find(b"\x00", name_start)
        if name_end < 0:
            raise GitStageUnsupportedRepositoryError("Git index long pathname is unterminated")
    if name_end == name_start:
        raise GitStageUnsupportedRepositoryError("Git index pathname is empty")
    entry_size = name_end - offset + 1
    padded = (entry_size + 7) & ~7
    end = offset + padded
    if end > len(payload):
        raise GitStageUnsupportedRepositoryError("Git index entry padding is truncated")
    return end


def _inspect_extensions(payload: bytes, offset: int) -> tuple[str, ...]:
    found: list[str] = []
    while offset < len(payload):
        if offset + EXTENSION_HEADER_BYTES > len(payload):
            raise GitStageUnsupportedRepositoryError("Git index extension header is truncated")
        signature = payload[offset : offset + 4]
        size = struct.unpack(">I", payload[offset + 4 : offset + 8])[0]
        end = offset + EXTENSION_HEADER_BYTES + size
        if end > len(payload):
            raise GitStageUnsupportedRepositoryError("Git index extension payload is truncated")
        if signature in FORBIDDEN_EXTENSIONS:
            raise GitStageUnsupportedRepositoryError("split/sparse Git index extension is unsupported")
        # Per Git index format, lowercase first byte marks a mandatory extension.
        if 0x61 <= signature[0] <= 0x7A:
            raise GitStageUnsupportedRepositoryError("mandatory Git index extension is unsupported")
        if signature not in KNOWN_SAFE_OPTIONAL_EXTENSIONS:
            raise GitStageUnsupportedRepositoryError("unproven optional Git index extension is unsupported")
        found.append(signature.decode("ascii", "strict"))
        offset = end
    return tuple(found)


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
    actual = hashlib.sha1(payload).digest()
    if actual != checksum:
        raise GitStageUnsupportedRepositoryError("Git index checksum is invalid")

    offset = 12
    for _ in range(entry_count):
        offset = _entry_end(payload, offset, version)
    extensions = _inspect_extensions(payload, offset)
    return GitIndexEnvelope(version, entry_count, actual.hex(), len(payload), extensions)


__all__ = [
    "FORBIDDEN_EXTENSIONS",
    "GitIndexEnvelope",
    "INDEX_MAGIC",
    "KNOWN_SAFE_OPTIONAL_EXTENSIONS",
    "MAX_INDEX_ENTRIES",
    "MIN_INDEX_BYTES",
    "SUPPORTED_INDEX_VERSIONS",
    "inspect_git_index_envelope",
]
