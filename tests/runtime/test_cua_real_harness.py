from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from hive_runtime.cua import CUA_MCP_PROTOCOL_VERSION, CuaAdapter, CuaDiscovery, CuaTool
from hive_runtime.cua_harness import CuaContractResolver, RealCuaWindowsHarness
from hive_runtime.errors import AuthorizationDenied, RpcProtocolError


def tool(name, caps, props, *, read_only=False):
    return CuaTool(name=name, capabilities=tuple(caps), input_schema={"type": "object", "properties": {p: {} for p in props}}, annotations={"readOnlyHint": read_only})


def discovery(*tools):
    return CuaDiscovery(protocol_version=CUA_MCP_PROTOCOL_VERSION, supported_versions=(CUA_MCP_PROTOCOL_VERSION,), server_name="cua-driver", tool_names=tuple(t.name for t in tools), raw_capabilities={"tools": {}}, tools=tuple(tools))


class CuaInventoryTests(unittest.TestCase):
    def test_canonical_tools_list_preserves_schema_and_capabilities(self):
        result = {"resultType": "complete", "tools": [{"name": "click", "inputSchema": {"type": "object", "properties": {"x": {}, "y": {}}}, "capabilities": ["input.pointer.click.left"], "annotations": {"readOnlyHint": False}}]}
        tools = CuaAdapter._validate_tools_list(result)
        self.assertEqual(tools[0].name, "click")
        self.assertIn("input.pointer.click.left", tools[0].capabilities)

    def test_incomplete_tool_metadata_fails_closed(self):
        with self.assertRaises(RpcProtocolError):
            CuaAdapter._validate_tools_list({"resultType": "complete", "tools": [{"name": "click"}]})


class CuaContractResolverTests(unittest.TestCase):
    def test_resolves_by_advertised_capability_not_model_name(self):
        d = discovery(tool("click", ("input.pointer.click.left",), ("x", "y")), tool("type_text", ("input.keyboard.type",), ("text",)))
        resolved = CuaContractResolver.resolve(d)
        self.assertEqual(resolved.click_tool.name, "click")
        self.assertEqual(resolved.type_tool.name, "type_text")

    def test_missing_required_schema_fails_closed(self):
        d = discovery(tool("click", ("input.pointer.click.left",), ("x",)), tool("type_text", ("input.keyboard.type",), ("text",)))
        with self.assertRaises(RpcProtocolError):
            CuaContractResolver.resolve(d)

    def test_ambiguous_capability_fails_closed(self):
        d = discovery(tool("click", ("input.pointer.click.left",), ("x", "y")), tool("click2", ("input.pointer.click",), ("x", "y")), tool("type_text", ("input.keyboard.type",), ("text",)))
        with self.assertRaises(RpcProtocolError):
            CuaContractResolver.resolve(d)

    def test_read_only_mutation_advertisement_fails_closed(self):
        d = discovery(tool("click", ("input.pointer.click.left",), ("x", "y"), read_only=True), tool("type_text", ("input.keyboard.type",), ("text",)))
        with self.assertRaises(RpcProtocolError):
            CuaContractResolver.resolve(d)


class RealHarnessOptInTests(unittest.TestCase):
    def test_real_harness_is_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(AuthorizationDenied):
                RealCuaWindowsHarness(binary="cua-driver.exe", sandbox_application="notepad.exe")

    def test_opt_in_still_requires_sandbox(self):
        with patch.dict(os.environ, {"HIVE_ENABLE_REAL_CUA": "1"}, clear=True):
            with self.assertRaises(AuthorizationDenied):
                RealCuaWindowsHarness(binary="cua-driver.exe", sandbox_application="")


if __name__ == "__main__":
    unittest.main()
