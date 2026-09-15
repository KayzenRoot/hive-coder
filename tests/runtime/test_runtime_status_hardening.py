from __future__ import annotations

import json
import unittest

from hive_runtime.runtime_status import (
    PERMISSION_CONTROL_PROVENANCE,
    PROVIDER_CATALOG_PROVENANCE,
    RUNTIME_STATUS_PROVENANCE,
    PermissionStatusSummary,
    ProviderStatus,
    RuntimeStatusSnapshot,
    StatusSignal,
    StatusState,
    disconnected_snapshot,
)


class RuntimeStatusHardeningTests(unittest.TestCase):
    def test_typed_objects_reject_string_states_before_serialization(self) -> None:
        with self.assertRaisesRegex(ValueError, "StatusState"):
            StatusSignal("READY", RUNTIME_STATUS_PROVENANCE, "not typed").validated()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "StatusState"):
            ProviderStatus("fixture", ("m1",), "READY", PROVIDER_CATALOG_PROVENANCE).validated()  # type: ignore[arg-type]
        with self.assertRaisesRegex(ValueError, "StatusState"):
            PermissionStatusSummary("READY", 1, 1, 0, PERMISSION_CONTROL_PROVENANCE).validated()  # type: ignore[arg-type]

    def test_decoder_rejects_noncanonical_provenance(self) -> None:
        raw = json.loads(disconnected_snapshot().to_json())
        raw["runtime"]["provenance"] = "caller-controlled-label"
        with self.assertRaisesRegex(ValueError, "runtime.provenance"):
            RuntimeStatusSnapshot.from_json(json.dumps(raw))

        raw = json.loads(disconnected_snapshot().to_json())
        raw["permission"]["provenance"] = "caller-controlled-label"
        with self.assertRaisesRegex(ValueError, "permission.provenance"):
            RuntimeStatusSnapshot.from_json(json.dumps(raw))


if __name__ == "__main__":
    unittest.main()
