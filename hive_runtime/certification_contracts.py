"""Trusted certification contracts for exact execution stacks and evaluation suites."""
from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, replace

from .expert_common import _SAFE_TOKEN, _SHA256, _sha
from .expert_identity import AgentProfile, AgentProfileAuthority


@dataclass(frozen=True)
class ExecutionStackDescriptor:
    """StackGenome: canonical descriptor whose fingerprint must equal AgentProfile.execution_stack_digest."""

    provider_id: str
    model_id: str
    model_revision_digest: str
    toolset_digest: str
    capsule_fingerprint: str
    skillset_digest: str
    runtime_digest: str
    protocol_version: str = "stack-genome-v1"

    def validate(self) -> None:
        for token in (self.provider_id, self.model_id, self.protocol_version):
            if not _SAFE_TOKEN.fullmatch(token):
                raise ValueError("invalid StackGenome token")
        for digest in (
            self.model_revision_digest, self.toolset_digest, self.capsule_fingerprint,
            self.skillset_digest, self.runtime_digest,
        ):
            if not _SHA256.fullmatch(digest):
                raise ValueError("StackGenome digests must be sha256")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "protocol": self.protocol_version,
            "provider": self.provider_id,
            "model": self.model_id,
            "model_revision": self.model_revision_digest,
            "toolset": self.toolset_digest,
            "capsule": self.capsule_fingerprint,
            "skillset": self.skillset_digest,
            "runtime": self.runtime_digest,
        })


class StackGenomeAuthority:
    def __init__(self, profile_authority: AgentProfileAuthority) -> None:
        self.profile_authority = profile_authority

    def verify_binding(self, profile: AgentProfile, descriptor: ExecutionStackDescriptor) -> bool:
        if not self.profile_authority.verify(profile):
            return False
        try:
            descriptor_fp = descriptor.fingerprint()
        except ValueError:
            return False
        return profile.execution_stack_digest == descriptor_fp and profile.capsule_fingerprint == descriptor.capsule_fingerprint


@dataclass(frozen=True)
class EvaluationSuite:
    """SuiteLineage contract. Diversity derives from sealed independence lineage, not caller labels."""

    suite_id: str
    suite_version: str
    family_id: str
    independence_root: str
    generator_id: str
    generator_version: str
    protocol_digest: str
    authority_tag: str = ""

    def validate_unsigned(self) -> None:
        for token in (
            self.suite_id, self.suite_version, self.family_id,
            self.independence_root, self.generator_id, self.generator_version,
        ):
            if not _SAFE_TOKEN.fullmatch(token):
                raise ValueError("invalid evaluation suite token")
        if not _SHA256.fullmatch(self.protocol_digest):
            raise ValueError("evaluation suite protocol digest must be sha256")

    def fingerprint(self) -> str:
        self.validate_unsigned()
        return _sha({
            "suite": self.suite_id, "version": self.suite_version,
            "family": self.family_id, "independence_root": self.independence_root,
            "generator": self.generator_id, "generator_version": self.generator_version,
            "protocol": self.protocol_digest,
        })

    def diversity_family(self) -> str:
        """Stable CP-0011 family identity: cosmetic family names cannot split one lineage."""
        self.validate_unsigned()
        return f"lineage.{_sha({'independence_root': self.independence_root})[:24]}"


class SuiteLineageAuthority:
    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("SuiteLineage key must contain at least 32 bytes")
        self._key = bytes(key)

    def seal(self, suite: EvaluationSuite) -> EvaluationSuite:
        unsigned = replace(suite, authority_tag="")
        tag = hmac.new(self._key, unsigned.fingerprint().encode(), hashlib.sha256).hexdigest()
        return replace(unsigned, authority_tag=tag)

    def verify(self, suite: EvaluationSuite) -> bool:
        if not _SHA256.fullmatch(suite.authority_tag):
            return False
        unsigned = replace(suite, authority_tag="")
        try:
            fingerprint = unsigned.fingerprint()
        except ValueError:
            return False
        expected = hmac.new(self._key, fingerprint.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(suite.authority_tag, expected)
