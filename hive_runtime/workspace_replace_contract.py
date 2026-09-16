from __future__ import annotations

"""Pure contract definitions for HCODER-WO-0022.

This module intentionally performs no filesystem mutation and grants no authority.
It freezes bounded names/metadata used by the existing-file replacement capability
so platform implementation can be completed without rediscovering the contract.
"""

from dataclasses import dataclass

REPLACE_CONTRACT = "hive-workspace-replace-v1"
REPLACE_ACTION = "replace_file_v1"
REPLACE_TARGET_STATE = "regular"

REPLACE_ARGUMENT_KEYS = frozenset(
    {
        "contract",
        "path",
        "parent_identity",
        "target_state",
        "target_identity",
        "old_content_sha256",
        "old_content_bytes",
        "new_content_sha256",
        "new_content_bytes",
    }
)


@dataclass(frozen=True)
class WorkspaceReplaceObservedState:
    """Bounded pre-approval state of one existing regular target."""

    parent_identity: str
    target_identity: str
    content_sha256: str
    content_bytes: int

    def __post_init__(self) -> None:
        if not self.parent_identity:
            raise ValueError("parent_identity must be non-empty")
        if not self.target_identity:
            raise ValueError("target_identity must be non-empty")
        if len(self.content_sha256) != 64:
            raise ValueError("content_sha256 must be a SHA-256 hex digest")
        try:
            int(self.content_sha256, 16)
        except ValueError as exc:
            raise ValueError("content_sha256 must be hexadecimal") from exc
        if self.content_bytes < 0:
            raise ValueError("content_bytes must be non-negative")


@dataclass(frozen=True)
class WorkspaceReplaceReceipt:
    workspace: str
    relative_path: str
    parent_identity: str
    previous_target_identity: str
    previous_content_sha256: str
    new_content_sha256: str
    new_content_bytes: int
    committed_state: str
