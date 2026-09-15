"""Hive model capability registry and deterministic negotiation."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class EvidenceState(str, Enum):
    VERIFIED = "verified"
    DECLARED = "declared"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CapabilityEvidence:
    capability: str
    state: EvidenceState
    source: str
    detail: str = ""


@dataclass(frozen=True)
class ModelProfile:
    provider: str
    model_id: str
    evidence: tuple[CapabilityEvidence, ...] = field(default_factory=tuple)

    def verified_capabilities(self) -> frozenset[str]:
        return frozenset(item.capability for item in self.evidence if item.state is EvidenceState.VERIFIED)


@dataclass(frozen=True)
class CapabilityRequest:
    required: frozenset[str]
    optional: frozenset[str] = frozenset()


@dataclass(frozen=True)
class NegotiationResult:
    allowed: bool
    enabled: frozenset[str]
    missing: frozenset[str]


class ModelCapabilityRegistry:
    """Registry where capability truth comes from evidence, never model names/prose."""

    def __init__(self) -> None:
        self._profiles: dict[tuple[str, str], ModelProfile] = {}

    def register(self, profile: ModelProfile) -> None:
        key = (profile.provider.strip().lower(), profile.model_id.strip())
        if not key[0] or not key[1]:
            raise ValueError("provider and model_id are required")
        if len({e.capability for e in profile.evidence}) != len(profile.evidence):
            raise ValueError("duplicate capability evidence")
        self._profiles[key] = profile

    def get(self, provider: str, model_id: str) -> ModelProfile:
        try:
            return self._profiles[(provider.strip().lower(), model_id.strip())]
        except KeyError as exc:
            raise KeyError("unknown model profile") from exc

    def negotiate(self, provider: str, model_id: str, request: CapabilityRequest) -> NegotiationResult:
        verified = self.get(provider, model_id).verified_capabilities()
        missing = request.required - verified
        enabled = (request.required | request.optional) & verified
        return NegotiationResult(not missing, enabled, missing)

    def profiles(self) -> Iterable[ModelProfile]:
        return tuple(self._profiles.values())
