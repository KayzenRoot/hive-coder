from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable

from .control_types import ActionRequest, CAPABILITY_SPECS, Capability, DecisionKind, PolicyDecision, normalize_application, normalize_workspace


@dataclass(frozen=True)
class CapabilityRule:
    capability: Capability
    allowed_actions: frozenset[str]
    requires_approval: bool = True
    allowed_applications: frozenset[str] = field(default_factory=frozenset)
    allowed_window_ids: frozenset[str] = field(default_factory=frozenset)
    allowed_workspace_roots: tuple[str, ...] = ()
    allowed_resources: frozenset[str] = field(default_factory=frozenset)
    denied_actions: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def build(
        cls,
        capability: Capability,
        *,
        allowed_actions: Iterable[str],
        requires_approval: bool = True,
        allowed_applications: Iterable[str] = (),
        allowed_window_ids: Iterable[str] = (),
        allowed_workspace_roots: Iterable[str] = (),
        allowed_resources: Iterable[str] = (),
        denied_actions: Iterable[str] = (),
    ) -> "CapabilityRule":
        return cls(
            capability=capability,
            allowed_actions=frozenset(str(item).strip() for item in allowed_actions if str(item).strip()),
            requires_approval=requires_approval,
            allowed_applications=frozenset(normalize_application(str(item)) for item in allowed_applications if str(item).strip()),
            allowed_window_ids=frozenset(str(item).strip() for item in allowed_window_ids if str(item).strip()),
            allowed_workspace_roots=tuple(normalize_workspace(str(item)) for item in allowed_workspace_roots if str(item).strip()),
            allowed_resources=frozenset(str(item).strip() for item in allowed_resources if str(item).strip()),
            denied_actions=frozenset(str(item).strip() for item in denied_actions if str(item).strip()),
        )


@dataclass(frozen=True)
class ControlPolicy:
    rules: tuple[CapabilityRule, ...]
    denied_capabilities: frozenset[Capability] = field(default_factory=frozenset)
    denied_applications: frozenset[str] = field(default_factory=frozenset)
    denied_window_ids: frozenset[str] = field(default_factory=frozenset)
    denied_workspace_roots: tuple[str, ...] = ()
    denied_resources: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def build(
        cls,
        rules: Iterable[CapabilityRule],
        *,
        denied_capabilities: Iterable[Capability] = (),
        denied_applications: Iterable[str] = (),
        denied_window_ids: Iterable[str] = (),
        denied_workspace_roots: Iterable[str] = (),
        denied_resources: Iterable[str] = (),
    ) -> "ControlPolicy":
        materialized = tuple(rules)
        seen: set[Capability] = set()
        for rule in materialized:
            if rule.capability in seen:
                raise ValueError(f"duplicate capability rule: {rule.capability.value}")
            seen.add(rule.capability)
            if not rule.allowed_actions:
                raise ValueError(f"capability rule has no allowed actions: {rule.capability.value}")
        return cls(
            rules=materialized,
            denied_capabilities=frozenset(denied_capabilities),
            denied_applications=frozenset(normalize_application(str(item)) for item in denied_applications if str(item).strip()),
            denied_window_ids=frozenset(str(item).strip() for item in denied_window_ids if str(item).strip()),
            denied_workspace_roots=tuple(normalize_workspace(str(item)) for item in denied_workspace_roots if str(item).strip()),
            denied_resources=frozenset(str(item).strip() for item in denied_resources if str(item).strip()),
        )

    def rule_for(self, capability: Capability) -> CapabilityRule | None:
        for rule in self.rules:
            if rule.capability == capability:
                return rule
        return None


def workspace_is_within(path: str, roots: tuple[str, ...]) -> bool:
    normalized = normalize_workspace(path)
    for root in roots:
        try:
            if os.path.commonpath([normalized, root]) == root:
                return True
        except ValueError:
            continue
    return False


