"""Strict canonical one-shot IPC contract for non-authoritative Hive runtime status."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TextIO

from .runtime_status import MAX_STATUS_BYTES, RuntimeStatusSnapshot

PROTOCOL_VERSION = "hive-runtime-status-ipc-v1"
REQUEST_OPERATION = "status.snapshot"
MAX_REQUEST_BYTES = 512
MAX_RESPONSE_BYTES = MAX_STATUS_BYTES + 256
_REQUEST_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


def _strict_object_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate runtime status IPC object key")
        result[key] = value
    return result


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _utf8_bytes(raw: str | bytes, *, ceiling: int) -> bytes:
    if isinstance(raw, str):
        data = raw.encode("utf-8")
    elif isinstance(raw, bytes):
        data = raw
    else:
        raise ValueError("runtime status IPC message must be text or bytes")
    if not data or len(data) > ceiling:
        raise ValueError("runtime status IPC message exceeds byte bounds")
    return data


def _decode_json(raw: str | bytes, *, ceiling: int, label: str) -> tuple[str, object]:
    data = _utf8_bytes(raw, ceiling=ceiling)
    try:
        decoded = data.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=_strict_object_pairs)
    except UnicodeError as exc:
        raise ValueError(f"invalid {label} UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid {label} JSON") from exc
    return decoded, value


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

    def to_dict(self) -> dict[str, str]:
        self.validated()
        return {"protocol": self.protocol, "requestId": self.request_id, "op": self.operation}


@dataclass(frozen=True)
class StatusResponse:
    request_id: str
    snapshot: RuntimeStatusSnapshot
    ok: bool = True
    protocol: str = PROTOCOL_VERSION

    def validated(self) -> "StatusResponse":
        StatusRequest(self.request_id).validated()
        if self.protocol != PROTOCOL_VERSION or self.ok is not True:
            raise ValueError("unsupported runtime status response envelope")
        if not isinstance(self.snapshot, RuntimeStatusSnapshot):
            raise ValueError("runtime status response requires a RuntimeStatusSnapshot")
        self.snapshot.validated()
        return self

    def to_dict(self) -> dict[str, object]:
        self.validated()
        return {
            "protocol": self.protocol,
            "requestId": self.request_id,
            "ok": True,
            "snapshot": self.snapshot.to_dict_unchecked(),
        }


def encode_request(request_id: str) -> str:
    return _canonical_json(StatusRequest(request_id).to_dict())


def parse_request(raw: str | bytes) -> StatusRequest:
    decoded, value = _decode_json(raw, ceiling=MAX_REQUEST_BYTES, label="runtime status request")
    if not isinstance(value, dict) or set(value) != {"protocol", "requestId", "op"}:
        raise ValueError("invalid runtime status request shape")
    if not all(isinstance(value[key], str) for key in value):
        raise ValueError("runtime status request fields must be strings")
    request = StatusRequest(value["requestId"], value["op"], value["protocol"]).validated()
    if decoded != _canonical_json(request.to_dict()):
        raise ValueError("runtime status request must use canonical JSON encoding")
    return request


def encode_response(request_id: str, snapshot: RuntimeStatusSnapshot) -> str:
    response = StatusResponse(request_id, snapshot).validated()
    encoded = _canonical_json(response.to_dict())
    if len(encoded.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ValueError("runtime status response exceeds byte ceiling")
    return encoded


def parse_response(raw: str | bytes) -> StatusResponse:
    decoded, value = _decode_json(raw, ceiling=MAX_RESPONSE_BYTES, label="runtime status response")
    if not isinstance(value, dict) or set(value) != {"protocol", "requestId", "ok", "snapshot"}:
        raise ValueError("invalid runtime status response shape")
    if value["protocol"] != PROTOCOL_VERSION or value["ok"] is not True:
        raise ValueError("unsupported runtime status response envelope")
    if not isinstance(value["requestId"], str) or not _REQUEST_ID.fullmatch(value["requestId"]):
        raise ValueError("invalid runtime status request id")
    snapshot = RuntimeStatusSnapshot.from_dict(value["snapshot"])
    response = StatusResponse(value["requestId"], snapshot).validated()
    if decoded != _canonical_json(response.to_dict()):
        raise ValueError("runtime status response must use canonical JSON encoding")
    return response


def serve_one(reader: TextIO, writer: TextIO, snapshot: RuntimeStatusSnapshot) -> None:
    """Handle exactly one line-framed request against a prebuilt presentation snapshot."""
    raw = reader.readline(MAX_REQUEST_BYTES + 3)
    if not raw:
        raise ValueError("runtime status request line is missing")
    if not raw.endswith("\n"):
        raise ValueError("runtime status request line must be newline terminated and bounded")
    line = raw[:-1]
    if line.endswith("\r"):
        line = line[:-1]
    if not line or len(line.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise ValueError("runtime status request line is missing or oversized")
    request = parse_request(line)
    response = encode_response(request.request_id, snapshot)
    writer.write(response + "\n")
    writer.flush()
