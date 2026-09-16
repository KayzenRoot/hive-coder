from __future__ import annotations

"""Pre-authority loose Git object preparation.

The transaction can deterministically frame/compress an approved SHA-1 blob and
prove its repository-local destination. It deliberately cannot publish into
`.git/objects`; publication authority remains unavailable.
"""

import hashlib
import zlib
from dataclasses import dataclass
from pathlib import Path

from .git_object_candidate import GitBlobCandidate, prepare_git_blob_candidate
from .git_object_store_inspector import GitObjectStoreEnvelope, inspect_local_object_store
from .git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError

LOOSE_OBJECT_TRANSACTION_CONTRACT = "hive-git-loose-object-transaction-v1"


@dataclass(frozen=True)
class GitLooseObjectPreparation:
    contract: str
    candidate: GitBlobCandidate
    store: GitObjectStoreEnvelope
    fanout: str
    leaf: str
    compressed_sha256: str
    compressed_bytes: int

    @property
    def relative_object_path(self) -> str:
        return f"objects/{self.fanout}/{self.leaf}"


def prepare_loose_blob(workspace_root: str | Path, content: bytes) -> tuple[GitLooseObjectPreparation, bytes]:
    candidate = prepare_git_blob_candidate(content)
    store = inspect_local_object_store(workspace_root)
    if store.object_format != "sha1" or len(candidate.oid) != 40:
        raise GitStageUnsupportedRepositoryError("loose-object format is outside the proven envelope")
    framed = b"blob " + str(len(content)).encode("ascii") + b"\x00" + content
    compressed = zlib.compress(framed)
    preparation = GitLooseObjectPreparation(
        contract=LOOSE_OBJECT_TRANSACTION_CONTRACT,
        candidate=candidate,
        store=store,
        fanout=candidate.oid[:2],
        leaf=candidate.oid[2:],
        compressed_sha256=hashlib.sha256(compressed).hexdigest(),
        compressed_bytes=len(compressed),
    )
    return preparation, compressed


class PreAuthorityLooseObjectTransaction:
    """No-publication transaction shell for the Codex implementation frontier."""

    mutation_authority_enabled = False

    def __init__(self, workspace_root: str | Path) -> None:
        self.workspace_root = Path(workspace_root)

    def prepare(self, content: bytes) -> tuple[GitLooseObjectPreparation, bytes]:
        return prepare_loose_blob(self.workspace_root, content)

    def inspect_existing(self, preparation: GitLooseObjectPreparation) -> None:
        del preparation
        raise GitStageUnavailableError("existing loose-object verification is not yet proven")

    def publish(self, preparation: GitLooseObjectPreparation, compressed: bytes) -> None:
        del preparation, compressed
        raise GitStageUnavailableError("loose-object publication authority is unavailable")

    def close(self) -> None:
        return None


__all__ = [
    "LOOSE_OBJECT_TRANSACTION_CONTRACT",
    "GitLooseObjectPreparation",
    "PreAuthorityLooseObjectTransaction",
    "prepare_loose_blob",
]
