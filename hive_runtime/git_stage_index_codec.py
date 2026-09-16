from __future__ import annotations

"""Inert Git index codec boundary for HCODER-WO-0023.

The codec is deliberately separated from publication and authority. A future
Dulwich-backed implementation may parse/serialize candidate index bytes, but
must never call porcelain, GitFile.close(), subprocesses, hooks, filters,
network, credentials, or mutate `.git/index` itself.
"""

from dataclasses import dataclass
from typing import Protocol, Sequence

from .git_stage import GitStageUnavailableError
from .git_stage_contract import GitStageObservedState


DULWICH_CANDIDATE_VERSION = "1.2.15"
INDEX_CODEC_CONTRACT = "hive-git-index-codec-v1"


@dataclass(frozen=True)
class GitIndexCandidate:
    codec_id: str
    source_index_sha256: str
    paths: tuple[str, ...]
    serialized: bytes

    def __post_init__(self) -> None:
        if not self.codec_id:
            raise ValueError("codec_id is required")
        if len(self.source_index_sha256) != 64:
            raise ValueError("source index digest must be SHA-256")
        if not self.paths or tuple(sorted(self.paths)) != self.paths or len(set(self.paths)) != len(self.paths):
            raise ValueError("candidate paths must be deterministic unique paths")
        if not isinstance(self.serialized, bytes):
            raise TypeError("serialized candidate must be bytes")


class GitIndexCodec(Protocol):
    codec_id: str

    def build_candidate(
        self,
        observed: GitStageObservedState,
        paths: Sequence[str],
    ) -> GitIndexCandidate: ...


class UnavailableGitIndexCodec:
    """Default codec until dependency provenance and semantics are approved."""

    codec_id = "unavailable-git-index-codec-v1"

    def build_candidate(self, observed: GitStageObservedState, paths: Sequence[str]) -> GitIndexCandidate:
        del observed, paths
        raise GitStageUnavailableError(
            "Git index codec is unavailable until the reviewed backend is explicitly enabled"
        )


class DulwichIndexCodecCandidate:
    """Design placeholder, intentionally non-instantiable and non-mutating.

    Approval requirements before implementation:
      * exact dependency/version/provenance recorded;
      * parse/serialize APIs proven without porcelain or process execution;
      * executable filters, hooks, remotes and credentials impossible in this path;
      * sparse/split/conflicted/unsupported index forms fail closed;
      * candidate bytes are returned to Hive-owned index.lock transaction only;
      * publication remains exclusively Hive-owned and permit-gated.
    """

    codec_id = f"dulwich-{DULWICH_CANDIDATE_VERSION}-candidate"

    def __init__(self) -> None:
        raise GitStageUnavailableError(
            "Dulwich codec remains a reviewed candidate, not runtime authority"
        )


__all__ = [
    "DULWICH_CANDIDATE_VERSION",
    "INDEX_CODEC_CONTRACT",
    "DulwichIndexCodecCandidate",
    "GitIndexCandidate",
    "GitIndexCodec",
    "UnavailableGitIndexCodec",
]
