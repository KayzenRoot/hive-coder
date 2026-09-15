from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Mapping

SENSITIVE_KEY_MARKERS = (
    "token",
    "secret",
    "password",
    "passwd",
    "authorization",
    "api_key",
    "api-key",
    "apikey",
    "cookie",
    "session_key",
    "private_key",
)
_SECRET_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}", re.IGNORECASE),
    re.compile(r"\bghp_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{8,}\b", re.IGNORECASE),
    re.compile(r"\bAKIA[A-Z0-9]{12,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"(?i)\b(?:api[_-]?key|token|secret|password|passwd)\s*[:=]\s*[^\s,;]+"),
)


def redact(value: Any, *, key: str | None = None) -> Any:
    if key is not None and any(marker in key.casefold() for marker in SENSITIVE_KEY_MARKERS):
        return "<redacted>"
    if isinstance(value, Mapping):
        return {str(k): redact(v, key=str(k)) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, str):
        result = value
        for pattern in _SECRET_PATTERNS:
            result = pattern.sub("<redacted>", result)
        return result
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return f"<redacted:{type(value).__name__}>"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    timestamp: float
    event_type: str
    session_id: str | None
    details_json: str
    previous_digest: str
    digest: str

    @property
    def details(self) -> Mapping[str, Any]:
        return json.loads(self.details_json)


class AuditLog:
    """Append-only event sequence. PermissionControlPlane keeps its instance private."""

    def __init__(self, clock: Callable[[], float]) -> None:
        self._clock = clock
        self._events: list[AuditEvent] = []

    def append(self, event_type: str, *, session_id: str | None = None, details: Mapping[str, Any] | None = None) -> AuditEvent:
        sequence = len(self._events) + 1
        timestamp = float(self._clock())
        if timestamp != timestamp or timestamp in (float("inf"), float("-inf")):
            raise ValueError("audit clock returned a non-finite value")
        clean_details = redact(dict(details or {}))
        previous = self._events[-1].digest if self._events else "0" * 64
        payload = {
            "sequence": sequence,
            "timestamp": timestamp,
            "event_type": str(event_type),
            "session_id": session_id,
            "details": clean_details,
            "previous_digest": previous,
        }
        digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        event = AuditEvent(
            sequence,
            timestamp,
            str(event_type),
            session_id,
            canonical_json(clean_details),
            previous,
            digest,
        )
        self._events.append(event)
        return event

    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def verify_chain(self) -> bool:
        previous = "0" * 64
        for index, event in enumerate(self._events, start=1):
            payload = {
                "sequence": index,
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "session_id": event.session_id,
                "details": event.details,
                "previous_digest": previous,
            }
            expected = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
            if event.sequence != index or event.previous_digest != previous or event.digest != expected:
                return False
            previous = event.digest
        return True
