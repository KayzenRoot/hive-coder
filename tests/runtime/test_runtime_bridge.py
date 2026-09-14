from __future__ import annotations

import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from hive_runtime.cua import CAPABILITIES_META_KEY, CUA_MCP_PROTOCOL_VERSION, VERSION_META_KEY, CuaAdapter
from hive_runtime.errors import ProcessExitedError, RpcProtocolError, RpcTimeoutError
from hive_runtime.interpreter import ACP_PROTOCOL_VERSION, InterpreterAdapter
from hive_runtime.jsonrpc import JsonRpcPeer
from hive_runtime.process import ManagedStdioProcess, ProcessSpec, safe_child_environment


def python_server(source: str) -> tuple[str, ...]:
    return (sys.executable, "-u", "-c", source)


ECHO_SERVER = r'''
import json, sys
for line in sys.stdin:
    msg = json.loads(line)
    if "id" in msg:
        print(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":{"method":msg["method"],"params":msg.get("params")}}), flush=True)
'''


class ProcessEnvironmentTests(unittest.TestCase):
    def test_ambient_secret_is_not_inherited(self) -> None:
        with patch.dict(os.environ, {"HIVE_TEST_SECRET": "do-not-leak"}, clear=False):
            child = safe_child_environment()
        self.assertNotIn("HIVE_TEST_SECRET", child)

    def test_explicit_override_is_passed(self) -> None:
        child = safe_child_environment({"HIVE_EXPLICIT_TEST": "allowed"})
        self.assertEqual(child["HIVE_EXPLICIT_TEST"], "allowed")

    def test_cua_telemetry_disable_cannot_be_overridden(self) -> None:
        adapter = CuaAdapter.from_binary("cua-driver", env_overrides={"CUA_DRIVER_RS_TELEMETRY_ENABLED": "true"})
        self.assertEqual(adapter.env_overrides["CUA_DRIVER_RS_TELEMETRY_ENABLED"], "false")


class JsonRpcTests(unittest.TestCase):
    def test_request_round_trip(self) -> None:
        process = ManagedStdioProcess(ProcessSpec(python_server(ECHO_SERVER), name="echo")).start()
        peer = JsonRpcPeer(process).start()
        try:
            result = peer.request("ping", {"x": 1}, timeout=1)
            self.assertEqual(result, {"method": "ping", "params": {"x": 1}})
        finally:
            peer.close()

    def test_timeout_is_bounded(self) -> None:
        server = "import sys, time\nfor line in sys.stdin:\n time.sleep(5)\n"
        process = ManagedStdioProcess(ProcessSpec(python_server(server), name="timeout")).start()
        peer = JsonRpcPeer(process).start()
        try:
            with self.assertRaises(RpcTimeoutError):
                peer.request("never", {}, timeout=0.05)
        finally:
            peer.close()

    def test_malformed_payload_fails_closed(self) -> None:
        server = "import sys\nfor line in sys.stdin:\n print('not-json', flush=True)\n"
        process = ManagedStdioProcess(ProcessSpec(python_server(server), name="malformed")).start()
        peer = JsonRpcPeer(process).start()
        try:
            with self.assertRaises(RpcProtocolError):
                peer.request("boom", {}, timeout=1)
        finally:
            peer.close()

    def test_unexpected_inbound_request_is_denied(self) -> None:
        server = r'''
import json, sys
request = json.loads(sys.stdin.readline())
print(json.dumps({"jsonrpc":"2.0","id":99,"method":"session/request_permission","params":{"sessionId":"s"}}), flush=True)
denial = json.loads(sys.stdin.readline())
assert denial["id"] == 99 and denial["error"]["code"] == -32601
print(json.dumps({"jsonrpc":"2.0","id":request["id"],"result":{"denied":True}}), flush=True)
'''
        process = ManagedStdioProcess(ProcessSpec(python_server(server), name="inbound")).start()
        peer = JsonRpcPeer(process).start()
        try:
            result = peer.request("trigger", {}, timeout=1)
            self.assertEqual(result, {"denied": True})
        finally:
            peer.close()

    def test_process_exit_wakes_pending_request(self) -> None:
        server = "import sys\nsys.stdin.readline()\nsys.exit(7)\n"
        process = ManagedStdioProcess(ProcessSpec(python_server(server), name="exit")).start()
        peer = JsonRpcPeer(process).start()
        try:
            with self.assertRaises(ProcessExitedError):
                peer.request("exit", {}, timeout=1)
        finally:
            peer.close()


