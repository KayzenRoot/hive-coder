from __future__ import annotations

import io
import json
import unittest

from hive_runtime.runtime_status import disconnected_snapshot
from hive_runtime.runtime_status_protocol import (
    MAX_REQUEST_BYTES,
    PROTOCOL_VERSION,
    REQUEST_OPERATION,
    encode_response,
    parse_request,
    serve_one,
)


class RuntimeStatusProtocolTests(unittest.TestCase):
    def test_parse_exact_request(self) -> None:
        request = parse_request(json.dumps({"protocol": PROTOCOL_VERSION, "requestId": "r-1", "op": REQUEST_OPERATION}))
        self.assertEqual(request.request_id, "r-1")

    def test_unknown_field_version_operation_and_bad_id_fail_closed(self) -> None:
        base = {"protocol": PROTOCOL_VERSION, "requestId": "r-1", "op": REQUEST_OPERATION}
        cases = [
            {**base, "extra": "no"},
            {**base, "protocol": "future"},
            {**base, "op": "provider.call"},
            {**base, "requestId": "../unsafe"},
        ]
        for payload in cases:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                parse_request(json.dumps(payload))

    def test_oversized_request_fails(self) -> None:
        with self.assertRaises(ValueError):
            parse_request("x" * (MAX_REQUEST_BYTES + 1))

    def test_response_contains_only_protocol_identity_and_validated_snapshot(self) -> None:
        raw = encode_response("r-2", disconnected_snapshot())
        parsed = json.loads(raw)
        self.assertEqual(set(parsed), {"protocol", "requestId", "ok", "snapshot"})
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["snapshot"]["runtime"]["state"], "DISCONNECTED")

    def test_one_shot_handler_emits_one_line_and_does_not_mutate(self) -> None:
        reader = io.StringIO(json.dumps({"protocol": PROTOCOL_VERSION, "requestId": "one", "op": REQUEST_OPERATION}) + "\n")
        writer = io.StringIO()
        calls = 0

        def factory():
            nonlocal calls
            calls += 1
            return disconnected_snapshot()

        serve_one(reader, writer, factory)
        self.assertEqual(calls, 1)
        self.assertEqual(len(writer.getvalue().splitlines()), 1)
        self.assertEqual(json.loads(writer.getvalue())["requestId"], "one")


if __name__ == "__main__":
    unittest.main()
