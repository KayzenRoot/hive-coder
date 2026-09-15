from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .control_plane import PermissionControlPlane
from .cua import CuaAdapter, CuaDiscovery, CuaTool
from .cua_executor import GatedCuaActionExecutor, PostActionVerifier
from .errors import AdapterStateError, AuthorizationDenied, RpcProtocolError


@dataclass(frozen=True)
class WindowsTarget:
    application: str
    window_id: str
    pid: int

    def canonical(self) -> dict[str, str]:
        return {"application": self.application.lower(), "window_id": self.window_id}


class WindowsForegroundTargetResolver:
    """Trusted foreground identity from Win32, never from model/task text."""

    def __call__(self, _request: Any = None) -> Mapping[str, str]:
        return self.resolve().canonical()

    @staticmethod
    def resolve() -> WindowsTarget:
        if sys.platform != "win32":
            raise AdapterStateError("Windows target resolver requires win32")
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        user32.GetForegroundWindow.argtypes = []
        user32.GetForegroundWindow.restype = wintypes.HWND
        user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL

        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            raise AuthorizationDenied("no_foreground_window")
        pid = wintypes.DWORD(0)
        if not user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)) or not pid.value:
            raise AuthorizationDenied("foreground_pid_unavailable")
        handle = kernel32.OpenProcess(0x1000, False, pid.value)
        if not handle:
            raise AuthorizationDenied("foreground_process_unavailable")
        try:
            size = wintypes.DWORD(32768)
            buf = ctypes.create_unicode_buffer(size.value)
            if not kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                raise AuthorizationDenied("foreground_image_unavailable")
            application = Path(buf.value).name
        finally:
            kernel32.CloseHandle(handle)
        return WindowsTarget(application=application, window_id=f"hwnd:{int(hwnd):x}", pid=int(pid.value))


@dataclass(frozen=True)
class ResolvedCuaContract:
    click_tool: CuaTool
    type_tool: CuaTool

    def bindings(self) -> dict[str, str]:
        return {"pointer.click": self.click_tool.name, "keyboard.type_text": self.type_tool.name}


class CuaContractResolver:
    CLICK_CAPS = frozenset(("input.pointer.click.left", "input.pointer.click"))
    TYPE_CAP = "input.keyboard.type"

    @classmethod
    def resolve(cls, discovery: CuaDiscovery) -> ResolvedCuaContract:
        click = cls._unique(discovery.tools, lambda t: bool(cls.CLICK_CAPS.intersection(t.capabilities)), "pointer click")
        type_tool = cls._unique(discovery.tools, lambda t: cls.TYPE_CAP in t.capabilities, "text input")
        cls._require_properties(click, ("x", "y"))
        cls._require_properties(type_tool, ("text",))
        if click.annotations.get("readOnlyHint") is True or type_tool.annotations.get("readOnlyHint") is True:
            raise RpcProtocolError("Cua mutation tool incorrectly advertises read-only")
        return ResolvedCuaContract(click, type_tool)

    @staticmethod
    def _unique(tools, predicate, label: str) -> CuaTool:
        matches = [tool for tool in tools if predicate(tool)]
        if len(matches) != 1:
            raise RpcProtocolError(f"Cua {label} contract must resolve uniquely")
        return matches[0]

    @staticmethod
    def _require_properties(tool: CuaTool, required: tuple[str, ...]) -> None:
        props = tool.input_schema.get("properties")
        if not isinstance(props, dict) or any(name not in props for name in required):
            raise RpcProtocolError(f"Cua tool {tool.name} lacks required Hive argument properties")


class RealCuaWindowsHarness:
    """Explicitly opted-in real-Cua connector with trusted sandbox identity."""

    def __init__(self, *, binary: str, sandbox_application: str) -> None:
        if os.environ.get("HIVE_ENABLE_REAL_CUA") != "1":
            raise AuthorizationDenied("real_cua_harness_requires_explicit_opt_in")
        if not binary or not sandbox_application:
            raise AuthorizationDenied("real_cua_harness_requires_binary_and_sandbox")
        self.binary = binary
        self.sandbox_application = sandbox_application.lower()
        self.adapter = CuaAdapter.from_binary(binary)
        self.contract: ResolvedCuaContract | None = None
        self.target_resolver = WindowsForegroundTargetResolver()

    def start(self) -> ResolvedCuaContract:
        discovery = self.adapter.start()
        self.contract = CuaContractResolver.resolve(discovery)
        self._require_safe_foreground()
        return self.contract

    def _require_safe_foreground(self) -> WindowsTarget:
        target = self.target_resolver.resolve()
        if target.application.lower() != self.sandbox_application:
            self.close()
            raise AuthorizationDenied("foreground_application_is_not_safe_sandbox")
        return target

    def build_executor(self, control_plane: PermissionControlPlane, *, post_action_verifier: PostActionVerifier | None = None) -> GatedCuaActionExecutor:
        if self.contract is None or self.adapter.peer is None:
            raise AdapterStateError("real Cua harness must be started before executor wiring")
        self._require_safe_foreground()
        executor = GatedCuaActionExecutor(control_plane=control_plane, peer=self.adapter.peer, live_target_resolver=self.target_resolver, post_action_verifier=post_action_verifier, tool_bindings=self.contract.bindings())
        return executor

    def close(self) -> None:
        self.adapter.close()
