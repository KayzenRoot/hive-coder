from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import AdapterStateError, RpcProtocolError
from .foundation_lock import expected_foundation_version
from .jsonrpc import JsonRpcPeer
from .process import ManagedStdioProcess, ProcessSpec
from .preflight import verify_binary_version

ACP_PROTOCOL_VERSION = 1


@dataclass(frozen=True)
class InterpreterIdentity:
    protocol_version: int
    name: str
    title: str | None
    version: str | None
    capabilities: Mapping[str, Any]


class InterpreterAdapter:
    """Hive-owned ACP v1 bridge. No provider prompt is executed by startup."""

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
        self.identity: InterpreterIdentity | None = None
        self._sessions: set[str] = set()
        self._updates: list[Any] = []
        self._updates_lock = threading.Lock()

    @classmethod
    def from_binary(cls, binary: str, **kwargs) -> "InterpreterAdapter":
        return cls((binary, "acp"), preflight_binary=binary, foundation_key="openInterpreter", **kwargs)

    def start(self) -> InterpreterIdentity:
        if self.process is not None:
            raise AdapterStateError("Interpreter adapter already started")
        if self.preflight_binary is not None:
            if self.foundation_key is None:
                raise AdapterStateError("production preflight requires a foundation key")
            verify_binary_version(self.preflight_binary, expected_foundation_version(self.foundation_key))
        process = ManagedStdioProcess(ProcessSpec(self.command, cwd=self.cwd, env_overrides=self.env_overrides, name="open-interpreter-acp")).start()
        peer = JsonRpcPeer(process, notification_handler=self._on_notification).start()
        self.process = process
        self.peer = peer
        try:
            result = peer.request(
                "initialize",
                {
                    "protocolVersion": ACP_PROTOCOL_VERSION,
                    "clientCapabilities": {},
                    "clientInfo": {"name": "hive-coder", "title": "Hive Coder", "version": "0.0.0"},
                },
                timeout=self.timeout,
            )
            identity = self._validate_initialize(result)
            self.identity = identity
            return identity
        except BaseException:
            self.close()
            raise

    def _validate_initialize(self, result: Any) -> InterpreterIdentity:
        if not isinstance(result, dict):
            raise RpcProtocolError("ACP initialize result must be an object")
        if result.get("protocolVersion") != ACP_PROTOCOL_VERSION:
            raise RpcProtocolError("ACP protocol version mismatch")
        info = result.get("agentInfo")
        capabilities = result.get("agentCapabilities")
        if not isinstance(info, dict) or not isinstance(info.get("name"), str):
            raise RpcProtocolError("ACP initialize missing agent identity")
        if not isinstance(capabilities, dict):
            raise RpcProtocolError("ACP initialize missing agent capabilities")
        return InterpreterIdentity(
            protocol_version=ACP_PROTOCOL_VERSION,
            name=info["name"],
            title=info.get("title") if isinstance(info.get("title"), str) else None,
            version=info.get("version") if isinstance(info.get("version"), str) else None,
            capabilities=capabilities,
        )

    def create_session(self, cwd: str | os.PathLike[str]) -> str:
        peer = self._require_peer()
        resolved = str(Path(cwd).expanduser().resolve())
        result = peer.request("session/new", {"cwd": resolved, "mcpServers": []}, timeout=self.timeout)
        if not isinstance(result, dict) or not isinstance(result.get("sessionId"), str) or not result["sessionId"]:
            raise RpcProtocolError("ACP session/new missing sessionId")
        session_id = result["sessionId"]
        self._sessions.add(session_id)
        return session_id

    def cancel(self, session_id: str) -> None:
        self._require_session(session_id)
        self._require_peer().notify("session/cancel", {"sessionId": session_id})

    def close_session(self, session_id: str) -> None:
        self._require_session(session_id)
        self._require_peer().request("session/close", {"sessionId": session_id}, timeout=self.timeout)
        self._sessions.discard(session_id)

    def updates(self) -> tuple[Any, ...]:
        with self._updates_lock:
            return tuple(self._updates)

    def _on_notification(self, method: str, params: Any) -> None:
        if method == "session/update":
            with self._updates_lock:
                self._updates.append(params)

    def _require_session(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise AdapterStateError(f"unknown Interpreter session: {session_id}")

    def _require_peer(self) -> JsonRpcPeer:
        if self.peer is None or self.identity is None:
            raise AdapterStateError("Interpreter adapter is not ready")
        return self.peer

    def close(self) -> None:
        peer = self.peer
        self.peer = None
        self.identity = None
        self._sessions.clear()
        if peer is not None:
            peer.close()
        elif self.process is not None:
            self.process.stop()
        self.process = None
