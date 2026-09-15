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

from .control_audit import AuditEvent, AuditLog, canonical_json, redact
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
_MAX_SIGNED_TOKEN_CHARS = 4096


@dataclass(frozen=True)
class _RequestSnapshot:
    capability: str
    action: str
    target: Mapping[str, str | None]
    arguments: Any
    fingerprint: str


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
    global_epoch: int
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
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)


class PermissionControlPlane:
    """Hive-owned fail-closed authorization state machine.

    No desktop executor or Cua tool invocation exists here. The trusted host/UI
    boundary may resolve approval challenges; model/tool surfaces must not be
    given that operation as a callable capability.
    """

    def __init__(
        self,
        *,
        security_clock: Callable[[], float] | None = None,
        audit_clock: Callable[[], float] | None = None,
        nonce_factory: Callable[[], str] | None = None,
        token_key: bytes | None = None,
        max_session_seconds: float = 3600.0,
        max_approval_ttl: float = 60.0,
        max_permit_ttl: float = 5.0,
    ) -> None:
        self._security_clock = security_clock or time.monotonic
        self._nonce_factory = nonce_factory or (lambda: secrets.token_urlsafe(24))
        self._token_key = token_key or secrets.token_bytes(32)
        if len(self._token_key) < 32:
            raise ValueError("token_key must be at least 256 bits")
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
        self._audit = AuditLog(audit_clock or time.time)

    @property
    def global_emergency_stop_active(self) -> bool:
        with self._lock:
            return self._global_emergency_stop

    def audit_events(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return self._audit.events()

    def verify_audit_chain(self) -> bool:
        with self._lock:
            return self._audit.verify_chain()

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
            now = self._security_now()
            session = _Session(
                session_id=session_id,
                policy=policy,
                created_at=now,
                expires_at=now + duration,
                cancel_callbacks=list(cancel_callbacks),
            )
            self._sessions[session_id] = session
            self._audit.append(
                "control.session_created",
                session_id=session_id,
                details={"duration_seconds": duration, "policy_epoch": session.policy_epoch},
            )
            return session_id

    def register_cancel_callback(self, session_id: str, callback: CancelCallback) -> None:
        with self._lock:
            session = self._require_active_session(session_id)
            session.cancel_callbacks.append(callback)
            self._audit.append("control.cancel_callback_registered", session_id=session_id)

    def evaluate(self, request: ActionRequest) -> PolicyDecision:
        with self._lock:
            session = self._require_active_session(request.session_id)
            decision, _snapshot = self._evaluate_locked(session, request)
            return decision

    def create_approval_challenge(self, request: ActionRequest, *, ttl_seconds: float | None = None) -> ApprovalChallenge:
        with self._lock:
            session = self._require_active_session(request.session_id)
            decision, snapshot = self._evaluate_locked(session, request)
            if decision.kind is DecisionKind.DENY or snapshot is None:
                raise AuthorizationDenied(decision.reason)
            if decision.kind is not DecisionKind.REQUIRE_APPROVAL:
                raise ApprovalError("policy does not require approval for this request")
            ttl = self._bounded_ttl(ttl_seconds, self.max_approval_ttl, "approval")
            challenge_id = self._unique_nonce("challenge")
            arguments_json = canonical_json(snapshot.arguments)
            arguments_sha256 = hashlib.sha256(arguments_json.encode("utf-8")).hexdigest()
            target_json = canonical_json(dict(snapshot.target))
            display_arguments_json = canonical_json(redact(snapshot.arguments))
            challenge = ApprovalChallenge(
                challenge_id=challenge_id,
                session_id=session.session_id,
                request_fingerprint=decision.request_fingerprint,
                policy_epoch=session.policy_epoch,
                expires_at=self._security_now() + ttl,
                capability=snapshot.capability,
                action=snapshot.action,
                target_json=target_json,
                arguments_sha256=arguments_sha256,
                display_arguments_json=display_arguments_json,
            )
            session.challenges[challenge_id] = _ApprovalRecord(challenge)
            self._audit.append(
                "control.approval_challenge_created",
                session_id=session.session_id,
                details={
                    "challenge_id": challenge_id,
                    "request_fingerprint": challenge.request_fingerprint,
                    "ttl_seconds": ttl,
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
            if self._security_now() >= challenge.expires_at:
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
                self._global_epoch,
            )
            self._audit.append(
                "control.approval_granted",
                session_id=session.session_id,
                details={
                    "approval_jti": jti,
                    "challenge_id": challenge_id,
                    "request_fingerprint": challenge.request_fingerprint,
                    "policy_epoch": session.policy_epoch,
                },
            )
            return token

    def authorize(self, request: ActionRequest, *, approval_token: str | None = None) -> ExecutionPermit:
        with self._lock:
            session = self._require_active_session(request.session_id)
            decision, snapshot = self._evaluate_locked(session, request)
            if decision.kind is DecisionKind.DENY or snapshot is None:
                raise AuthorizationDenied(decision.reason)
            if decision.kind is DecisionKind.REQUIRE_APPROVAL:
                if approval_token is None:
                    raise AuthorizationDenied("approval_required")
                approval = self._verify_token(approval_token, expected_kind="approval", session=session)
                if approval.request_fingerprint != decision.request_fingerprint:
                    raise ApprovalError("approval request fingerprint mismatch")
                if approval.consumed:
                    raise ApprovalError("approval token already used")
                approval.consumed = True
                self._audit.append(
                    "control.approval_consumed",
                    session_id=session.session_id,
                    details={"approval_jti": approval.jti, "request_fingerprint": decision.request_fingerprint},
                )
            elif approval_token is not None:
                raise ApprovalError("approval token supplied for approval-free action")

            now = self._security_now()
            remaining = session.expires_at - now
            if remaining <= 0:
                raise SessionStateError("control session expired during authorization")
            ttl = min(self.max_permit_ttl, remaining)
            jti = self._unique_nonce("permit")
            expires_at = now + ttl
            payload = {
                "kind": "permit",
                "jti": jti,
                "session_id": session.session_id,
                "request_fingerprint": snapshot.fingerprint,
                "policy_epoch": session.policy_epoch,
                "exp": expires_at,
                "global_epoch": self._global_epoch,
            }
            token = self._sign(payload)
            record = _TokenRecord(
                "permit",
                jti,
                session.session_id,
                snapshot.fingerprint,
                session.policy_epoch,
                expires_at,
                self._global_epoch,
            )
            session.permits[jti] = record
            permit = ExecutionPermit(token, session.session_id, snapshot.fingerprint, session.policy_epoch, expires_at)
            self._audit.append(
                "control.execution_permit_issued",
                session_id=session.session_id,
                details={
                    "permit_jti": jti,
                    "request_fingerprint": snapshot.fingerprint,
                    "ttl_seconds": ttl,
                    "policy_epoch": session.policy_epoch,
                },
            )
            return permit

    def consume_execution_permit(self, permit_token: str, request: ActionRequest) -> None:
        with self._lock:
            session = self._require_active_session(request.session_id)
            snapshot = self._snapshot_request(request)
            permit = self._verify_token(permit_token, expected_kind="permit", session=session)
            if permit.request_fingerprint != snapshot.fingerprint:
                raise PermitError("permit request fingerprint mismatch")
            if permit.consumed:
                raise PermitError("permit already consumed")
            permit.consumed = True
            self._audit.append(
                "control.execution_permit_consumed",
                session_id=session.session_id,
                details={"permit_jti": permit.jti, "request_fingerprint": snapshot.fingerprint},
            )

    def update_policy(self, session_id: str, policy: ControlPolicy) -> None:
        with self._lock:
            session = self._require_active_session(session_id)
            session.policy = policy
            session.policy_epoch += 1
            self._invalidate_ephemeral(session)
            self._audit.append(
                "control.policy_updated",
                session_id=session_id,
                details={"policy_epoch": session.policy_epoch},
            )

    def cancel_session(self, session_id: str, *, reason: str = "cancelled") -> None:
        with self._lock:
            callbacks = self._transition_session_locked(session_id, SessionState.CANCELLED, reason)
        self._dispatch_cancel_callbacks(session_id, str(reason), callbacks)

    def user_takeover(self, session_id: str, *, reason: str = "user_takeover") -> None:
        with self._lock:
            callbacks = self._transition_session_locked(session_id, SessionState.USER_TAKEOVER, reason)
        self._dispatch_cancel_callbacks(session_id, str(reason), callbacks)

    def emergency_stop(self, *, session_id: str | None = None, reason: str = "emergency_stop") -> None:
        dispatch: list[tuple[str, tuple[CancelCallback, ...]]] = []
        with self._lock:
            if session_id is not None:
                callbacks = self._transition_session_locked(session_id, SessionState.EMERGENCY_STOPPED, reason)
                dispatch.append((session_id, callbacks))
            else:
                self._global_emergency_stop = True
                self._global_epoch += 1
                affected = [sid for sid, session in self._sessions.items() if session.state is SessionState.ACTIVE]
                for sid in affected:
                    callbacks = self._transition_session_locked(sid, SessionState.EMERGENCY_STOPPED, reason)
                    dispatch.append((sid, callbacks))
                self._audit.append(
                    "control.global_emergency_stop",
                    details={"reason": reason, "affected_sessions": len(affected), "global_epoch": self._global_epoch},
                )
        for sid, callbacks in dispatch:
            self._dispatch_cancel_callbacks(sid, str(reason), callbacks)

    def reset_global_emergency_stop(self) -> None:
        with self._lock:
            if not self._global_emergency_stop:
                return
            self._global_emergency_stop = False
            self._global_epoch += 1
            self._audit.append("control.global_emergency_stop_reset", details={"global_epoch": self._global_epoch})

    def session_state(self, session_id: str) -> SessionState:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionStateError("unknown control session")
            callbacks = self._expire_if_needed(session)
            state = session.state
        if callbacks:
            self._dispatch_cancel_callbacks(session_id, "session_expired", callbacks)
        return state

    def request_fingerprint(self, request: ActionRequest) -> str:
        with self._lock:
            return self._snapshot_request(request).fingerprint

    def _evaluate_locked(self, session: _Session, request: ActionRequest) -> tuple[PolicyDecision, _RequestSnapshot | None]:
        snapshot: _RequestSnapshot | None = None
        try:
            snapshot = self._snapshot_request(request)
            decision = evaluate_policy(
                session.policy,
                request,
                fingerprint=snapshot.fingerprint,
                policy_epoch=session.policy_epoch,
            )
        except (AttributeError, OSError, TypeError, ValueError):
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
        self._audit.append(
            "control.policy_decision",
            session_id=session.session_id,
            details={
                "decision": decision.kind.value,
                "reason": decision.reason,
                "risk": None if decision.risk is None else decision.risk.value,
                "capability": self._capability_string(request.capability),
                "action": str(request.action),
                "request_fingerprint": decision.request_fingerprint,
                "policy_epoch": session.policy_epoch,
                "untrusted_context_sha256": self._safe_hash_untrusted_context(request.untrusted_context),
            },
        )
        return decision, snapshot

    def _snapshot_request(self, request: ActionRequest) -> _RequestSnapshot:
        capability = self._capability_string(request.capability)
        action = str(request.action).strip()
        target = request.target.canonical()
        arguments = self._normalize_json_value(request.arguments)
        payload = {
            "session_id": str(request.session_id),
            "capability": capability,
            "action": action,
            "target": target,
            "arguments": arguments,
        }
        fingerprint = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        return _RequestSnapshot(capability, action, target, arguments, fingerprint)

    def _transition_session_locked(self, session_id: str, state: SessionState, reason: str) -> tuple[CancelCallback, ...]:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionStateError("unknown control session")
        if session.state is not SessionState.ACTIVE:
            return ()
        session.state = state
        session.policy_epoch += 1
        self._invalidate_ephemeral(session)
        self._audit.append(
            "control.session_state_changed",
            session_id=session_id,
            details={"state": state.value, "reason": str(reason), "policy_epoch": session.policy_epoch},
        )
        return tuple(session.cancel_callbacks)

    def _dispatch_cancel_callbacks(self, session_id: str, reason: str, callbacks: tuple[CancelCallback, ...]) -> None:
        for index, callback in enumerate(callbacks):
            thread = threading.Thread(
                target=self._run_cancel_callback,
                args=(callback, session_id, reason),
                name=f"hive-cancel-{session_id}-{index}",
                daemon=True,
            )
            thread.start()

    def _run_cancel_callback(self, callback: CancelCallback, session_id: str, reason: str) -> None:
        try:
            callback(session_id, reason)
        except Exception as exc:
            with self._lock:
                self._audit.append(
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
        callbacks = self._expire_if_needed(session)
        if callbacks:
            self._dispatch_cancel_callbacks(session_id, "session_expired", callbacks)
        if session.state is not SessionState.ACTIVE:
            raise SessionStateError(f"control session is not active: {session.state.value}")
        return session

    def _expire_if_needed(self, session: _Session) -> tuple[CancelCallback, ...]:
        if session.state is SessionState.ACTIVE and self._security_now() >= session.expires_at:
            return self._transition_session_locked(session.session_id, SessionState.EXPIRED, "session_expired")
        return ()

    def _verify_token(self, token: str, *, expected_kind: str, session: _Session) -> _TokenRecord:
        error_type = PermitError if expected_kind == "permit" else ApprovalError
        if not isinstance(token, str) or not token or len(token) > _MAX_SIGNED_TOKEN_CHARS:
            raise error_type("signed token length outside bounds")
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
        if not isinstance(payload, dict) or payload.get("kind") != expected_kind:
            raise error_type("signed token kind mismatch")
        if payload.get("session_id") != session.session_id:
            raise error_type("signed token session mismatch")
        if payload.get("global_epoch") != self._global_epoch:
            raise error_type("signed token invalidated by emergency epoch")
        if payload.get("policy_epoch") != session.policy_epoch:
            raise error_type("signed token invalidated by policy epoch")
        exp = payload.get("exp")
        if not isinstance(exp, (int, float)) or self._security_now() >= float(exp):
            raise error_type("signed token expired")
        jti = payload.get("jti")
        if not isinstance(jti, str) or not jti:
            raise error_type("signed token missing jti")
        fingerprint = payload.get("request_fingerprint")
        if not isinstance(fingerprint, str) or len(fingerprint) != 64:
            raise error_type("signed token request fingerprint malformed")
        store = session.approval_tokens if expected_kind == "approval" else session.permits
        record = store.get(jti)
        if record is None:
            raise error_type("signed token is unknown or revoked")
        if (
            record.kind != expected_kind
            or record.session_id != session.session_id
            or record.request_fingerprint != fingerprint
            or record.policy_epoch != payload.get("policy_epoch")
            or record.global_epoch != payload.get("global_epoch")
            or record.expires_at != float(exp)
        ):
            raise error_type("signed token record mismatch")
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
        if ttl != ttl or ttl in (float("inf"), float("-inf")) or ttl <= 0 or ttl > maximum:
            raise ApprovalError(f"{label} ttl outside configured bounds")
        return ttl

    def _security_now(self) -> float:
        value = float(self._security_clock())
        if value != value or value in (float("inf"), float("-inf")):
            raise SessionStateError("security clock returned a non-finite value")
        return value

    @staticmethod
    def _capability_string(capability: Any) -> str:
        value = getattr(capability, "value", capability)
        return str(value)

    @staticmethod
    def _safe_hash_untrusted_context(value: Mapping[str, Any]) -> str:
        try:
            normalized = PermissionControlPlane._normalize_json_value(value)
            payload = {"context": normalized}
        except (TypeError, ValueError):
            payload = {"invalid_untrusted_context": type(value).__name__}
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_json_value(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(k): PermissionControlPlane._normalize_json_value(v)
                for k, v in sorted(list(value.items()), key=lambda item: str(item[0]))
            }
        if isinstance(value, (list, tuple)):
            return [PermissionControlPlane._normalize_json_value(item) for item in list(value)]
        if value is None or isinstance(value, (bool, int, float, str)):
            if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
                raise ValueError("non-finite action argument")
            return value
        raise ValueError(f"unsupported action argument type: {type(value).__name__}")
