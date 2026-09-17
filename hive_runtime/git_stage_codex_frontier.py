from __future__ import annotations

"""Frozen pre-Codex implementation frontier for HCODER-WO-0023.

This module records the seams that the pre-Codex preparation phase handed to the
executor. It grants no authority and mints nothing: the governed capability lives
in ``hive_runtime/git_stage.py`` and is gated by the Permission & Control Plane.

The pre-Codex list is kept verbatim as a historical record. ``completed_seams``
reports which of those seams the executor has since implemented, so this module
never claims that finished work is still outstanding.
"""

from dataclasses import dataclass

PRE_CODEX_FRONTIER_CONTRACT = "hive-git-stage-pre-codex-frontier-v1"
REQUIRED_ACTION = "git_stage_paths_v1"
REQUIRED_CAPABILITY = "git.write"

_PRE_CODEX_SEAMS = (
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

_COMPLETED_SEAMS = _PRE_CODEX_SEAMS[:-1]


@dataclass(frozen=True)
class CodexImplementationFrontier:
    contract: str = PRE_CODEX_FRONTIER_CONTRACT
    action: str = REQUIRED_ACTION
    capability: str = REQUIRED_CAPABILITY
    codec_backend: str = "dulwich-1.2.15-pure-python-index-codec-v1"
    authority_late_binding: bool = True
    public_mutation_enabled: bool = True
    shell_process_allowed: bool = False
    hooks_filters_allowed: bool = False
    network_credentials_allowed: bool = False

    def pre_codex_seams(self) -> tuple[str, ...]:
        """The seam list as handed over by the pre-Codex phase. Historical."""
        return _PRE_CODEX_SEAMS

    def completed_seams(self) -> tuple[str, ...]:
        """Seams implemented by the executor under a Context Lock delta."""
        return _COMPLETED_SEAMS

    def remaining_seams(self) -> tuple[str, ...]:
        """Seams not yet complete. Only the independent HEDS promotion review remains."""
        return tuple(seam for seam in _PRE_CODEX_SEAMS if seam not in _COMPLETED_SEAMS)


FROZEN_FRONTIER = CodexImplementationFrontier()

__all__ = [
    "PRE_CODEX_FRONTIER_CONTRACT",
    "REQUIRED_ACTION",
    "REQUIRED_CAPABILITY",
    "CodexImplementationFrontier",
    "FROZEN_FRONTIER",
]
