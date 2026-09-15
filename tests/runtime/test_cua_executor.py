from __future__ import annotations

import unittest

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.control_policy import ControlPolicy
from hive_runtime.control_types import ActionRequest, ActionTarget, Capability
from hive_runtime.cua_executor import GatedCuaActionExecutor
from hive_runtime.errors import AuthorizationDenied, PermitError, RpcProtocolError


class FakePeer:
    def __init__(self) -> None:
        self.calls = []
    def request(self, method, params, timeout):
        self.calls.append((method, params, timeout))
        return {"content": [], "isError": False}


def policy() -> ControlPolicy:
    return ControlPolicy(
        allowed_capabilities=frozenset({Capability.POINTER_INPUT, Capability.TEXT_INPUT}),
        allowed_actions=frozenset({"pointer.click", "keyboard.type_text"}),
        allowed_applications=frozenset({"notepad.exe"}),
        allowed_window_ids=frozenset({"win-1"}),
    )


class GatedCuaExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cp = PermissionControlPlane(token_key=b"x" * 32)
        self.peer = FakePeer()
        self.sid = self.cp.create_session(policy(), duration_seconds=60)
        self.target = ActionTarget(application="notepad.exe", window_id="win-1")
        self.executor = GatedCuaActionExecutor(
            control_plane=self.cp,
            peer=self.peer,
            live_target_resolver=lambda request: request.target.canonical(),
        )
        self.cp.register_cancel_callback(self.sid, self.executor.cancellation_callback)

    def _request(self, action="pointer.click", capability=Capability.POINTER_INPUT, arguments=None):
        return ActionRequest(
            session_id=self.sid,
            capability=capability,
            action=action,
            target=self.target,
            arguments=arguments or {"x": 10, "y": 20},
        )

    def _permit(self, request):
        challenge = self.cp.create_approval_challenge(request)
        approval = self.cp.approve_challenge_from_trusted_ui(challenge.challenge_id, session_id=self.sid)
        return self.cp.authorize(request, approval_token=approval).token

    def test_permit_gates_safe_tool(self):
        request = self._request()
        result = self.executor.execute(request, permit_token=self._permit(request))
        self.assertFalse(result["isError"])
        self.assertEqual(self.peer.calls[0][0], "tools/call")

    def test_unknown_tool_denied_before_rpc(self):
        request = self._request("shell.execute", Capability.SHELL_EXECUTE)
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token="not-a-permit")
        self.assertEqual(self.peer.calls, [])

    def test_capability_mismatch_denied(self):
        request = self._request(capability=Capability.TEXT_INPUT)
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token="x")
        self.assertEqual(self.peer.calls, [])

    def test_permit_is_single_use(self):
        request = self._request()
        permit = self._permit(request)
        self.executor.execute(request, permit_token=permit)
        with self.assertRaises(PermitError):
            self.executor.execute(request, permit_token=permit)
        self.assertEqual(len(self.peer.calls), 1)

    def test_live_window_swap_denied_and_permit_burned(self):
        request = self._request()
        permit = self._permit(request)
        self.executor.live_target_resolver = lambda _: {"application": "notepad.exe", "window_id": "evil-window"}
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token=permit)
        self.assertEqual(self.peer.calls, [])
        self.executor.live_target_resolver = lambda r: r.target.canonical()
        with self.assertRaises(PermitError):
            self.executor.execute(request, permit_token=permit)

    def test_user_takeover_blocks_future_dispatch(self):
        self.cp.user_takeover(self.sid)
        request = self._request()
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token="x")
        self.assertEqual(self.peer.calls, [])

    def test_tool_error_fails_closed(self):
        request = self._request()
        permit = self._permit(request)
        self.peer.request = lambda *args, **kwargs: {"isError": True}
        with self.assertRaises(RpcProtocolError):
            self.executor.execute(request, permit_token=permit)

    def test_post_action_verification_can_fail_closed(self):
        request = self._request()
        permit = self._permit(request)
        self.executor.post_action_verifier = lambda request, result: False
        with self.assertRaises(RpcProtocolError):
            self.executor.execute(request, permit_token=permit)


if __name__ == "__main__":
    unittest.main()
