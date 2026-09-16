from __future__ import annotations

"""Pure Git blob candidate computation for governed staging.

This module computes the canonical SHA-1 Git blob object identity from approved
bytes. It deliberately has no filesystem, subprocess, network, hook, filter,
credential, compression or publication surface. Object-store mutation remains
separately governed and unavailable.
"""

import hashlib
from dataclasses import dataclass

GIT_BLOB_CANDIDATE_CONTRACT = "hive-git-blob-candidate-v1"
GIT_OBJECT_FORMAT = "sha1"
MAX_GIT_BLOB_BYTES = 16 * 1024 * 1024


@dataclass(frozen=True)
class GitBlobCandidate:
    contract: str
    object_format: str
    oid: str
    content_sha256: str
    content_bytes: int


def prepare_git_blob_candidate(content: bytes) -> GitBlobCandidate:
    if not isinstance(content, bytes):
        raise TypeError("Git blob candidate content must be bytes")
    if len(content) > MAX_GIT_BLOB_BYTES:
        raise ValueError("Git blob candidate exceeds governed ceiling")
    header = b"blob " + str(len(content)).encode("ascii") + b"\x00"
    oid = hashlib.sha1(header + content).hexdigest()
    return GitBlobCandidate(
        contract=GIT_BLOB_CANDIDATE_CONTRACT,
        object_format=GIT_OBJECT_FORMAT,
        oid=oid,
        content_sha256=hashlib.sha256(content).hexdigest(),
        content_bytes=len(content),
    )


__all__ = [
    "GIT_BLOB_CANDIDATE_CONTRACT",
    "GIT_OBJECT_FORMAT",
    "MAX_GIT_BLOB_BYTES",
    "GitBlobCandidate",
    "prepare_git_blob_candidate",
]
