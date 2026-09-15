from __future__ import annotations

import io
import json
import unittest

from hive_runtime.runtime_status import MAX_STATUS_BYTES, disconnected_snapshot
from hive_runtime.runtime_status_protocol import (
    MAX_REQUEST_BYTES,
    MAX_RESPONSE_BYTES,
    PROTOCOL_VERSION,
    REQUEST_OPERATION,
    encode_request,
    encode_response,
    parse_request,
    parse_response,
    serve_one,
)


class RuntimeStatusProtocolTests(unittest.TestCase):
    def test_canonical_request_round_trip(self) -> None:
        raw = encode_request("r-1")
        self.assertEqual(
            raw,
            '{"op":"status.snapshot","protocol":"hive-runtime-status-ipc-v1","requestId":"r-1"}',
        )
        request = parse_request(raw)
        self.assertEqual(request.request_id, "r-1")
        self.assertEqual(request.operation, REQUEST_OPERATION)
        self.assertEqual(request.protocol, PROTOCOL_VERSION)

    def test_noncanonical_duplicate_unknown_version_operation_and_bad_id_fail_closed(self) -> None:
        canonical = encode_request("r-1")
        cases = [
            json.dumps({"protocol": PROTOCOL_VERSION, "requestId": "r-1", "op": REQUEST_OPERATION}),
            canonical.replace('{"op":', '{"op":"status.snapshot","op":', 1),
            canonical[:-1] + ',"extra":"no"}',
            canonical.replace(PROTOCOL_VERSION, "future"),
            canonical.replace(REQUEST_OPERATION, "provider.call"),
            encode_request("r-1").replace('"r-1"', '"../unsafe"'),
        ]
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                parse_request(payload)

    def test_oversized_request_fails(self) -> None:
        with self.assertRaises(ValueError):
            parse_request("x" * (MAX_REQUEST_BYTES + 1))

    def test_response_round_trip_revalidates_canonical_snapshot(self) -> None:
        raw = encode_response("r-2", disconnected_snapshot())
        response = parse_response(raw)
        self.assertEqual(response.request_id, "r-2")
        self.assertEqual(response.snapshot.runtime.state.value, "DISCONNECTED")
        parsed = json.loads(raw)
        self.assertEqual(set(parsed), {"ok", "protocol", "requestId", "snapshot"})
        self.assertEqual(parsed["snapshot"]["runtime"]["provenance"], "hive-runtime-status")
        self.assertEqual(parsed["snapshot"]["permission"]["provenance"], "hive-permission-control-plane")

    def test_response_duplicate_key_and_noncanonical_wire_fail_closed(self) -> None:
        raw = encode_response("r-3", disconnected_snapshot())
        duplicate = raw.replace('{"ok":true,', '{"ok":true,"ok":true,', 1)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_response(duplicate)
        with self.assertRaisesRegex(ValueError, "canonical"):
            parse_response(" " + raw)

    def test_response_ceiling_is_snapshot_ceiling_plus_bounded_envelope(self) -> None:
        self.assertEqual(MAX_RESPONSE_BYTES, MAX_STATUS_BYTES + 256)
        self.assertLessEqual(len(encode_response("x" * 64, disconnected_snapshot()).encode("utf-8")), MAX_RESPONSE_BYTES)

    def test_one_shot_handler_emits_exactly_one_line_from_prebuilt_snapshot(self) -> None:
        first = encode_request("one")
        second = encode_request("two")
        reader = io.StringIO(first + "\n" + second + "\n")
        writer = io.StringIO()
        serve_one(reader, writer, disconnected_snapshot())
        lines = writer.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(parse_response(lines[0]).request_id, "one")
        self.assertEqual(reader.readline().rstrip("\n"), second)

    def test_one_shot_handler_accepts_crlf_but_requires_line_termination(self) -> None:
        raw = encode_request("line")
        writer = io.StringIO()
        serve_one(io.StringIO(raw + "\r\n"), writer, disconnected_snapshot())
        self.assertEqual(parse_response(writer.getvalue().rstrip("\n")).request_id, "line")
        with self.assertRaisesRegex(ValueError, "newline terminated"):
            serve_one(io.StringIO(raw), io.StringIO(), disconnected_snapshot())

    def test_one_shot_handler_rejects_oversized_line_before_snapshot_use(self) -> None:
        oversized = "x" * (MAX_REQUEST_BYTES + 2) + "\n"
        with self.assertRaises(ValueError):
            serve_one(io.StringIO(oversized), io.StringIO(), disconnected_snapshot())


if __name__ == "__main__":
    unittest.main()