def evaluate_policy(policy: ControlPolicy, request: ActionRequest, *, fingerprint: str, policy_epoch: int) -> PolicyDecision:
    capability = request.capability
    if not isinstance(capability, Capability):
        try:
            capability = Capability(str(capability))
        except ValueError:
            return PolicyDecision(DecisionKind.DENY, "unknown_capability", None, fingerprint, policy_epoch)
    spec = CAPABILITY_SPECS.get(capability)
    if spec is None:
        return PolicyDecision(DecisionKind.DENY, "unknown_capability", None, fingerprint, policy_epoch)
    if capability in policy.denied_capabilities:
        return PolicyDecision(DecisionKind.DENY, "capability_explicitly_denied", spec.risk, fingerprint, policy_epoch)

    rule = policy.rule_for(capability)
    if rule is None:
        return PolicyDecision(DecisionKind.DENY, "capability_not_allowlisted", spec.risk, fingerprint, policy_epoch)

    action = str(request.action).strip()
    if not action:
        return PolicyDecision(DecisionKind.DENY, "missing_action", spec.risk, fingerprint, policy_epoch)
    if action in rule.denied_actions:
        return PolicyDecision(DecisionKind.DENY, "action_explicitly_denied", spec.risk, fingerprint, policy_epoch)
    if action not in rule.allowed_actions:
        return PolicyDecision(DecisionKind.DENY, "action_not_allowlisted", spec.risk, fingerprint, policy_epoch)

    target = request.target.canonical()
    for required in spec.required_target_fields:
        if not target.get(required):
            return PolicyDecision(DecisionKind.DENY, f"missing_required_target:{required}", spec.risk, fingerprint, policy_epoch)

    app = target["application"]
    if app is not None:
        if app in policy.denied_applications:
            return PolicyDecision(DecisionKind.DENY, "application_explicitly_denied", spec.risk, fingerprint, policy_epoch)
        if app not in rule.allowed_applications:
            return PolicyDecision(DecisionKind.DENY, "application_not_allowlisted", spec.risk, fingerprint, policy_epoch)
    elif rule.allowed_applications or "application" in spec.required_target_fields:
        return PolicyDecision(DecisionKind.DENY, "application_scope_unknown", spec.risk, fingerprint, policy_epoch)

    window_id = target["window_id"]
    if window_id is not None:
        if window_id in policy.denied_window_ids:
            return PolicyDecision(DecisionKind.DENY, "window_explicitly_denied", spec.risk, fingerprint, policy_epoch)
        if window_id not in rule.allowed_window_ids:
            return PolicyDecision(DecisionKind.DENY, "window_not_allowlisted", spec.risk, fingerprint, policy_epoch)
    elif rule.allowed_window_ids or "window_id" in spec.required_target_fields:
        return PolicyDecision(DecisionKind.DENY, "window_scope_unknown", spec.risk, fingerprint, policy_epoch)

    workspace = target["workspace"]
    if workspace is not None:
        if workspace_is_within(workspace, policy.denied_workspace_roots):
            return PolicyDecision(DecisionKind.DENY, "workspace_explicitly_denied", spec.risk, fingerprint, policy_epoch)
        if not workspace_is_within(workspace, rule.allowed_workspace_roots):
            return PolicyDecision(DecisionKind.DENY, "workspace_not_allowlisted", spec.risk, fingerprint, policy_epoch)
    elif rule.allowed_workspace_roots or "workspace" in spec.required_target_fields:
        return PolicyDecision(DecisionKind.DENY, "workspace_scope_unknown", spec.risk, fingerprint, policy_epoch)

    resource = target["resource"]
    if resource is not None:
        if resource in policy.denied_resources:
            return PolicyDecision(DecisionKind.DENY, "resource_explicitly_denied", spec.risk, fingerprint, policy_epoch)
        if resource not in rule.allowed_resources:
            return PolicyDecision(DecisionKind.DENY, "resource_not_allowlisted", spec.risk, fingerprint, policy_epoch)
    elif rule.allowed_resources or "resource" in spec.required_target_fields:
        return PolicyDecision(DecisionKind.DENY, "resource_scope_unknown", spec.risk, fingerprint, policy_epoch)

    kind = DecisionKind.REQUIRE_APPROVAL if (spec.mandatory_approval or rule.requires_approval) else DecisionKind.ALLOW
    return PolicyDecision(kind, "policy_allow", spec.risk, fingerprint, policy_epoch)
