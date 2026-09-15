from __future__ import annotations

import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from hive_runtime.process import ManagedStdioProcess, ProcessSpec
from hive_runtime.runtime_status_protocol import PROTOCOL_VERSION, REQUEST_OPERATION


ROOT = Path(__file__).resolve().parents[2]
SIDECAR = ROOT / "tools" / "runtime" / "status_sidecar.py"


def sidecar_spec(*args: str) -> ProcessSpec:
    return ProcessSpec((sys.executable, "-u", str(SIDECAR), *args), name="runtime-status-sidecar")


class RuntimeStatusSidecarTests(unittest.TestCase):
    def test_fixed_mode_one_shot_roundtrip(self) -> None:
        process = ManagedStdioProcess(sidecar_spec("--stdio-status-v1")).start()
        try:
            request = {"protocol": PROTOCOL_VERSION, "requestId": "process-1", "op": REQUEST_OPERATION}
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            line = process.stdout.readline()
            parsed = json.loads(line)
            self.assertEqual(parsed["requestId"], "process-1")
            self.assertEqual(parsed["snapshot"]["runtime"]["state"], "DISCONNECTED")
            deadline = time.time() + 2
            while process.is_running and time.time() < deadline:
                time.sleep(0.01)
            self.assertFalse(process.is_running)
            self.assertEqual(process.returncode, 0)
        finally:
            process.stop()

    def test_unknown_mode_exits_without_protocol_output(self) -> None:
        process = ManagedStdioProcess(sidecar_spec("--not-a-mode")).start()
        try:
            deadline = time.time() + 2
            while process.is_running and time.time() < deadline:
                time.sleep(0.01)
            self.assertFalse(process.is_running)
            self.assertEqual(process.returncode, 64)
            self.assertEqual(process.stdout.read(), "")
        finally:
            process.stop()

    def test_malformed_request_exits_nonzero_without_snapshot(self) -> None:
        process = ManagedStdioProcess(sidecar_spec("--stdio-status-v1")).start()
        try:
            process.stdin.write("not-json\n")
            process.stdin.flush()
            deadline = time.time() + 2
            while process.is_running and time.time() < deadline:
                time.sleep(0.01)
            self.assertFalse(process.is_running)
            self.assertEqual(process.returncode, 65)
            self.assertEqual(process.stdout.read(), "")
        finally:
            process.stop()

    def test_ambient_secret_is_not_exported(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "never-export-this"}, clear=False):
            process = ManagedStdioProcess(sidecar_spec("--stdio-status-v1")).start()
        try:
            request = {"protocol": PROTOCOL_VERSION, "requestId": "secret-test", "op": REQUEST_OPERATION}
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            line = process.stdout.readline()
            self.assertNotIn("never-export-this", line)
            self.assertNotIn("OPENAI_API_KEY", line)
        finally:
            process.stop()


if __name__ == "__main__":
    unittest.main()
