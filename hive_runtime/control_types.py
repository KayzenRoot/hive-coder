from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class RiskClass(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Capability(str, Enum):
    SCREEN_OBSERVE = "screen.observe"
    ACCESSIBILITY_OBSERVE = "accessibility.observe"
    WINDOW_OBSERVE = "window.observe"
    POINTER_INPUT = "pointer.input"
    KEYBOARD_INPUT = "keyboard.input"
    TEXT_INPUT = "text.input"
    CLIPBOARD_READ = "clipboard.read"
    CLIPBOARD_WRITE = "clipboard.write"
    WINDOW_MUTATE = "window.mutate"
    BROWSER_READ = "browser.read"
    BROWSER_MUTATE = "browser.mutate"
    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"
    GIT_WRITE = "git.write"
    SHELL_EXECUTE = "shell.execute"
    DESTRUCTIVE = "destructive"
    PRIVILEGED = "privileged"


@dataclass(frozen=True)
class CapabilitySpec:
    capability: Capability
    risk: RiskClass
    required_target_fields: frozenset[str]
    materially_sensitive: bool
    mandatory_approval: bool


CAPABILITY_SPECS: dict[Capability, CapabilitySpec] = {
    Capability.SCREEN_OBSERVE: CapabilitySpec(Capability.SCREEN_OBSERVE, RiskClass.HIGH, frozenset(), True, True),
    Capability.ACCESSIBILITY_OBSERVE: CapabilitySpec(Capability.ACCESSIBILITY_OBSERVE, RiskClass.MEDIUM, frozenset({"application", "window_id"}), True, False),
    Capability.WINDOW_OBSERVE: CapabilitySpec(Capability.WINDOW_OBSERVE, RiskClass.MEDIUM, frozenset({"application", "window_id"}), True, False),
    Capability.POINTER_INPUT: CapabilitySpec(Capability.POINTER_INPUT, RiskClass.HIGH, frozenset({"application", "window_id"}), True, True),
    Capability.KEYBOARD_INPUT: CapabilitySpec(Capability.KEYBOARD_INPUT, RiskClass.HIGH, frozenset({"application", "window_id"}), True, True),
    Capability.TEXT_INPUT: CapabilitySpec(Capability.TEXT_INPUT, RiskClass.HIGH, frozenset({"application", "window_id"}), True, True),
    Capability.CLIPBOARD_READ: CapabilitySpec(Capability.CLIPBOARD_READ, RiskClass.HIGH, frozenset(), True, True),
    Capability.CLIPBOARD_WRITE: CapabilitySpec(Capability.CLIPBOARD_WRITE, RiskClass.HIGH, frozenset(), True, True),
    Capability.WINDOW_MUTATE: CapabilitySpec(Capability.WINDOW_MUTATE, RiskClass.HIGH, frozenset({"application", "window_id"}), True, True),
    Capability.BROWSER_READ: CapabilitySpec(Capability.BROWSER_READ, RiskClass.MEDIUM, frozenset({"application", "window_id"}), True, False),
    Capability.BROWSER_MUTATE: CapabilitySpec(Capability.BROWSER_MUTATE, RiskClass.HIGH, frozenset({"application", "window_id"}), True, True),
    Capability.FILESYSTEM_READ: CapabilitySpec(Capability.FILESYSTEM_READ, RiskClass.MEDIUM, frozenset({"workspace"}), True, False),
    Capability.FILESYSTEM_WRITE: CapabilitySpec(Capability.FILESYSTEM_WRITE, RiskClass.HIGH, frozenset({"workspace"}), True, True),
    Capability.GIT_WRITE: CapabilitySpec(Capability.GIT_WRITE, RiskClass.HIGH, frozenset({"workspace"}), True, True),
    Capability.SHELL_EXECUTE: CapabilitySpec(Capability.SHELL_EXECUTE, RiskClass.CRITICAL, frozenset({"workspace"}), True, True),
    Capability.DESTRUCTIVE: CapabilitySpec(Capability.DESTRUCTIVE, RiskClass.CRITICAL, frozenset({"resource"}), True, True),
    Capability.PRIVILEGED: CapabilitySpec(Capability.PRIVILEGED, RiskClass.CRITICAL, frozenset({"resource"}), True, True),
}


class SessionState(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EMERGENCY_STOPPED = "emergency_stopped"
    USER_TAKEOVER = "user_takeover"
    EXPIRED = "expired"


class DecisionKind(str, Enum):
    DENY = "deny"
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(frozen=True)
class ActionTarget:
    workspace: str | None = None
    application: str | None = None
    window_id: str | None = None
    resource: str | None = None

    def canonical(self) -> dict[str, str | None]:
        workspace = None if self.workspace is None else normalize_workspace(self.workspace)
        application = None if self.application is None else normalize_application(self.application)
        window_id = None if self.window_id is None else str(self.window_id).strip()
        resource = None if self.resource is None else str(self.resource).strip()
        return {
            "workspace": workspace,
            "application": application,
            "window_id": window_id,
            "resource": resource,
        }


@dataclass(frozen=True)
class ActionRequest:
    session_id: str
    capability: Capability | str
    action: str
    target: ActionTarget = field(default_factory=ActionTarget)
    arguments: Mapping[str, Any] = field(default_factory=dict)
    untrusted_context: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    kind: DecisionKind
    reason: str
    risk: RiskClass | None
    request_fingerprint: str
    policy_epoch: int


@dataclass(frozen=True)
class ApprovalChallenge:
    challenge_id: str
    session_id: str
    request_fingerprint: str
    policy_epoch: int
    expires_at: float
    capability: str
    action: str
    target_json: str
    arguments_sha256: str
    display_arguments_json: str

    @property
    def target(self) -> Mapping[str, Any]:
        return json.loads(self.target_json)

    @property
    def display_arguments(self) -> Mapping[str, Any]:
        return json.loads(self.display_arguments_json)


@dataclass(frozen=True)
class ExecutionPermit:
    token: str
    session_id: str
    request_fingerprint: str
    policy_epoch: int
    expires_at: float


def normalize_application(value: str) -> str:
    return value.strip().casefold()


def normalize_workspace(value: str) -> str:
    expanded = Path(value).expanduser().resolve(strict=False)
    return os.path.normcase(os.path.normpath(str(expanded)))
