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
MAX_COUNTER = 1_000_000

RUNTIME_STATUS_PROVENANCE = "hive-runtime-status"
PROVIDER_CATALOG_PROVENANCE = "hive-provider-catalog"
TASK_RUNTIME_PROVENANCE = "hive-agent-task-runtime"
PERMISSION_CONTROL_PROVENANCE = "hive-permission-control-plane"


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


def _parse_state(value: object, *, field: str) -> StatusState:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a runtime status state")
    try:
        return StatusState(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a runtime status state") from exc


def _require_state(value: object, *, field: str) -> StatusState:
    if not isinstance(value, StatusState):
        raise ValueError(f"{field} must be a StatusState")
    return value


def _provenance(value: object, *, field: str, expected: str) -> str:
    text = _bounded_text(value, field=field)
    if text != expected:
        raise ValueError(f"{field} must be {expected}")
    return text


def _counter(value: object, *, field: str, maximum: int = MAX_COUNTER) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > maximum:
        raise ValueError(f"{field} is out of bounds")
    return value


def _nullable_counter(value: object, *, field: str) -> int | None:
    return None if value is None else _counter(value, field=field)


def _record(value: object, *, field: str, keys: set[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    if set(value.keys()) != keys:
        raise ValueError(f"{field} has unexpected fields")
    return value


def _strict_object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


@dataclass(frozen=True)
class StatusSignal:
    state: StatusState
    provenance: str
    detail: str

    def validated(self) -> "StatusSignal":
        _require_state(self.state, field="runtime.state")
        _provenance(self.provenance, field="runtime.provenance", expected=RUNTIME_STATUS_PROVENANCE)
        _bounded_text(self.detail, field="runtime.detail")
        return self


@dataclass(frozen=True)
class ProviderStatus:
    provider_id: str
    model_ids: tuple[str, ...]
    state: StatusState
    provenance: str

    def validated(self) -> "ProviderStatus":
        _bounded_text(self.provider_id, field="provider_id", limit=80)
        _require_state(self.state, field="provider.state")
        _provenance(self.provenance, field="provider.provenance", expected=PROVIDER_CATALOG_PROVENANCE)
        if not isinstance(self.model_ids, tuple):
            raise ValueError("provider model ids must be an immutable tuple")
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
    provenance: str

    def validated(self) -> "TaskStatusSummary":
        _bounded_text(self.task_id, field="task_id", limit=128)
        _bounded_text(self.state, field="task_state", limit=32)
        _provenance(self.provenance, field="task.provenance", expected=TASK_RUNTIME_PROVENANCE)
        node_total = _counter(self.node_total, field="task.node_total", maximum=MAX_TASK_NODES)
        node_succeeded = _counter(self.node_succeeded, field="task.node_succeeded", maximum=MAX_TASK_NODES)
        executions = _counter(self.executions, field="task.executions")
        failures = _counter(self.failures, field="task.failures")
        if node_succeeded > node_total:
            raise ValueError("task node counters out of bounds")
        if failures > executions:
            raise ValueError("task failure count exceeds executions")
        return self


@dataclass(frozen=True)
class PermissionStatusSummary:
    state: StatusState
    policy_epoch: int | None
    active_sessions: int | None
    pending_approvals: int | None
    provenance: str

    def validated(self) -> "PermissionStatusSummary":
        _require_state(self.state, field="permission.state")
        _provenance(
            self.provenance,
            field="permission.provenance",
            expected=PERMISSION_CONTROL_PROVENANCE,
        )
        values = (
            _nullable_counter(self.policy_epoch, field="permission.policy_epoch"),
            _nullable_counter(self.active_sessions, field="permission.active_sessions"),
            _nullable_counter(self.pending_approvals, field="permission.pending_approvals"),
        )
        if self.state in {StatusState.UNKNOWN, StatusState.DISCONNECTED} and any(value is not None for value in values):
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
        if not isinstance(self.runtime, StatusSignal):
            raise ValueError("invalid runtime status signal")
        self.runtime.validated()
        if not isinstance(self.providers, tuple):
            raise ValueError("providers must be an immutable tuple")
        if len(self.providers) > MAX_PROVIDERS:
            raise ValueError("too many providers")
        seen: set[str] = set()
        for provider in self.providers:
            if not isinstance(provider, ProviderStatus):
                raise ValueError("invalid provider status")
            provider.validated()
            key = provider.provider_id.strip().lower()
            if key in seen:
                raise ValueError("duplicate provider id")
            seen.add(key)
        if self.task is not None:
            if not isinstance(self.task, TaskStatusSummary):
                raise ValueError("invalid task status")
            self.task.validated()
        if not isinstance(self.permission, PermissionStatusSummary):
            raise ValueError("invalid permission status")
        self.permission.validated()
        encoded = self._json_unchecked().encode("utf-8")
        if len(encoded) > MAX_STATUS_BYTES:
            raise ValueError("runtime status exceeds byte ceiling")
        return self

    def to_dict_unchecked(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "runtime": {
                "state": self.runtime.state.value,
                "provenance": self.runtime.provenance.strip(),
                "detail": self.runtime.detail.strip(),
            },
            "providers": [
                {
                    "providerId": provider.provider_id.strip().lower(),
                    "modelIds": [model_id.strip() for model_id in provider.model_ids],
                    "state": provider.state.value,
                    "provenance": provider.provenance.strip(),
                }
                for provider in self.providers
            ],
            "task": None
            if self.task is None
            else {
                "taskId": self.task.task_id.strip(),
                "state": self.task.state.strip(),
                "nodeTotal": self.task.node_total,
                "nodeSucceeded": self.task.node_succeeded,
                "executions": self.task.executions,
                "failures": self.task.failures,
                "provenance": self.task.provenance.strip(),
            },
            "permission": {
                "state": self.permission.state.value,
                "policyEpoch": self.permission.policy_epoch,
                "activeSessions": self.permission.active_sessions,
                "pendingApprovals": self.permission.pending_approvals,
                "provenance": self.permission.provenance.strip(),
            },
        }

    def _json_unchecked(self) -> str:
        return json.dumps(self.to_dict_unchecked(), sort_keys=True, separators=(",", ":"))

    def to_json(self) -> str:
        self.validated()
        return self._json_unchecked()

    @classmethod
    def from_dict(cls, value: object) -> "RuntimeStatusSnapshot":
        root = _record(value, field="snapshot", keys={"schema", "runtime", "providers", "task", "permission"})
        if root["schema"] != STATUS_SCHEMA:
            raise ValueError("unsupported runtime status schema")

        runtime_raw = _record(root["runtime"], field="runtime", keys={"state", "provenance", "detail"})
        runtime = StatusSignal(
            _parse_state(runtime_raw["state"], field="runtime.state"),
            _provenance(
                runtime_raw["provenance"],
                field="runtime.provenance",
                expected=RUNTIME_STATUS_PROVENANCE,
            ),
            _bounded_text(runtime_raw["detail"], field="runtime.detail"),
        )

        providers_raw = root["providers"]
        if not isinstance(providers_raw, list) or len(providers_raw) > MAX_PROVIDERS:
            raise ValueError("invalid providers")
        providers: list[ProviderStatus] = []
        for index, raw in enumerate(providers_raw):
            provider_raw = _record(
                raw,
                field=f"providers[{index}]",
                keys={"providerId", "modelIds", "state", "provenance"},
            )
            model_values = provider_raw["modelIds"]
            if not isinstance(model_values, list) or len(model_values) > MAX_MODELS_PER_PROVIDER:
                raise ValueError("invalid provider models")
            models = tuple(_bounded_text(model, field="model_id", limit=128) for model in model_values)
            providers.append(
                ProviderStatus(
                    _bounded_text(provider_raw["providerId"], field="provider_id", limit=80).lower(),
                    models,
                    _parse_state(provider_raw["state"], field="provider.state"),
                    _provenance(
                        provider_raw["provenance"],
                        field="provider.provenance",
                        expected=PROVIDER_CATALOG_PROVENANCE,
                    ),
                ).validated()
            )

        task_raw = root["task"]
        task: TaskStatusSummary | None = None
        if task_raw is not None:
            task_value = _record(
                task_raw,
                field="task",
                keys={"taskId", "state", "nodeTotal", "nodeSucceeded", "executions", "failures", "provenance"},
            )
            task = TaskStatusSummary(
                _bounded_text(task_value["taskId"], field="task_id", limit=128),
                _bounded_text(task_value["state"], field="task_state", limit=32),
                _counter(task_value["nodeTotal"], field="task.node_total", maximum=MAX_TASK_NODES),
                _counter(task_value["nodeSucceeded"], field="task.node_succeeded", maximum=MAX_TASK_NODES),
                _counter(task_value["executions"], field="task.executions"),
                _counter(task_value["failures"], field="task.failures"),
                _provenance(
                    task_value["provenance"],
                    field="task.provenance",
                    expected=TASK_RUNTIME_PROVENANCE,
                ),
            ).validated()

        permission_raw = _record(
            root["permission"],
            field="permission",
            keys={"state", "policyEpoch", "activeSessions", "pendingApprovals", "provenance"},
        )
        permission = PermissionStatusSummary(
            _parse_state(permission_raw["state"], field="permission.state"),
            _nullable_counter(permission_raw["policyEpoch"], field="permission.policy_epoch"),
            _nullable_counter(permission_raw["activeSessions"], field="permission.active_sessions"),
            _nullable_counter(permission_raw["pendingApprovals"], field="permission.pending_approvals"),
            _provenance(
                permission_raw["provenance"],
                field="permission.provenance",
                expected=PERMISSION_CONTROL_PROVENANCE,
            ),
        ).validated()

        return cls(runtime, tuple(providers), task, permission).validated()

    @classmethod
    def from_json(cls, raw: str | bytes) -> "RuntimeStatusSnapshot":
        if isinstance(raw, str):
            data = raw.encode("utf-8")
        elif isinstance(raw, bytes):
            data = raw
        else:
            raise ValueError("runtime status JSON must be text or bytes")
        if not data or len(data) > MAX_STATUS_BYTES:
            raise ValueError("runtime status JSON exceeds byte bounds")
        try:
            decoded = data.decode("utf-8")
            value = json.loads(decoded, object_pairs_hook=_strict_object_pairs)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid runtime status JSON") from exc
        return cls.from_dict(value)


SECRET_KEYS = ("token", "secret", "password", "credential", "api_key", "apikey", "permit", "approval_token")


def reject_secret_like_mapping(values: Mapping[str, object]) -> None:
    """Reject accidental secret-bearing observation keys before reduction."""
    for key in values:
        lowered = str(key).strip().lower()
        if any(marker in lowered for marker in SECRET_KEYS):
            raise ValueError("secret-like observation keys are not allowed")


def summarize_provider_catalog(catalog: ProviderCatalog, provider_ids: Iterable[str]) -> tuple[ProviderStatus, ...]:
    summaries: list[ProviderStatus] = []
    for raw_provider in provider_ids:
        provider_id = _bounded_text(raw_provider, field="provider_id", limit=80).lower()
        models = tuple(_bounded_text(model.model_id, field="model_id", limit=128) for model in catalog.models(provider_id))
        state = StatusState.READY if models else StatusState.UNKNOWN
        summaries.append(ProviderStatus(provider_id, models, state, PROVIDER_CATALOG_PROVENANCE).validated())
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
        provenance=TASK_RUNTIME_PROVENANCE,
    ).validated()


def unobserved_permission(state: StatusState) -> PermissionStatusSummary:
    if not isinstance(state, StatusState) or state not in {StatusState.UNKNOWN, StatusState.DISCONNECTED}:
        raise ValueError("unobserved permission state must be UNKNOWN or DISCONNECTED")
    return PermissionStatusSummary(state, None, None, None, PERMISSION_CONTROL_PROVENANCE).validated()


def disconnected_snapshot() -> RuntimeStatusSnapshot:
    return RuntimeStatusSnapshot(
        runtime=StatusSignal(
            StatusState.DISCONNECTED,
            RUNTIME_STATUS_PROVENANCE,
            "No trusted live runtime observation is connected.",
        ),
        providers=(),
        task=None,
        permission=unobserved_permission(StatusState.DISCONNECTED),
    ).validated()


def degraded_snapshot() -> RuntimeStatusSnapshot:
    """Return a fixed non-secret fail-closed snapshot for rejected observation data."""
    return RuntimeStatusSnapshot(
        runtime=StatusSignal(
            StatusState.DEGRADED,
            RUNTIME_STATUS_PROVENANCE,
            "Runtime observation was rejected by bounded validation.",
        ),
        providers=(),
        task=None,
        permission=PermissionStatusSummary(
            StatusState.DEGRADED,
            None,
            None,
            None,
            PERMISSION_CONTROL_PROVENANCE,
        ),
    ).validated()


def encode_status_fail_closed(snapshot: object) -> str:
    """Encode trusted presentation data or emit a fixed DEGRADED snapshot without leaking errors."""
    try:
        if not isinstance(snapshot, RuntimeStatusSnapshot):
            raise ValueError("invalid runtime status snapshot")
        return snapshot.to_json()
    except (AttributeError, TypeError, UnicodeError, ValueError):
        return degraded_snapshot().to_json()


def decode_status_fail_closed(raw: object) -> RuntimeStatusSnapshot:
    """Decode strict status JSON or return the same fixed DEGRADED presentation state."""
    try:
        if not isinstance(raw, (str, bytes)):
            raise ValueError("invalid runtime status JSON")
        return RuntimeStatusSnapshot.from_json(raw)
    except (AttributeError, TypeError, UnicodeError, ValueError):
        return degraded_snapshot()
