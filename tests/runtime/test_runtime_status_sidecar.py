from __future__ import annotations

import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from hive_runtime.process import ManagedStdioProcess, ProcessSpec, safe_child_environment
from hive_runtime.runtime_status_protocol import (
    MAX_REQUEST_BYTES,
    PROTOCOL_VERSION,
    REQUEST_OPERATION,
    encode_request,
    parse_response,
)

ROOT = Path(__file__).resolve().parents[2]
SIDECAR = ROOT / "tools" / "runtime" / "status_sidecar.py"
MODE = "--stdio-status-v1"
EXIT_USAGE = 64
EXIT_PROTOCOL = 65


def sidecar_spec(*args: str) -> ProcessSpec:
    return ProcessSpec((sys.executable, "-u", str(SIDECAR), *args), name="runtime-status-sidecar")


def wait_for_exit(process: ManagedStdioProcess, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while process.is_running and time.monotonic() < deadline:
        time.sleep(0.01)
    return not process.is_running


class RuntimeStatusSidecarTests(unittest.TestCase):
    def test_fixed_mode_is_process_level_one_shot_with_canonical_roundtrip(self) -> None:
        process = ManagedStdioProcess(sidecar_spec(MODE)).start()
        try:
            process.stdin.write(encode_request("process-1") + "\n")
            process.stdin.write(encode_request("must-not-run") + "\n")
            process.stdin.flush()
            line = process.stdout.readline()
            self.assertTrue(line.endswith("\n"))
            response = parse_response(line[:-1])
            parsed = json.loads(line)
            self.assertEqual(response.request_id, "process-1")
            self.assertEqual(parsed["snapshot"]["runtime"]["state"], "DISCONNECTED")
            self.assertTrue(wait_for_exit(process))
            self.assertEqual(process.returncode, 0)
            self.assertEqual(process.stdout.read(), "")
        finally:
            process.stop()
        self.assertEqual(process.stderr_tail(), ())

    def test_missing_unknown_and_extra_modes_fail_closed(self) -> None:
        for args in ((), ("--not-a-mode",), (MODE, "extra")):
            with self.subTest(args=args):
                process = ManagedStdioProcess(sidecar_spec(*args)).start()
                try:
                    self.assertTrue(wait_for_exit(process))
                    self.assertEqual(process.returncode, EXIT_USAGE)
                    self.assertEqual(process.stdout.read(), "")
                finally:
                    process.stop()
                self.assertEqual(process.stderr_tail(), ())

    def test_invalid_protocol_requests_fail_closed_at_process_boundary(self) -> None:
        canonical = encode_request("rejected")
        noncanonical = json.dumps(
            {"protocol": PROTOCOL_VERSION, "requestId": "rejected", "op": REQUEST_OPERATION},
            separators=(",", ":"),
        )
        duplicate = canonical.replace('{"op":', '{"op":"status.snapshot","op":', 1)
        future_protocol = canonical.replace(PROTOCOL_VERSION, "future")
        unsupported_operation = canonical.replace(REQUEST_OPERATION, "provider.call")
        cases = (
            "not-json",
            noncanonical,
            duplicate,
            future_protocol,
            unsupported_operation,
            "x" * (MAX_REQUEST_BYTES + 1),
        )
        for payload in cases:
            with self.subTest(payload=payload[:48]):
                process = ManagedStdioProcess(sidecar_spec(MODE)).start()
                try:
                    process.stdin.write(payload + "\n")
                    process.stdin.flush()
                    self.assertTrue(wait_for_exit(process))
                    self.assertEqual(process.returncode, EXIT_PROTOCOL)
                    self.assertEqual(process.stdout.read(), "")
                finally:
                    process.stop()
                self.assertEqual(process.stderr_tail(), ())

    def test_missing_newline_fails_closed_after_eof(self) -> None:
        process = ManagedStdioProcess(sidecar_spec(MODE)).start()
        try:
            process.stdin.write(encode_request("missing-newline"))
            process.stdin.flush()
            process.stdin.close()
            self.assertTrue(wait_for_exit(process))
            self.assertEqual(process.returncode, EXIT_PROTOCOL)
            self.assertEqual(process.stdout.read(), "")
        finally:
            process.stop()
        self.assertEqual(process.stderr_tail(), ())

    def test_ambient_secret_is_excluded_from_child_environment_and_output(self) -> None:
        secret = "never-export-this"
        with patch.dict(os.environ, {"OPENAI_API_KEY": secret}, clear=False):
            child_env = safe_child_environment()
            self.assertNotIn("OPENAI_API_KEY", child_env)
            process = ManagedStdioProcess(sidecar_spec(MODE)).start()

        try:
            process.stdin.write(encode_request("secret-test") + "\n")
            process.stdin.flush()
            line = process.stdout.readline()
            self.assertTrue(wait_for_exit(process))
            self.assertEqual(process.returncode, 0)
            self.assertNotIn(secret, line)
            self.assertNotIn("OPENAI_API_KEY", line)
            self.assertEqual(process.stdout.read(), "")
            parse_response(line[:-1])
        finally:
            process.stop()
        self.assertEqual(process.stderr_tail(), ())


if __name__ == "__main__":
    unittest.main()
