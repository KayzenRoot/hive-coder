from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .control_audit import AuditLog, canonical_json, redact
from .control_policy import ControlPolicy, evaluate_policy
from .control_types import (
    ActionRequest,
    ApprovalChallenge,
    DecisionKind,
    ExecutionPermit,
    PolicyDecision,
    SessionState,
)
from .errors import ApprovalError, AuthorizationDenied, PermitError, SessionStateError

CancelCallback = Callable[[str, str], None]


@dataclass
class _ApprovalRecord:
    challenge: ApprovalChallenge
    consumed: bool = False


@dataclass
class _TokenRecord:
    kind: str
    jti: str
    session_id: str
    request_fingerprint: str
    policy_epoch: int
    expires_at: float
    consumed: bool = False


@dataclass
class _Session:
    session_id: str
    policy: ControlPolicy
    created_at: float
    expires_at: float
    state: SessionState = SessionState.ACTIVE
    policy_epoch: int = 1
    cancel_callbacks: list[CancelCallback] = field(default_factory=list)
    challenges: dict[str, _ApprovalRecord] = field(default_factory=dict)
    approval_tokens: dict[str, _TokenRecord] = field(default_factory=dict)
    permits: dict[str, _TokenRecord] = field(default_factory=dict)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


class PermissionControlPlane:
    """Hive-owned fail-closed authorization state machine.

    It deliberately contains no desktop executor and no Cua tool invocation.
    Trusted UI/orchestrator code may approve challenges; untrusted model/tool
    surfaces must never receive that method as a callable capability.
    """

    def __init__(
        self,
        *,
        clock: Callable[[], float] | None = None,
        nonce_factory: Callable[[], str] | None = None,
        token_key: bytes | None = None,
        max_session_seconds: float = 3600.0,
        max_approval_ttl: float = 60.0,
        max_permit_ttl: float = 5.0,
    ) -> None:
        self._clock = clock or time.time
        self._nonce_factory = nonce_factory or (lambda: secrets.token_urlsafe(24))
        self._token_key = token_key or secrets.token_bytes(32)
        if len(self._token_key) < 16:
            raise ValueError("token_key must be at least 128 bits")
        self.max_session_seconds = float(max_session_seconds)
        self.max_approval_ttl = float(max_approval_ttl)
        self.max_permit_ttl = float(max_permit_ttl)
        if min(self.max_session_seconds, self.max_approval_ttl, self.max_permit_ttl) <= 0:
            raise ValueError("control-plane TTL limits must be positive")
        self._sessions: dict[str, _Session] = {}
        self._issued_ids: set[str] = set()
        self._lock = threading.RLock()
        self._global_emergency_stop = False
        self._global_epoch = 1
        self.audit = AuditLog(self._clock)

    @property
    def global_emergency_stop_active(self) -> bool:
        return self._global_emergency_stop

    def create_session(
        self,
        policy: ControlPolicy,
        *,
        duration_seconds: float,
        cancel_callbacks: tuple[CancelCallback, ...] = (),
    ) -> str:
        duration = float(duration_seconds)
        if duration <= 0 or duration > self.max_session_seconds:
            raise SessionStateError("session duration outside configured bounds")
        with self._lock:
            if self._global_emergency_stop:
                raise SessionStateError("global emergency stop is active")
            session_id = self._unique_nonce("session")
            now = self._now()
            session = _Session(
                session_id=session_id,
                policy=policy,
                created_at=now,
                expires_at=now + duration,
                cancel_callbacks=list(cancel_callbacks),
            )
            self._sessions[session_id] = session
            self.audit.append(
                "control.session_created",
                session_id=session_id,
                details={"expires_at": session.expires_at, "policy_epoch": session.policy_epoch},
            )
            return session_id

    def register_cancel_callback(self, session_id: str, callback: CancelCallback) -> None:
        with self._lock:
            session = self._require_active_session(session_id)
            session.cancel_callbacks.append(callback)
            self.audit.append("control.cancel_callback_registered", session_id=session_id)

    def evaluate(self, request: ActionRequest) -> PolicyDecision:
        with self._lock:
            session = self._require_active_session(request.session_id)
            try:
                fingerprint = self.request_fingerprint(request)
                decision = evaluate_policy(
                    session.policy,
                    request,
                    fingerprint=fingerprint,
                    policy_epoch=session.policy_epoch,
                )
            except (OSError, TypeError, ValueError):
                fingerprint = hashlib.sha256(
                    canonical_json(
                        {
                            "session_id": str(request.session_id),
                            "capability": self._capability_string(request.capability),
                            "action": str(request.action),
                            "invalid_request": True,
                        }
                    ).encode("utf-8")
                ).hexdigest()
                decision = PolicyDecision(
                    DecisionKind.DENY,
                    "invalid_request_shape",
                    None,
                    fingerprint,
                    session.policy_epoch,
                )
            self.audit.append(
                "control.policy_decision",
                session_id=session.session_id,
                details={
                    "decision": decision.kind.value,
                    "reason": decision.reason,
                    "risk": None if decision.risk is None else decision.risk.value,
                    "capability": self._capability_string(request.capability),
                    "action": str(request.action),
                    "request_fingerprint": fingerprint,
                    "policy_epoch": session.policy_epoch,
                    "untrusted_context_sha256": self._hash_untrusted_context(request.untrusted_context),
                },
            )
            return decision

    def create_approval_challenge(self, request: ActionRequest, *, ttl_seconds: float | None = None) -> ApprovalChallenge:
        with self._lock:
            session = self._require_active_session(request.session_id)
            decision = self.evaluate(request)
            if decision.kind is DecisionKind.DENY:
                raise AuthorizationDenied(decision.reason)
            if decision.kind is not DecisionKind.REQUIRE_APPROVAL:
                raise ApprovalError("policy does not require approval for this request")
            ttl = self._bounded_ttl(ttl_seconds, self.max_approval_ttl, "approval")
            challenge_id = self._unique_nonce("challenge")
            normalized_arguments = self._normalize_json_value(request.arguments)
            arguments_sha256 = hashlib.sha256(
                canonical_json(normalized_arguments).encode("utf-8")
            ).hexdigest()
            challenge = ApprovalChallenge(
                challenge_id=challenge_id,
                session_id=session.session_id,
                request_fingerprint=decision.request_fingerprint,
                policy_epoch=session.policy_epoch,
                expires_at=self._now() + ttl,
                capability=self._capability_string(request.capability),
                action=str(request.action),
                target=request.target.canonical(),
                arguments_sha256=arguments_sha256,
                display_arguments=redact(normalized_arguments),
            )
            session.challenges[challenge_id] = _ApprovalRecord(challenge)
            self.audit.append(
                "control.approval_challenge_created",
                session_id=session.session_id,
                details={
                    "challenge_id": challenge_id,
                    "request_fingerprint": challenge.request_fingerprint,
                    "expires_at": challenge.expires_at,
                    "policy_epoch": session.policy_epoch,
                    "capability": challenge.capability,
                    "action": challenge.action,
                    "target": challenge.target,
                    "arguments_sha256": challenge.arguments_sha256,
                    "display_arguments": challenge.display_arguments,
                },
            )
            return challenge

    def approve_challenge_from_trusted_ui(self, challenge_id: str, *, session_id: str) -> str:
        with self._lock:
            session = self._require_active_session(session_id)
            record = session.challenges.get(challenge_id)
            if record is None:
                raise ApprovalError("unknown approval challenge")
            challenge = record.challenge
            if record.consumed:
                raise ApprovalError("approval challenge already consumed")
            if challenge.policy_epoch != session.policy_epoch:
                raise ApprovalError("approval challenge is stale after policy change")
            if self._now() >= challenge.expires_at:
                raise ApprovalError("approval challenge expired")
            record.consumed = True
            jti = self._unique_nonce("approval")
            payload = {
                "kind": "approval",
                "jti": jti,
                "session_id": session.session_id,
                "request_fingerprint": challenge.request_fingerprint,
                "policy_epoch": session.policy_epoch,
                "exp": challenge.expires_at,
                "global_epoch": self._global_epoch,
            }
            token = self._sign(payload)
            session.approval_tokens[jti] = _TokenRecord(
                "approval",
                jti,
                session.session_id,
                challenge.request_fingerprint,
                session.policy_epoch,
                challenge.expires_at,
            )
            self.audit.append(
                "control.approval_granted",
                session_id=session.session_id,
                details={
                    "approval_jti": jti,
                    "challenge_id": challenge_id,
                    "request_fingerprint": challenge.request_fingerprint,
                    "expires_at": challenge.expires_at,
                    "policy_epoch": session.policy_epoch,
                },
            )
            return token

    def authorize(self, request: ActionRequest, *, approval_token: str | None = None) -> ExecutionPermit:
        with self._lock:
            session = self._require_active_session(request.session_id)
            decision = self.evaluate(request)
            if decision.kind is DecisionKind.DENY:
                raise AuthorizationDenied(decision.reason)
            if decision.kind is DecisionKind.REQUIRE_APPROVAL:
                if approval_token is None:
                    raise AuthorizationDenied("approval_required")
                approval = self._verify_token(approval_token, expected_kind="approval", session=session)
                if approval.request_fingerprint != decision.request_fingerprint:
                    raise ApprovalError("approval request fingerprint mismatch")
                if approval.policy_epoch != session.policy_epoch:
                    raise ApprovalError("approval policy epoch mismatch")
                if approval.consumed:
                    raise ApprovalError("approval token already used")
                approval.consumed = True
                self.audit.append(
                    "control.approval_consumed",
                    session_id=session.session_id,
                    details={"approval_jti": approval.jti, "request_fingerprint": decision.request_fingerprint},
                )
            elif approval_token is not None:
                raise ApprovalError("approval token supplied for approval-free action")

            ttl = min(self.max_permit_ttl, max(0.001, session.expires_at - self._now()))
            jti = self._unique_nonce("permit")
            expires_at = self._now() + ttl
            payload = {
                "kind": "permit",
                "jti": jti,
                "session_id": session.session_id,
                "request_fingerprint": decision.request_fingerprint,
                "policy_epoch": session.policy_epoch,
                "exp": expires_at,
                "global_epoch": self._global_epoch,
            }
            token = self._sign(payload)
            record = _TokenRecord(
                "permit",
                jti,
                session.session_id,
                decision.request_fingerprint,
                session.policy_epoch,
                expires_at,
            )
            session.permits[jti] = record
            permit = ExecutionPermit(token, session.session_id, decision.request_fingerprint, session.policy_epoch, expires_at)
            self.audit.append(
                "control.execution_permit_issued",
                session_id=session.session_id,
                details={
                    "permit_jti": jti,
                    "request_fingerprint": decision.request_fingerprint,
                    "expires_at": expires_at,
                    "policy_epoch": session.policy_epoch,
                },
            )
            return permit

    def consume_execution_permit(self, permit_token: str, request: ActionRequest) -> None:
        with self._lock:
            session = self._require_active_session(request.session_id)
            expected_fingerprint = self.request_fingerprint(request)
            permit = self._verify_token(permit_token, expected_kind="permit", session=session)
            if permit.request_fingerprint != expected_fingerprint:
                raise PermitError("permit request fingerprint mismatch")
            if permit.policy_epoch != session.policy_epoch:
                raise PermitError("permit policy epoch mismatch")
            if permit.consumed:
                raise PermitError("permit already consumed")
            permit.consumed = True
            self.audit.append(
                "control.execution_permit_consumed",
                session_id=session.session_id,
                details={"permit_jti": permit.jti, "request_fingerprint": expected_fingerprint},
            )

    def update_policy(self, session_id: str, policy: ControlPolicy) -> None:
        with self._lock:
            session = self._require_active_session(session_id)
            session.policy = policy
            session.policy_epoch += 1
            self._invalidate_ephemeral(session)
            self.audit.append(
                "control.policy_updated",
                session_id=session_id,
                details={"policy_epoch": session.policy_epoch},
            )

    def cancel_session(self, session_id: str, *, reason: str = "cancelled") -> None:
        self._transition_session(session_id, SessionState.CANCELLED, reason)

    def user_takeover(self, session_id: str, *, reason: str = "user_takeover") -> None:
        self._transition_session(session_id, SessionState.USER_TAKEOVER, reason)

    def emergency_stop(self, *, session_id: str | None = None, reason: str = "emergency_stop") -> None:
        with self._lock:
            if session_id is not None:
                self._transition_session_locked(session_id, SessionState.EMERGENCY_STOPPED, reason)
                return
            self._global_emergency_stop = True
            self._global_epoch += 1
            affected = [sid for sid, session in self._sessions.items() if session.state is SessionState.ACTIVE]
            for sid in affected:
                self._transition_session_locked(sid, SessionState.EMERGENCY_STOPPED, reason)
            self.audit.append(
                "control.global_emergency_stop",
                details={"reason": reason, "affected_sessions": len(affected), "global_epoch": self._global_epoch},
            )

    def reset_global_emergency_stop(self) -> None:
        with self._lock:
            if not self._global_emergency_stop:
                return
            self._global_emergency_stop = False
            self._global_epoch += 1
            self.audit.append("control.global_emergency_stop_reset", details={"global_epoch": self._global_epoch})

    def session_state(self, session_id: str) -> SessionState:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionStateError("unknown control session")
            self._expire_if_needed(session)
            return session.state

    def request_fingerprint(self, request: ActionRequest) -> str:
        capability = self._capability_string(request.capability)
        payload = {
            "session_id": str(request.session_id),
            "capability": capability,
            "action": str(request.action).strip(),
            "target": request.target.canonical(),
            "arguments": self._normalize_json_value(request.arguments),
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def _transition_session(self, session_id: str, state: SessionState, reason: str) -> None:
        with self._lock:
            self._transition_session_locked(session_id, state, reason)

    def _transition_session_locked(self, session_id: str, state: SessionState, reason: str) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionStateError("unknown control session")
        if session.state is not SessionState.ACTIVE:
            return
        session.state = state
        session.policy_epoch += 1
        self._invalidate_ephemeral(session)
        self.audit.append(
            "control.session_state_changed",
            session_id=session_id,
            details={"state": state.value, "reason": str(reason), "policy_epoch": session.policy_epoch},
        )
        callbacks = tuple(session.cancel_callbacks)
        for callback in callbacks:
            try:
                callback(session_id, str(reason))
            except Exception as exc:
                self.audit.append(
                    "control.cancel_callback_failed",
                    session_id=session_id,
                    details={"error_type": type(exc).__name__},
                )

    def _invalidate_ephemeral(self, session: _Session) -> None:
        session.challenges.clear()
        session.approval_tokens.clear()
        session.permits.clear()

    def _require_active_session(self, session_id: str) -> _Session:
        if self._global_emergency_stop:
            raise SessionStateError("global emergency stop is active")
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionStateError("unknown control session")
        self._expire_if_needed(session)
        if session.state is not SessionState.ACTIVE:
            raise SessionStateError(f"control session is not active: {session.state.value}")
        return session

    def _expire_if_needed(self, session: _Session) -> None:
        if session.state is SessionState.ACTIVE and self._now() >= session.expires_at:
            self._transition_session_locked(session.session_id, SessionState.EXPIRED, "session_expired")

    def _verify_token(self, token: str, *, expected_kind: str, session: _Session) -> _TokenRecord:
        error_type = PermitError if expected_kind == "permit" else ApprovalError
        try:
            encoded, signature = token.split(".", 1)
            payload_bytes = _unb64(encoded)
            supplied_sig = _unb64(signature)
        except Exception as exc:
            raise error_type("malformed signed token") from exc
        expected_sig = hmac.new(self._token_key, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_sig, expected_sig):
            raise error_type("invalid signed token")
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise error_type("invalid signed token payload") from exc
        if payload.get("kind") != expected_kind:
            raise error_type("signed token kind mismatch")
        if payload.get("session_id") != session.session_id:
            raise error_type("signed token session mismatch")
        if payload.get("global_epoch") != self._global_epoch:
            raise error_type("signed token invalidated by emergency epoch")
        if payload.get("policy_epoch") != session.policy_epoch:
            raise error_type("signed token invalidated by policy epoch")
        exp = payload.get("exp")
        if not isinstance(exp, (int, float)) or self._now() >= float(exp):
            raise error_type("signed token expired")
        jti = payload.get("jti")
        if not isinstance(jti, str) or not jti:
            raise error_type("signed token missing jti")
        store = session.approval_tokens if expected_kind == "approval" else session.permits
        record = store.get(jti)
        if record is None:
            raise error_type("signed token is unknown or revoked")
        return record

    def _sign(self, payload: Mapping[str, Any]) -> str:
        encoded = canonical_json(payload).encode("utf-8")
        signature = hmac.new(self._token_key, encoded, hashlib.sha256).digest()
        return f"{_b64(encoded)}.{_b64(signature)}"

    def _unique_nonce(self, prefix: str) -> str:
        for _ in range(10):
            value = f"{prefix}_{self._nonce_factory()}"
            if value not in self._issued_ids:
                self._issued_ids.add(value)
                return value
        raise SessionStateError("nonce factory produced repeated identifiers")

    def _bounded_ttl(self, value: float | None, maximum: float, label: str) -> float:
        ttl = maximum if value is None else float(value)
        if ttl <= 0 or ttl > maximum:
            raise ApprovalError(f"{label} ttl outside configured bounds")
        return ttl

    def _now(self) -> float:
        value = float(self._clock())
        if value != value or value in (float("inf"), float("-inf")):
            raise SessionStateError("clock returned a non-finite value")
        return value

    @staticmethod
    def _capability_string(capability: Any) -> str:
        value = getattr(capability, "value", capability)
        return str(value)

    @staticmethod
    def _hash_untrusted_context(value: Mapping[str, Any]) -> str:
        normalized = PermissionControlPlane._normalize_json_value(value)
        return hashlib.sha256(canonical_json(normalized).encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_json_value(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): PermissionControlPlane._normalize_json_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
        if isinstance(value, (list, tuple)):
            return [PermissionControlPlane._normalize_json_value(item) for item in value]
        if value is None or isinstance(value, (bool, int, float, str)):
            if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
                raise ValueError("non-finite action argument")
            return value
        raise ValueError(f"unsupported action argument type: {type(value).__name__}")
