"""Governed Hive skill manifests, store and activation boundary."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping

_SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SkillEvaluator = Callable[["SkillManifest", str], Mapping[str, object]]
CapabilityAuthorizer = Callable[["SkillManifest"], frozenset[str]]


class SkillTrust(str, Enum):
    LOCAL_VERIFIED = "local_verified"
    MCP_UNTRUSTED = "mcp_untrusted"


class SkillState(str, Enum):
    INSTALLED = "installed"
    VALIDATED = "validated"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class SkillManifest:
    skill_id: str
    version: str
    title: str
    entrypoint: str
    requested_capabilities: frozenset[str] = frozenset()
    provenance: str = ""
    digest: str = ""

    def validate(self) -> None:
        if not _SKILL_ID.fullmatch(self.skill_id): raise ValueError("invalid skill id")
        if not _VERSION.fullmatch(self.version): raise ValueError("version must be strict semver x.y.z")
        if not self.title.strip() or not self.entrypoint.strip() or not self.provenance.strip(): raise ValueError("title, entrypoint and provenance are required")
        if any(not cap.strip() for cap in self.requested_capabilities): raise ValueError("empty capability")


@dataclass
class SkillRecord:
    manifest: SkillManifest
    content: str
    trust: SkillTrust
    state: SkillState = SkillState.INSTALLED
    evaluation_digest: str | None = None


class SkillStore:
    """Skills are data; trusted host-injected evaluator/authorizer own promotion."""

    def __init__(self, *, evaluator: SkillEvaluator, capability_authorizer: CapabilityAuthorizer) -> None:
        self._records: dict[tuple[str, str], SkillRecord] = {}
        self._evaluator = evaluator
        self._capability_authorizer = capability_authorizer

    @staticmethod
    def content_digest(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def ingest(self, manifest: SkillManifest, content: str, trust: SkillTrust) -> SkillRecord:
        manifest.validate(); digest = self.content_digest(content)
        if manifest.digest and manifest.digest != digest: raise ValueError("skill digest mismatch")
        key = (manifest.skill_id, manifest.version)
        if key in self._records: raise ValueError("skill version already exists")
        record = SkillRecord(manifest=manifest, content=content, trust=trust); self._records[key] = record; return record

    def ingest_mcp_resource(self, manifest: SkillManifest, content: str) -> SkillRecord:
        return self.ingest(manifest, content, SkillTrust.MCP_UNTRUSTED)

    def evaluate(self, skill_id: str, version: str) -> SkillRecord:
        record = self._records[(skill_id, version)]
        evaluation = dict(self._evaluator(record.manifest, record.content))
        if evaluation.get("passed") is not True: raise ValueError("skill evaluation did not pass")
        # Bind evidence to the exact immutable identity/content being promoted.
        envelope = {"skill_id": skill_id, "version": version, "content_sha256": self.content_digest(record.content), "evaluation": evaluation}
        payload = json.dumps(envelope, sort_keys=True, separators=(",", ":"), default=str)
        record.evaluation_digest = hashlib.sha256(payload.encode()).hexdigest(); record.state = SkillState.VALIDATED; return record

    def activate(self, skill_id: str, version: str) -> SkillRecord:
        record = self._records[(skill_id, version)]
        if record.state is not SkillState.VALIDATED: raise PermissionError("skill must be validated before activation")
        granted = self._capability_authorizer(record.manifest)
        if not record.manifest.requested_capabilities.issubset(granted): raise PermissionError("skill requested capabilities outside trusted authorization")
        record.state = SkillState.ACTIVE; return record

    def rollback(self, skill_id: str, version: str) -> SkillRecord:
        record = self._records[(skill_id, version)]; record.state = SkillState.ROLLED_BACK; return record
