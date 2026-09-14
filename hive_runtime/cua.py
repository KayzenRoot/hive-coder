from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .errors import AdapterStateError, RpcProtocolError
from .foundation_lock import expected_foundation_version
from .jsonrpc import JsonRpcPeer
from .process import ManagedStdioProcess, ProcessSpec
from .preflight import verify_binary_version

CUA_MCP_PROTOCOL_VERSION = "2026-07-28"
VERSION_META_KEY = "io.modelcontextprotocol/protocolVersion"
CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities"


@dataclass(frozen=True)
class CuaDiscovery:
    protocol_version: str
    supported_versions: tuple[str, ...]
    server_name: str | None
    tool_names: tuple[str, ...]
    raw_capabilities: Mapping[str, Any]


class CuaAdapter:
    """Discovery-only Hive bridge for Cua Driver modern MCP. No tools/call API exists here."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        cwd: str | os.PathLike[str] | None = None,
        env_overrides: Mapping[str, str] | None = None,
        timeout: float = 5.0,
        preflight_binary: str | None = None,
        foundation_key: str | None = None,
    ) -> None:
        self.command = tuple(command)
        self.cwd = cwd
        self.env_overrides = dict(env_overrides or {})
        self.timeout = timeout
        self.preflight_binary = preflight_binary
        self.foundation_key = foundation_key
        self.process: ManagedStdioProcess | None = None
        self.peer: JsonRpcPeer | None = None
        self.discovery: CuaDiscovery | None = None

    @classmethod
    def from_binary(cls, binary: str, **kwargs) -> "CuaAdapter":
        env = {**dict(kwargs.pop("env_overrides", {}) or {}), "CUA_DRIVER_RS_TELEMETRY_ENABLED": "false"}
        return cls((binary, "mcp"), env_overrides=env, preflight_binary=binary, foundation_key="cuaDriver", **kwargs)

    @staticmethod
    def _meta(capabilities: Mapping[str, Any] | None = None) -> dict[str, Any]:
        return {
            VERSION_META_KEY: CUA_MCP_PROTOCOL_VERSION,
            CAPABILITIES_META_KEY: dict(capabilities or {}),
        }

    def start(self) -> CuaDiscovery:
        if self.process is not None:
            raise AdapterStateError("Cua adapter already started")
        if self.preflight_binary is not None:
            if self.foundation_key is None:
                raise AdapterStateError("production preflight requires a foundation key")
            verify_binary_version(
                self.preflight_binary,
                expected_foundation_version(self.foundation_key),
                env_overrides=self.env_overrides,
            )
        process = ManagedStdioProcess(ProcessSpec(self.command, cwd=self.cwd, env_overrides=self.env_overrides, name="cua-driver-mcp")).start()
        peer = JsonRpcPeer(process).start()
        self.process = process
        self.peer = peer
        try:
            result = peer.request("server/discover", {"_meta": self._meta()}, timeout=self.timeout)
            discovery = self._validate_discovery(result)
            self.discovery = discovery
            return discovery
        except BaseException:
            self.close()
            raise

    def _validate_discovery(self, result: Any) -> CuaDiscovery:
        if not isinstance(result, dict):
            raise RpcProtocolError("Cua server/discover result must be an object")
        versions = result.get("supportedVersions")
        if not isinstance(versions, list) or CUA_MCP_PROTOCOL_VERSION not in versions:
            raise RpcProtocolError("Cua does not advertise the pinned modern MCP version")
        if result.get("resultType") != "complete":
            raise RpcProtocolError("Cua discovery result is not complete")
        capabilities = result.get("capabilities")
        if not isinstance(capabilities, dict):
            raise RpcProtocolError("Cua discovery missing capabilities")
        tools = result.get("tools", [])
        if not isinstance(tools, list):
            raise RpcProtocolError("Cua discovery tools must be a list")
        names: list[str] = []
        for tool in tools:
            if not isinstance(tool, dict) or not isinstance(tool.get("name"), str):
                raise RpcProtocolError("Cua discovery contains malformed tool metadata")
            names.append(tool["name"])
        meta = result.get("_meta")
        server_name = None
        if isinstance(meta, dict):
            server_info = meta.get("io.modelcontextprotocol/serverInfo")
            if isinstance(server_info, dict) and isinstance(server_info.get("name"), str):
                server_name = server_info["name"]
        return CuaDiscovery(
            protocol_version=CUA_MCP_PROTOCOL_VERSION,
            supported_versions=tuple(str(item) for item in versions),
            server_name=server_name,
            tool_names=tuple(names),
            raw_capabilities=capabilities,
        )

    def close(self) -> None:
        peer = self.peer
        self.peer = None
        self.discovery = None
        if peer is not None:
            peer.close()
        elif self.process is not None:
            self.process.stop()
        self.process = None
