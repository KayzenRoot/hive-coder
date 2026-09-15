from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

from .control_plane import PermissionControlPlane
from .control_types import ActionRequest, Capability
from .errors import AdapterStateError, AuthorizationDenied, RpcProtocolError


class LiveTargetResolver(Protocol):
    def __call__(self, request: ActionRequest) -> Mapping[str, str | None]: ...


class PostActionVerifier(Protocol):
    def __call__(self, request: ActionRequest, result: Any) -> bool: ...


@dataclass(frozen=True)
class SafeCuaTool:
    capability: Capability
    tool_name: str
    action: str
    mutating: bool = True


# Intentionally tiny first mutation surface. Clipboard, shell, filesystem,
# destructive and privileged operations are not represented and therefore deny.
SAFE_CUA_TOOLS: dict[str, SafeCuaTool] = {
    "pointer.click": SafeCuaTool(Capability.POINTER_INPUT, "pointer.click", "pointer.click"),
    "keyboard.type_text": SafeCuaTool(Capability.TEXT_INPUT, "keyboard.type_text", "keyboard.type_text"),
}


class GatedCuaActionExecutor:
    """Permit-gated bridge to Cua MCP tools/call.

    The executor never creates approvals or permits. It consumes a permit issued
    by PermissionControlPlane, revalidates the live target immediately before
    dispatch, and exposes cancellation hooks for emergency stop/user takeover.
    """

    def __init__(
        self,
        *,
        control_plane: PermissionControlPlane,
        peer: Any,
        live_target_resolver: LiveTargetResolver,
        post_action_verifier: PostActionVerifier | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.control_plane = control_plane
        self.peer = peer
        self.live_target_resolver = live_target_resolver
        self.post_action_verifier = post_action_verifier
        self.timeout = float(timeout)
        self._lock = threading.RLock()
        self._cancelled_sessions: set[str] = set()
        self._inflight: dict[str, threading.Event] = {}

    def cancellation_callback(self, session_id: str, reason: str) -> None:
        with self._lock:
            self._cancelled_sessions.add(session_id)
            event = self._inflight.get(session_id)
            if event is not None:
                event.set()

    def execute(self, request: ActionRequest, *, permit_token: str) -> Any:
        spec = SAFE_CUA_TOOLS.get(str(request.action))
        if spec is None:
            raise AuthorizationDenied("cua_tool_not_in_safe_subset")
        capability = request.capability.value if isinstance(request.capability, Capability) else str(request.capability)
        if capability != spec.capability.value:
            raise AuthorizationDenied("cua_tool_capability_mismatch")
        if not isinstance(request.arguments, Mapping):
            raise AuthorizationDenied("cua_arguments_must_be_object")
        if self.peer is None:
            raise AdapterStateError("Cua MCP peer is not available")

        with self._lock:
            if request.session_id in self._cancelled_sessions:
                raise AuthorizationDenied("control_session_cancelled_before_execution")
            if request.session_id in self._inflight:
                raise AuthorizationDenied("parallel_cua_mutation_for_session_denied")
            cancel_event = threading.Event()
            self._inflight[request.session_id] = cancel_event

        try:
            # The permit is consumed immediately before live target validation and
            # dispatch. A failed validation cannot reuse the permit.
            self.control_plane.consume_execution_permit(permit_token, request)
            if cancel_event.is_set():
                raise AuthorizationDenied("control_session_cancelled_before_dispatch")
            live = dict(self.live_target_resolver(request))
            expected = request.target.canonical()
            for field in ("application", "window_id"):
                if expected.get(field) != live.get(field):
                    raise AuthorizationDenied(f"live_target_{field}_mismatch")
            if cancel_event.is_set():
                raise AuthorizationDenied("control_session_cancelled_before_dispatch")

            params = {
                "name": spec.tool_name,
                "arguments": dict(request.arguments),
                "_meta": {"hive/requestFingerprint": self.control_plane.request_fingerprint(request)},
            }
            result = self.peer.request("tools/call", params, timeout=self.timeout)
            if cancel_event.is_set():
                raise AuthorizationDenied("control_session_cancelled_during_execution")
            self._validate_tool_result(result)
            if self.post_action_verifier is not None and not self.post_action_verifier(request, result):
                raise RpcProtocolError("Cua post-action verification failed")
            return result
        finally:
            with self._lock:
                self._inflight.pop(request.session_id, None)

    @staticmethod
    def _validate_tool_result(result: Any) -> None:
        if not isinstance(result, Mapping):
            raise RpcProtocolError("Cua tools/call result must be an object")
        if result.get("isError") is True:
            raise RpcProtocolError("Cua tools/call reported an error")
