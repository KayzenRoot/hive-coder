"""Strict one-shot IPC contract for non-authoritative Hive runtime status."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Callable, TextIO

from .runtime_status import RuntimeStatusSnapshot

PROTOCOL_VERSION = "hive-runtime-status-ipc-v1"
REQUEST_OPERATION = "status.snapshot"
MAX_REQUEST_BYTES = 512
MAX_RESPONSE_BYTES = 40_000
_REQUEST_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


@dataclass(frozen=True)
class StatusRequest:
    request_id: str
    operation: str = REQUEST_OPERATION
    protocol: str = PROTOCOL_VERSION

    def validated(self) -> "StatusRequest":
        if self.protocol != PROTOCOL_VERSION:
            raise ValueError("unsupported runtime status protocol")
        if self.operation != REQUEST_OPERATION:
            raise ValueError("unsupported runtime status operation")
        if not isinstance(self.request_id, str) or not _REQUEST_ID.fullmatch(self.request_id):
            raise ValueError("invalid runtime status request id")
        return self


def _utf8_bytes(raw: str | bytes, *, ceiling: int) -> bytes:
    if isinstance(raw, str):
        data = raw.encode("utf-8")
    elif isinstance(raw, bytes):
        data = raw
    else:
        raise ValueError("runtime status message must be text or bytes")
    if not data or len(data) > ceiling:
        raise ValueError("runtime status message exceeds byte bounds")
    return data


def parse_request(raw: str | bytes) -> StatusRequest:
    data = _utf8_bytes(raw, ceiling=MAX_REQUEST_BYTES)
    try:
        decoded = data.decode("utf-8")
        value = json.loads(decoded)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid runtime status request JSON") from exc
    if not isinstance(value, dict) or set(value) != {"protocol", "requestId", "op"}:
        raise ValueError("invalid runtime status request shape")
    if not all(isinstance(value[key], str) for key in value):
        raise ValueError("runtime status request fields must be strings")
    return StatusRequest(value["requestId"], value["op"], value["protocol"]).validated()


def encode_response(request_id: str, snapshot: RuntimeStatusSnapshot) -> str:
    request = StatusRequest(request_id).validated()
    snapshot.validated()
    envelope = {
        "protocol": PROTOCOL_VERSION,
        "requestId": request.request_id,
        "ok": True,
        "snapshot": snapshot.to_dict_unchecked(),
    }
    encoded = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ValueError("runtime status response exceeds byte ceiling")
    return encoded


def serve_one(reader: TextIO, writer: TextIO, snapshot_factory: Callable[[], RuntimeStatusSnapshot]) -> None:
    """Handle exactly one bounded status request without external side effects."""
    raw = reader.readline(MAX_REQUEST_BYTES + 2)
    if not raw or len(raw.encode("utf-8")) > MAX_REQUEST_BYTES + 1:
        raise ValueError("runtime status request line is missing or oversized")
    request = parse_request(raw.rstrip("\r\n"))
    response = encode_response(request.request_id, snapshot_factory())
    writer.write(response + "\n")
    writer.flush()
