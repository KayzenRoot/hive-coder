from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from typing import Any, Callable

from .errors import ProcessExitedError, RpcProtocolError, RpcRemoteError, RpcTimeoutError
from .process import ManagedStdioProcess

NotificationHandler = Callable[[str, Any], None]
InboundRequestHandler = Callable[[str, Any], Any]


@dataclass
class _Pending:
    event: threading.Event
    result: Any = None
    error: BaseException | None = None


class JsonRpcPeer:
    """Strict newline-delimited JSON-RPC 2.0 peer over one managed stdio process."""

    def __init__(
        self,
        process: ManagedStdioProcess,
        *,
        notification_handler: NotificationHandler | None = None,
        inbound_request_handler: InboundRequestHandler | None = None,
        max_line_bytes: int = 1_048_576,
    ) -> None:
        self.process = process
        self.notification_handler = notification_handler
        self.inbound_request_handler = inbound_request_handler
        self.max_line_bytes = max_line_bytes
        self._next_id = 1
        self._pending: dict[int | str, _Pending] = {}
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._fatal: BaseException | None = None
        self._closed = False
        self._reader: threading.Thread | None = None

    def start(self) -> "JsonRpcPeer":
        self.process.ensure_running()
        if self._reader is not None:
            raise RpcProtocolError("JSON-RPC peer already started")
        self._reader = threading.Thread(target=self._read_loop, name=f"{self.process.spec.name}-jsonrpc", daemon=True)
        self._reader.start()
        return self

    @property
    def fatal_error(self) -> BaseException | None:
        return self._fatal

    def request(self, method: str, params: Any = None, *, timeout: float = 5.0) -> Any:
        if not method:
            raise ValueError("JSON-RPC method is required")
        self._raise_if_unavailable()
        with self._lock:
            request_id = self._next_id
            self._next_id += 1
            pending = _Pending(threading.Event())
            self._pending[request_id] = pending
        message: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        try:
            self._write(message)
        except BaseException:
            with self._lock:
                self._pending.pop(request_id, None)
            raise
        if not pending.event.wait(timeout):
            with self._lock:
                self._pending.pop(request_id, None)
            raise RpcTimeoutError(f"JSON-RPC request timed out: {method}")
        if pending.error is not None:
            raise pending.error
        return pending.result

    def notify(self, method: str, params: Any = None) -> None:
        if not method:
            raise ValueError("JSON-RPC method is required")
        self._raise_if_unavailable()
        message: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        self._write(message)

    def _write(self, message: dict[str, Any]) -> None:
        encoded = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
        if len(encoded.encode("utf-8")) > self.max_line_bytes:
            raise RpcProtocolError("outbound JSON-RPC message exceeds line limit")
        with self._write_lock:
            self.process.ensure_running()
            try:
                self.process.stdin.write(encoded + "\n")
                self.process.stdin.flush()
            except (OSError, UnicodeError) as exc:
                raise ProcessExitedError(f"failed writing to {self.process.spec.name}") from exc

    def _read_loop(self) -> None:
        try:
            while not self._closed:
                line = self.process.stdout.readline()
                if line == "":
                    if not self._closed:
                        self._fail(ProcessExitedError(f"{self.process.spec.name} stdout closed; code={self.process.returncode}"))
                    return
                if len(line.encode("utf-8")) > self.max_line_bytes:
                    self._fail(RpcProtocolError("inbound JSON-RPC line exceeds limit"))
                    return
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    self._fail(RpcProtocolError("malformed JSON-RPC payload"))
                    return
                try:
                    self._dispatch(message)
                except BaseException as exc:
                    self._fail(exc if isinstance(exc, RpcProtocolError) else RpcProtocolError(type(exc).__name__))
                    return
        except (OSError, UnicodeError) as exc:
            if not self._closed:
                self._fail(RpcProtocolError(f"JSON-RPC read failure: {type(exc).__name__}"))

    def _dispatch(self, message: Any) -> None:
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            raise RpcProtocolError("invalid JSON-RPC envelope")
        has_id = "id" in message
        has_method = isinstance(message.get("method"), str)
        if has_method:
            if has_id:
                self._handle_inbound_request(message)
            else:
                handler = self.notification_handler
                if handler is not None:
                    handler(message["method"], message.get("params"))
            return
        if not has_id:
            raise RpcProtocolError("JSON-RPC response missing id")
        if ("result" in message) == ("error" in message):
            raise RpcProtocolError("JSON-RPC response must contain exactly one of result/error")
        request_id = message["id"]
        with self._lock:
            pending = self._pending.pop(request_id, None)
        if pending is None:
            raise RpcProtocolError(f"response for unknown request id: {request_id!r}")
        if "error" in message:
            error = message["error"]
            if not isinstance(error, dict) or not isinstance(error.get("code"), int) or not isinstance(error.get("message"), str):
                pending.error = RpcProtocolError("invalid JSON-RPC error object")
            else:
                pending.error = RpcRemoteError(error["code"], error["message"], error.get("data"))
        else:
            pending.result = message["result"]
        pending.event.set()

    def _handle_inbound_request(self, message: dict[str, Any]) -> None:
        request_id = message["id"]
        method = message["method"]
        handler = self.inbound_request_handler
        if handler is None:
            self._write({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Hive client denies unsupported inbound request: {method}"},
            })
            return
        try:
            result = handler(method, message.get("params"))
        except Exception as exc:
            self._write({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32000, "message": f"Hive inbound handler rejected request: {type(exc).__name__}"},
            })
            return
        self._write({"jsonrpc": "2.0", "id": request_id, "result": result})

    def _raise_if_unavailable(self) -> None:
        if self._closed:
            raise ProcessExitedError("JSON-RPC peer is closed")
        if self._fatal is not None:
            raise self._fatal
        self.process.ensure_running()

    def _fail(self, error: BaseException) -> None:
        if self._fatal is None:
            self._fatal = error
        with self._lock:
            pending = list(self._pending.values())
            self._pending.clear()
        for item in pending:
            item.error = self._fatal
            item.event.set()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._fail(ProcessExitedError("JSON-RPC peer closed"))
        self.process.stop()
        reader = self._reader
        if reader is not None and reader.is_alive() and reader is not threading.current_thread():
            reader.join(timeout=0.2)
