from __future__ import annotations

"""Frozen pre-Codex implementation frontier for HCODER-WO-0023.

This module names the remaining implementation seams without granting any Git
mutation authority. Codex must complete these seams under the WO-0023 handoff,
Context Lock, tests and exact-head evidence gates.
"""

from dataclasses import dataclass

PRE_CODEX_FRONTIER_CONTRACT = "hive-git-stage-pre-codex-frontier-v1"
REQUIRED_ACTION = "git_stage_paths_v1"
REQUIRED_CAPABILITY = "git.write"


@dataclass(frozen=True)
class CodexImplementationFrontier:
    contract: str = PRE_CODEX_FRONTIER_CONTRACT
    action: str = REQUIRED_ACTION
    capability: str = REQUIRED_CAPABILITY
    codec_backend: str = "dulwich-candidate-1.2.15"
    authority_late_binding: bool = True
    public_mutation_enabled: bool = False
    shell_process_allowed: bool = False
    hooks_filters_allowed: bool = False
    network_credentials_allowed: bool = False

    def remaining_seams(self) -> tuple[str, ...]:
        return (
            "prove_and_pin_index_codec_backend",
            "implement_owned_private_loose_object_temp",
            "implement_exact_existing_object_collision_proof",
            "serialize_exact_index_candidate",
            "bind_blob_oids_and_index_digest_to_action_request",
            "add_dedicated_git_write_control_plane_capability",
            "consume_single_use_permit_at_final_safe_boundary",
            "publish_content_addressed_blobs_then_atomic_index",
            "prove_postconditions_and_redacted_receipt",
            "prove_native_windows_linux_macos_e2e",
            "complete_evidence_ledger_and_heds",
        )


FROZEN_FRONTIER = CodexImplementationFrontier()

__all__ = [
    "PRE_CODEX_FRONTIER_CONTRACT",
    "REQUIRED_ACTION",
    "REQUIRED_CAPABILITY",
    "CodexImplementationFrontier",
    "FROZEN_FRONTIER",
]
