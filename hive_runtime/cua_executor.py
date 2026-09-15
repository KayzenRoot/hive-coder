from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from .control_plane import PermissionControlPlane
from .control_types import ActionRequest, Capability
from .cua import CuaAdapter
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


SAFE_CUA_TOOLS: dict[str, SafeCuaTool] = {
    "pointer.click": SafeCuaTool(Capability.POINTER_INPUT, "pointer.click", "pointer.click"),
    "keyboard.type_text": SafeCuaTool(Capability.TEXT_INPUT, "keyboard.type_text", "keyboard.type_text"),
}


class GatedCuaActionExecutor:
    """Permit-gated, fail-closed bridge to the tiny approved Cua tools/call subset."""

    def __init__(self, *, control_plane: PermissionControlPlane, peer: Any, live_target_resolver: LiveTargetResolver, post_action_verifier: PostActionVerifier | None = None, timeout: float = 5.0, tool_bindings: Mapping[str, str] | None = None) -> None:
        self.control_plane = control_plane
        self.peer = peer
        self.live_target_resolver = live_target_resolver
        self.post_action_verifier = post_action_verifier
        self.timeout = float(timeout)
        bindings = dict(tool_bindings or {})
        if set(bindings) - set(SAFE_CUA_TOOLS) or any(not isinstance(v, str) or not v for v in bindings.values()):
            raise AuthorizationDenied("untrusted_or_unknown_cua_tool_binding")
        self.tool_bindings = bindings
        self._lock = threading.RLock()
        self._cancelled_sessions: set[str] = set()
        self._inflight: dict[str, threading.Event] = {}

    def cancellation_callback(self, session_id: str, reason: str) -> None:
        with self._lock:
            self._cancelled_sessions.add(session_id)
            event = self._inflight.get(session_id)
            if event is not None:
                event.set()
        close = getattr(self.peer, "close", None)
        if callable(close):
            try:
                close()
            except Exception:
                pass

    def execute(self, request: ActionRequest, *, permit_token: str) -> Any:
        spec = SAFE_CUA_TOOLS.get(str(request.action))
        if spec is None:
            raise AuthorizationDenied("cua_tool_not_in_safe_subset")
        capability = request.capability.value if isinstance(request.capability, Capability) else str(request.capability)
        if capability != spec.capability.value:
            raise AuthorizationDenied("cua_tool_capability_mismatch")
        arguments = self._validated_arguments(spec, request.arguments)
        if self.peer is None:
            raise AdapterStateError("Cua MCP peer is not available")
        tool_name = self.tool_bindings.get(spec.action, spec.tool_name)

        with self._lock:
            if request.session_id in self._cancelled_sessions:
                raise AuthorizationDenied("control_session_cancelled_before_execution")
            if request.session_id in self._inflight:
                raise AuthorizationDenied("parallel_cua_mutation_for_session_denied")
            cancel_event = threading.Event()
            self._inflight[request.session_id] = cancel_event

        try:
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

            meta = CuaAdapter.modern_meta()
            meta["hive/requestFingerprint"] = self.control_plane.request_fingerprint(request)
            params = {"name": tool_name, "arguments": arguments, "_meta": meta}
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
    def _validated_arguments(spec: SafeCuaTool, raw: Any) -> dict[str, Any]:
        if not isinstance(raw, Mapping):
            raise AuthorizationDenied("cua_arguments_must_be_object")
        args = dict(raw)
        if spec.action == "pointer.click":
            if set(args) != {"x", "y"}:
                raise AuthorizationDenied("pointer_click_arguments_not_allowlisted")
            for key in ("x", "y"):
                value = args[key]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= float(value) <= 100000:
                    raise AuthorizationDenied("pointer_click_coordinate_invalid")
            return args
        if spec.action == "keyboard.type_text":
            if set(args) != {"text"} or not isinstance(args.get("text"), str):
                raise AuthorizationDenied("type_text_arguments_not_allowlisted")
            text = args["text"]
            if not text or len(text) > 4096 or "\x00" in text:
                raise AuthorizationDenied("type_text_payload_outside_bounds")
            return {"text": text}
        raise AuthorizationDenied("cua_tool_not_in_safe_subset")

    @staticmethod
    def _validate_tool_result(result: Any) -> None:
        if not isinstance(result, Mapping):
            raise RpcProtocolError("Cua tools/call result must be an object")
        if result.get("isError") is True:
            raise RpcProtocolError("Cua tools/call reported an error")