class InterpreterAdapterTests(unittest.TestCase):
    def test_handshake_session_cancel_close_without_prompt(self) -> None:
        server = r'''
import json, sys
session = "sess-1"
for line in sys.stdin:
    msg = json.loads(line)
    method = msg.get("method")
    if method == "initialize":
        assert msg["params"]["protocolVersion"] == 1
        print(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":{"protocolVersion":1,"agentInfo":{"name":"codex-acp","title":"Open Interpreter","version":"0.0.43"},"agentCapabilities":{"sessionCapabilities":{"close":{},"list":{}}}}}), flush=True)
    elif method == "session/new":
        assert msg["params"]["mcpServers"] == []
        print(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":{"sessionId":session}}), flush=True)
        print(json.dumps({"jsonrpc":"2.0","method":"session/update","params":{"sessionId":session,"update":{"sessionUpdate":"available_commands_update"}}}), flush=True)
    elif method == "session/cancel":
        assert msg["params"]["sessionId"] == session and "id" not in msg
    elif method == "session/close":
        assert msg["params"]["sessionId"] == session
        print(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":{}}), flush=True)
    else:
        raise SystemExit(9)
'''
        adapter = InterpreterAdapter(python_server(server), timeout=1)
        try:
            identity = adapter.start()
            self.assertEqual(identity.protocol_version, ACP_PROTOCOL_VERSION)
            self.assertEqual(identity.title, "Open Interpreter")
            with tempfile.TemporaryDirectory() as tmp:
                session_id = adapter.create_session(tmp)
            self.assertEqual(session_id, "sess-1")
            adapter.cancel(session_id)
            deadline = time.time() + 1
            while not adapter.updates() and time.time() < deadline:
                time.sleep(0.01)
            self.assertTrue(adapter.updates())
            adapter.close_session(session_id)
        finally:
            adapter.close()

    def test_protocol_version_mismatch_fails_closed(self) -> None:
        server = r'''
import json, sys
msg = json.loads(sys.stdin.readline())
print(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":{"protocolVersion":2,"agentInfo":{"name":"wrong"},"agentCapabilities":{}}}), flush=True)
'''
        adapter = InterpreterAdapter(python_server(server), timeout=1)
        with self.assertRaises(RpcProtocolError):
            adapter.start()
        self.assertIsNone(adapter.process)


class CuaAdapterTests(unittest.TestCase):
    def test_modern_discovery_only(self) -> None:
        server = rf'''
import json, sys
msg = json.loads(sys.stdin.readline())
assert msg["method"] == "server/discover"
meta = msg["params"]["_meta"]
assert meta["{VERSION_META_KEY}"] == "{CUA_MCP_PROTOCOL_VERSION}"
assert isinstance(meta["{CAPABILITIES_META_KEY}"], dict)
result = {{
  "resultType":"complete",
  "supportedVersions":["{CUA_MCP_PROTOCOL_VERSION}"],
  "capabilities":{{"extensions":{{"io.modelcontextprotocol/skills":{{}}}}}},
  "tools":[{{"name":"get_config"}},{{"name":"click"}}],
  "ttlMs":0,
  "cacheScope":"private",
  "_meta":{{"io.modelcontextprotocol/serverInfo":{{"name":"cua-driver","version":"0.28.1"}}}}
}}
print(json.dumps({{"jsonrpc":"2.0","id":msg["id"],"result":result}}), flush=True)
for line in sys.stdin:
    extra = json.loads(line)
    if extra.get("method") == "tools/call":
        raise SystemExit(42)
'''
        adapter = CuaAdapter(python_server(server), timeout=1)
        try:
            discovery = adapter.start()
            self.assertEqual(discovery.protocol_version, CUA_MCP_PROTOCOL_VERSION)
            self.assertEqual(discovery.server_name, "cua-driver")
            self.assertIn("click", discovery.tool_names)
            self.assertFalse(hasattr(adapter, "call_tool"), "WO-0003 must not expose tools/call")
        finally:
            adapter.close()

    def test_missing_pinned_version_fails_closed(self) -> None:
        server = r'''
import json, sys
msg = json.loads(sys.stdin.readline())
result = {"resultType":"complete","supportedVersions":["2025-06-18"],"capabilities":{},"tools":[]}
print(json.dumps({"jsonrpc":"2.0","id":msg["id"],"result":result}), flush=True)
'''
        adapter = CuaAdapter(python_server(server), timeout=1)
        with self.assertRaises(RpcProtocolError):
            adapter.start()
        self.assertIsNone(adapter.process)


class VersionPreflightTests(unittest.TestCase):
    def test_exact_version_token_is_required(self) -> None:
        from hive_runtime.preflight import reports_exact_version
        self.assertTrue(reports_exact_version("interpreter 0.0.43", "0.0.43"))
        self.assertFalse(reports_exact_version("interpreter 0.0.430", "0.0.43"))
        self.assertFalse(reports_exact_version("interpreter 0.0.43-beta.1", "0.0.43"))


if __name__ == "__main__":
    unittest.main()
