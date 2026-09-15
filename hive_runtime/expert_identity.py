"""Versioned expertise identity and trusted-host profile sealing."""
from __future__ import annotations
import hashlib
import hmac
from dataclasses import dataclass, replace
from typing import Iterable, Mapping
from .orchestration import AgentRole
from .expert_common import _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha, BenchmarkDimension

def _validate_texts(values: Iterable[str], *, field: str) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(not isinstance(value, str) or not value.strip() for value in result):
        raise ValueError(f"{field} must contain non-empty text")
    return result

@dataclass(frozen=True)
class ExpertiseCapsule:
    capsule_id: str
    version: str
    role: AgentRole
    domains: tuple[str, ...]
    principles: tuple[str, ...]
    anti_patterns: tuple[str, ...]
    review_lenses: tuple[str, ...]
    required_model_capabilities: frozenset[str]
    allowed_tool_kinds: frozenset[str]
    benchmark_dimensions: frozenset[BenchmarkDimension]
    provenance_digest: str

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.capsule_id) or not _SAFE_TOKEN.fullmatch(self.version):
            raise ValueError("invalid expertise capsule identity")
        _validate_texts(self.domains, field="domains")
        _validate_texts(self.principles, field="principles")
        _validate_texts(self.anti_patterns, field="anti_patterns")
        _validate_texts(self.review_lenses, field="review_lenses")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.required_model_capabilities):
            raise ValueError("invalid capsule model capability")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.allowed_tool_kinds):
            raise ValueError("invalid capsule tool kind")
        if not self.benchmark_dimensions:
            raise ValueError("capsule requires benchmark dimensions")
        if not _SHA256.fullmatch(self.provenance_digest):
            raise ValueError("capsule provenance must be sha256")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "id": self.capsule_id,
            "version": self.version,
            "role": self.role.value,
            "domains": list(self.domains),
            "principles": list(self.principles),
            "anti_patterns": list(self.anti_patterns),
            "review_lenses": list(self.review_lenses),
            "model_capabilities": sorted(self.required_model_capabilities),
            "tool_kinds": sorted(self.allowed_tool_kinds),
            "benchmarks": sorted(item.value for item in self.benchmark_dimensions),
            "provenance": self.provenance_digest,
        })


@dataclass(frozen=True)
class AgentProfile:
    agent_id: str
    role: AgentRole
    capsule_fingerprint: str
    required_model_capabilities: frozenset[str]
    max_context_tokens: int
    independence_key: str
    execution_stack_digest: str
    profile_tag: str = ""

    def validate_unsigned(self) -> None:
        if not _SAFE_ID.fullmatch(self.agent_id) or not _SAFE_ID.fullmatch(self.independence_key):
            raise ValueError("invalid agent profile identity")
        if not _SHA256.fullmatch(self.capsule_fingerprint):
            raise ValueError("invalid capsule fingerprint")
        if any(not _SAFE_TOKEN.fullmatch(item) for item in self.required_model_capabilities):
            raise ValueError("invalid profile capability")
        if not _SHA256.fullmatch(self.execution_stack_digest):
            raise ValueError("invalid execution stack digest")
        if not 512 <= self.max_context_tokens <= 2_000_000:
            raise ValueError("invalid context token budget")

    def fingerprint(self) -> str:
        self.validate_unsigned()
        return _sha({
            "agent_id": self.agent_id,
            "role": self.role.value,
            "capsule": self.capsule_fingerprint,
            "model_capabilities": sorted(self.required_model_capabilities),
            "max_context_tokens": self.max_context_tokens,
            "independence_key": self.independence_key,
            "execution_stack": self.execution_stack_digest,
        })


class AgentProfileAuthority:
    """Trusted-host seal. It proves profile provenance, not execution authority."""

    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("agent profile authority key must contain at least 32 bytes")
        self._key = bytes(key)

    def seal(self, profile: AgentProfile) -> AgentProfile:
        unsigned = replace(profile, profile_tag="")
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, profile_tag=tag)

    def verify(self, profile: AgentProfile) -> bool:
        if not _SHA256.fullmatch(profile.profile_tag):
            return False
        unsigned = replace(profile, profile_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(profile.profile_tag, expected)

class ExpertAgentRegistry:
    def __init__(self, profile_authority: AgentProfileAuthority) -> None:
        self.profile_authority = profile_authority
        self._capsules: dict[str, ExpertiseCapsule] = {}
        self._profiles: dict[str, AgentProfile] = {}

    def add_capsule(self, capsule: ExpertiseCapsule) -> str:
        fingerprint = capsule.fingerprint()
        if fingerprint in self._capsules:
            raise ValueError("duplicate expertise capsule")
        self._capsules[fingerprint] = capsule
        return fingerprint

    def add_profile(self, profile: AgentProfile) -> None:
        if not self.profile_authority.verify(profile):
            raise PermissionError("unsealed agent profile")
        if profile.agent_id in self._profiles:
            raise ValueError("duplicate agent profile")
        capsule = self._capsules.get(profile.capsule_fingerprint)
        if capsule is None or capsule.role is not profile.role:
            raise ValueError("profile references missing or wrong-role capsule")
        if not capsule.required_model_capabilities.issubset(profile.required_model_capabilities):
            raise ValueError("profile lacks capsule-required model capabilities")
        self._profiles[profile.agent_id] = profile

    def profiles_for(self, role: AgentRole) -> tuple[AgentProfile, ...]:
        return tuple(sorted((p for p in self._profiles.values() if p.role is role), key=lambda p: p.agent_id))

    def capsules(self) -> Mapping[str, ExpertiseCapsule]:
        return dict(self._capsules)

    def get_profile(self, agent_id: str) -> AgentProfile:
        return self._profiles[agent_id]

    def capsule_for(self, profile: AgentProfile) -> ExpertiseCapsule:
        capsule = self._capsules.get(profile.capsule_fingerprint)
        if capsule is None:
            raise LookupError("agent capsule is not registered")
        return capsule
