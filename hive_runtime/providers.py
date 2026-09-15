"""Hive-owned provider/model contracts, catalog normalization and routing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Protocol

from .intelligence.capabilities import CapabilityEvidence, CapabilityRequest, EvidenceState, ModelCapabilityRegistry, ModelProfile


@dataclass(frozen=True)
class ProviderModel:
    model_id: str
    display_name: str


@dataclass(frozen=True)
class CapabilityProbeResult:
    """Raw provider observation. It has no authority to mark itself verified."""
    capability: str
    source: str
    detail: str = ""


class ProviderAdapter(Protocol):
    provider_id: str
    def list_models(self) -> Iterable[ProviderModel]: ...
    def probe(self, model_id: str) -> Iterable[CapabilityProbeResult]: ...


CapabilityVerifier = Callable[[str, str, CapabilityProbeResult], bool]


class CredentialScope:
    """Explicit secret boundary. Values are never printable/serializable by this object."""
    def __init__(self, values: Mapping[str, str]) -> None:
        if any(not k or not isinstance(v, str) or not v for k, v in values.items()):
            raise ValueError("credential keys and values must be non-empty")
        self._values = dict(values)

    def get(self, key: str) -> str:
        return self._values[key]

    def redacted(self) -> dict[str, str]:
        return {key: "[REDACTED]" for key in self._values}

    def __repr__(self) -> str:
        return f"CredentialScope({self.redacted()!r})"


class ProviderCatalog:
    """Catalog whose verification authority is injected by the trusted Hive host."""
    def __init__(self, registry: ModelCapabilityRegistry, verifier: CapabilityVerifier) -> None:
        if not callable(verifier):
            raise TypeError("trusted capability verifier is required")
        self.registry = registry
        self._verifier = verifier
        self._models: dict[tuple[str, str], ProviderModel] = {}

    def refresh(self, adapter: ProviderAdapter) -> tuple[ProviderModel, ...]:
        provider = adapter.provider_id.strip().lower()
        if not provider:
            raise ValueError("provider_id is required")
        models = tuple(adapter.list_models())
        seen: set[str] = set()
        for model in models:
            model_id = model.model_id.strip()
            if not model_id or model_id in seen:
                raise ValueError("provider model ids must be unique and non-empty")
            seen.add(model_id)
            evidence = []
            seen_caps: set[str] = set()
            for probe in adapter.probe(model_id):
                capability = probe.capability.strip()
                if not capability or capability in seen_caps:
                    raise ValueError("probe capabilities must be unique and non-empty")
                seen_caps.add(capability)
                verified = self._verifier(provider, model_id, probe) is True
                evidence.append(CapabilityEvidence(capability, EvidenceState.VERIFIED if verified else EvidenceState.UNKNOWN, probe.source, probe.detail))
            self.registry.register(ModelProfile(provider, model_id, tuple(evidence)))
            self._models[(provider, model_id)] = ProviderModel(model_id, model.display_name.strip() or model_id)
        return models

    def models(self, provider: str) -> tuple[ProviderModel, ...]:
        p = provider.strip().lower()
        return tuple(model for (owner, _), model in self._models.items() if owner == p)


class ModelRouter:
    """Deterministic router: capability eligibility first, caller score second."""
    def __init__(self, registry: ModelCapabilityRegistry, scorer: Callable[[ModelProfile], tuple] | None = None) -> None:
        self.registry = registry
        self.scorer = scorer or (lambda profile: (profile.provider, profile.model_id))

    def select(self, request: CapabilityRequest, *, provider: str | None = None) -> ModelProfile:
        candidates = []
        for profile in self.registry.profiles():
            if provider and profile.provider != provider.strip().lower():
                continue
            if self.registry.negotiate(profile.provider, profile.model_id, request).allowed:
                candidates.append(profile)
        if not candidates:
            raise LookupError("no verified model satisfies required capabilities")
        return min(candidates, key=self.scorer)


class OpenCodeGoProfile:
    """Provider identity only. Capabilities must come from trusted verification, never this name."""
    provider_id = "opencode-go"
