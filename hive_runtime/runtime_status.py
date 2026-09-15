"""Bounded non-authoritative runtime observability for Hive Coder.

This module intentionally exports presentation state only. It cannot mint permits,
approve requests, execute providers, run prompts, mutate tasks, or expose credentials.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from .agent_tasks import TaskSnapshot
from .providers import ProviderCatalog

STATUS_SCHEMA = "hive-runtime-status-v1"
MAX_STATUS_BYTES = 32_768
MAX_TEXT = 160
MAX_PROVIDERS = 16
MAX_MODELS_PER_PROVIDER = 64
MAX_TASK_NODES = 256


class StatusState(str, Enum):
    READY = "READY"
    UNKNOWN = "UNKNOWN"
    DISCONNECTED = "DISCONNECTED"
    DEGRADED = "DEGRADED"


def _bounded_text(value: object, *, field: str, limit: int = MAX_TEXT) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    text = value.strip()
    if not text or len(text) > limit:
        raise ValueError(f"{field} must contain 1..{limit} characters")
    return text


@dataclass(frozen=True)
class StatusSignal:
    state: StatusState
    provenance: str
    detail: str

    def validated(self) -> "StatusSignal":
        _bounded_text(self.provenance, field="provenance")
        _bounded_text(self.detail, field="detail")
        return self


@dataclass(frozen=True)
class ProviderStatus:
    provider_id: str
    model_ids: tuple[str, ...]
    state: StatusState = StatusState.READY

    def validated(self) -> "ProviderStatus":
        _bounded_text(self.provider_id, field="provider_id", limit=80)
        if len(self.model_ids) > MAX_MODELS_PER_PROVIDER:
            raise ValueError("too many provider models")
        seen: set[str] = set()
        for model_id in self.model_ids:
            normalized = _bounded_text(model_id, field="model_id", limit=128)
            if normalized in seen:
                raise ValueError("duplicate provider model id")
            seen.add(normalized)
        if self.state is StatusState.READY and not self.model_ids:
            raise ValueError("READY provider requires at least one observed model")
        return self


@dataclass(frozen=True)
class TaskStatusSummary:
    task_id: str
    state: str
    node_total: int
    node_succeeded: int
    executions: int
    failures: int

    def validated(self) -> "TaskStatusSummary":
        _bounded_text(self.task_id, field="task_id", limit=128)
        _bounded_text(self.state, field="task_state", limit=32)
        counters = (self.node_total, self.node_succeeded, self.executions, self.failures)
        if any(not isinstance(value, int) or value < 0 for value in counters):
            raise ValueError("task counters must be non-negative integers")
        if self.node_total > MAX_TASK_NODES or self.node_succeeded > self.node_total:
            raise ValueError("task node counters out of bounds")
        if self.failures > self.executions:
            raise ValueError("task failure count exceeds executions")
        return self


@dataclass(frozen=True)
class PermissionStatusSummary:
    state: StatusState
    policy_epoch: int | None
    active_sessions: int | None
    pending_approvals: int | None

    def validated(self) -> "PermissionStatusSummary":
        for name, value in (
            ("policy_epoch", self.policy_epoch),
            ("active_sessions", self.active_sessions),
            ("pending_approvals", self.pending_approvals),
        ):
            if value is not None and (not isinstance(value, int) or value < 0 or value > 1_000_000):
                raise ValueError(f"{name} is out of bounds")
        if self.state in {StatusState.UNKNOWN, StatusState.DISCONNECTED} and any(
            value is not None for value in (self.policy_epoch, self.active_sessions, self.pending_approvals)
        ):
            raise ValueError("unknown/disconnected permission state cannot carry authoritative-looking counters")
        return self


@dataclass(frozen=True)
class RuntimeStatusSnapshot:
    runtime: StatusSignal
    providers: tuple[ProviderStatus, ...]
    task: TaskStatusSummary | None
    permission: PermissionStatusSummary
    schema: str = STATUS_SCHEMA

    def validated(self) -> "RuntimeStatusSnapshot":
        if self.schema != STATUS_SCHEMA:
            raise ValueError("unsupported runtime status schema")
        self.runtime.validated()
        if len(self.providers) > MAX_PROVIDERS:
            raise ValueError("too many providers")
        seen: set[str] = set()
        for provider in self.providers:
            provider.validated()
            key = provider.provider_id.strip().lower()
            if key in seen:
                raise ValueError("duplicate provider id")
            seen.add(key)
        if self.task is not None:
            self.task.validated()
        self.permission.validated()
        encoded = json.dumps(self.to_dict_unchecked(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > MAX_STATUS_BYTES:
            raise ValueError("runtime status exceeds byte ceiling")
        return self

    def to_dict_unchecked(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "runtime": {
                "state": self.runtime.state.value,
                "provenance": self.runtime.provenance,
                "detail": self.runtime.detail,
            },
            "providers": [
                {
                    "providerId": provider.provider_id,
                    "modelIds": list(provider.model_ids),
                    "state": provider.state.value,
                }
                for provider in self.providers
            ],
            "task": None
            if self.task is None
            else {
                "taskId": self.task.task_id,
                "state": self.task.state,
                "nodeTotal": self.task.node_total,
                "nodeSucceeded": self.task.node_succeeded,
                "executions": self.task.executions,
                "failures": self.task.failures,
            },
            "permission": {
                "state": self.permission.state.value,
                "policyEpoch": self.permission.policy_epoch,
                "activeSessions": self.permission.active_sessions,
                "pendingApprovals": self.permission.pending_approvals,
            },
        }

    def to_json(self) -> str:
        self.validated()
        return json.dumps(self.to_dict_unchecked(), sort_keys=True, separators=(",", ":"))


SECRET_KEYS = ("token", "secret", "password", "credential", "api_key", "apikey", "permit", "approval_token")


def reject_secret_like_mapping(values: Mapping[str, object]) -> None:
    """Reject accidental secret-bearing observation input before reduction."""
    for key in values:
        lowered = str(key).strip().lower()
        if any(marker in lowered for marker in SECRET_KEYS):
            raise ValueError("secret-like observation keys are not allowed")


def summarize_provider_catalog(catalog: ProviderCatalog, provider_ids: Iterable[str]) -> tuple[ProviderStatus, ...]:
    summaries: list[ProviderStatus] = []
    for raw_provider in provider_ids:
        provider_id = _bounded_text(raw_provider, field="provider_id", limit=80).lower()
        models = tuple(model.model_id for model in catalog.models(provider_id))
        state = StatusState.READY if models else StatusState.UNKNOWN
        summaries.append(ProviderStatus(provider_id, models, state).validated())
        if len(summaries) > MAX_PROVIDERS:
            raise ValueError("too many providers")
    return tuple(summaries)


def summarize_task(snapshot: TaskSnapshot) -> TaskStatusSummary:
    total = len(snapshot.node_status)
    succeeded = sum(1 for _, state in snapshot.node_status if state.value == "succeeded")
    return TaskStatusSummary(
        task_id=snapshot.task_id,
        state=snapshot.status.value,
        node_total=total,
        node_succeeded=succeeded,
        executions=snapshot.executions,
        failures=snapshot.failures,
    ).validated()


def disconnected_snapshot() -> RuntimeStatusSnapshot:
    return RuntimeStatusSnapshot(
        runtime=StatusSignal(StatusState.DISCONNECTED, "hive-runtime-status", "No trusted live runtime observation is connected."),
        providers=(),
        task=None,
        permission=PermissionStatusSummary(StatusState.DISCONNECTED, None, None, None),
    ).validated()
