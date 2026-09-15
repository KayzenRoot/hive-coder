from __future__ import annotations

import threading
import unittest

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.control_policy import CapabilityRule, ControlPolicy
from hive_runtime.control_types import ActionRequest, ActionTarget, Capability
from hive_runtime.cua_executor import GatedCuaActionExecutor
from hive_runtime.errors import AuthorizationDenied, PermitError, RpcProtocolError


class FakePeer:
    def __init__(self) -> None:
        self.calls = []
        self.closed = False

    def request(self, method, params, timeout):
        self.calls.append((method, params, timeout))
        return {"content": [], "isError": False}

    def close(self):
        self.closed = True


class BlockingPeer(FakePeer):
    def __init__(self) -> None:
        super().__init__()
        self.entered = threading.Event()
        self.released = threading.Event()

    def request(self, method, params, timeout):
        self.calls.append((method, params, timeout))
        self.entered.set()
        self.released.wait(1.0)
        return {"content": [], "isError": False}

    def close(self):
        self.closed = True
        self.released.set()


def policy() -> ControlPolicy:
    return ControlPolicy.build((
        CapabilityRule.build(Capability.POINTER_INPUT, allowed_actions=("pointer.click",), allowed_applications=("notepad.exe",), allowed_window_ids=("win-1",)),
        CapabilityRule.build(Capability.TEXT_INPUT, allowed_actions=("keyboard.type_text",), allowed_applications=("notepad.exe",), allowed_window_ids=("win-1",)),
    ))


class GatedCuaExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cp = PermissionControlPlane(token_key=b"x" * 32)
        self.peer = FakePeer()
        self.sid = self.cp.create_session(policy(), duration_seconds=60)
        self.target = ActionTarget(application="notepad.exe", window_id="win-1")
        self.executor = GatedCuaActionExecutor(control_plane=self.cp, peer=self.peer, live_target_resolver=lambda request: request.target.canonical())
        self.cp.register_cancel_callback(self.sid, self.executor.cancellation_callback)

    def _request(self, action="pointer.click", capability=Capability.POINTER_INPUT, arguments=None):
        if arguments is None:
            arguments = {"x": 10, "y": 20} if action == "pointer.click" else {"text": "hello"}
        return ActionRequest(session_id=self.sid, capability=capability, action=action, target=self.target, arguments=arguments)

    def _permit(self, request):
        challenge = self.cp.create_approval_challenge(request)
        approval = self.cp.approve_challenge_from_trusted_ui(challenge.challenge_id, session_id=self.sid)
        return self.cp.authorize(request, approval_token=approval).token

    def test_permit_gates_safe_tool(self):
        request = self._request()
        result = self.executor.execute(request, permit_token=self._permit(request))
        self.assertFalse(result["isError"])
        self.assertEqual(self.peer.calls[0][0], "tools/call")

    def test_text_type_safe_tool(self):
        request = self._request("keyboard.type_text", Capability.TEXT_INPUT, {"text": "hello"})
        self.executor.execute(request, permit_token=self._permit(request))
        self.assertEqual(self.peer.calls[0][1]["arguments"], {"text": "hello"})

    def test_unknown_tool_denied_before_rpc(self):
        request = self._request("shell.execute", Capability.SHELL_EXECUTE, {"command": "whoami"})
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token="not-a-permit")
        self.assertEqual(self.peer.calls, [])

    def test_capability_mismatch_denied(self):
        request = self._request(capability=Capability.TEXT_INPUT)
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token="x")
        self.assertEqual(self.peer.calls, [])

    def test_extra_pointer_argument_denied(self):
        request = self._request(arguments={"x": 10, "y": 20, "button": "right"})
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token="x")
        self.assertEqual(self.peer.calls, [])

    def test_oversized_text_denied(self):
        request = self._request("keyboard.type_text", Capability.TEXT_INPUT, {"text": "x" * 4097})
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

    def test_user_takeover_blocks_future_dispatch_and_closes_peer(self):
        self.cp.user_takeover(self.sid)
        request = self._request()
        with self.assertRaises(AuthorizationDenied):
            self.executor.execute(request, permit_token="x")
        for _ in range(100):
            if self.peer.closed:
                break
            threading.Event().wait(0.005)
        self.assertTrue(self.peer.closed)
        self.assertEqual(self.peer.calls, [])

    def test_emergency_stop_interrupts_blocking_peer(self):
        peer = BlockingPeer()
        executor = GatedCuaActionExecutor(control_plane=self.cp, peer=peer, live_target_resolver=lambda request: request.target.canonical())
        self.cp.register_cancel_callback(self.sid, executor.cancellation_callback)
        request = self._request()
        permit = self._permit(request)
        errors = []
        thread = threading.Thread(target=lambda: self._capture(errors, lambda: executor.execute(request, permit_token=permit)))
        thread.start()
        self.assertTrue(peer.entered.wait(0.5))
        self.cp.emergency_stop(session_id=self.sid)
        thread.join(1.0)
        self.assertFalse(thread.is_alive())
        self.assertTrue(peer.closed)
        self.assertTrue(errors)
        self.assertIsInstance(errors[0], AuthorizationDenied)

    @staticmethod
    def _capture(errors, fn):
        try:
            fn()
        except Exception as exc:
            errors.append(exc)

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
