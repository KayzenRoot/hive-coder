from __future__ import annotations

import contextlib
import io
import json
import runpy
import unittest
from pathlib import Path

from hive_runtime.agent_tasks import NodeStatus, TaskBudget, TaskSnapshot, TaskStatus
from hive_runtime.intelligence.capabilities import CapabilityRequest, ModelCapabilityRegistry
from hive_runtime.providers import CapabilityProbeResult, ProviderCatalog, ProviderModel
from hive_runtime.runtime_status import (
    MAX_MODELS_PER_PROVIDER,
    MAX_PROVIDERS,
    PERMISSION_CONTROL_PROVENANCE,
    PROVIDER_CATALOG_PROVENANCE,
    RUNTIME_STATUS_PROVENANCE,
    TASK_RUNTIME_PROVENANCE,
    PermissionStatusSummary,
    ProviderStatus,
    RuntimeStatusSnapshot,
    StatusSignal,
    StatusState,
    TaskStatusSummary,
    decode_status_fail_closed,
    disconnected_snapshot,
    encode_status_fail_closed,
    reject_secret_like_mapping,
    summarize_provider_catalog,
    summarize_task,
    unobserved_permission,
)


class FakeProvider:
    provider_id = "fixture"

    def __init__(self, models: tuple[ProviderModel, ...]) -> None:
        self._models = models

    def list_models(self):
        return self._models

    def probe(self, model_id: str):
        return (CapabilityProbeResult("text", "fixture"),)


class RuntimeStatusContractTests(unittest.TestCase):
    def test_disconnected_snapshot_is_truthful_non_authoritative_and_attributed(self) -> None:
        raw = disconnected_snapshot().to_json()
        parsed = json.loads(raw)
        self.assertEqual(parsed["runtime"]["state"], "DISCONNECTED")
        self.assertEqual(parsed["runtime"]["provenance"], RUNTIME_STATUS_PROVENANCE)
        self.assertEqual(parsed["permission"]["state"], "DISCONNECTED")
        self.assertEqual(parsed["permission"]["provenance"], PERMISSION_CONTROL_PROVENANCE)
        self.assertIsNone(parsed["permission"]["policyEpoch"])
        self.assertEqual(parsed["providers"], [])
        self.assertIsNone(parsed["task"])
        for forbidden in ("permit", "credential", "password", "approvalToken", "prompt", "modelOutput"):
            self.assertNotIn(forbidden, raw)

    def test_ready_provider_requires_concrete_model_observation_and_provenance(self) -> None:
        with self.assertRaises(ValueError):
            ProviderStatus("fixture", (), StatusState.READY, PROVIDER_CATALOG_PROVENANCE).validated()
        with self.assertRaises(ValueError):
            ProviderStatus("fixture", ("model-a",), StatusState.READY, " ").validated()
        observed = ProviderStatus(
            "fixture",
            ("model-a",),
            StatusState.READY,
            PROVIDER_CATALOG_PROVENANCE,
        ).validated()
        self.assertEqual(observed.model_ids, ("model-a",))

    def test_empty_provider_catalog_is_unknown_not_ready(self) -> None:
        registry = ModelCapabilityRegistry()
        catalog = ProviderCatalog(registry, lambda provider, model, probe: False)
        result = summarize_provider_catalog(catalog, ("fixture",))
        self.assertEqual(result[0].state, StatusState.UNKNOWN)
        self.assertEqual(result[0].model_ids, ())
        self.assertEqual(result[0].provenance, PROVIDER_CATALOG_PROVENANCE)

    def test_observed_provider_catalog_is_bounded_and_does_not_verify_by_name(self) -> None:
        registry = ModelCapabilityRegistry()
        catalog = ProviderCatalog(registry, lambda provider, model, probe: False)
        catalog.refresh(FakeProvider((ProviderModel("m1", "Model One"),)))
        result = summarize_provider_catalog(catalog, ("fixture",))
        self.assertEqual(
            result,
            (ProviderStatus("fixture", ("m1",), StatusState.READY, PROVIDER_CATALOG_PROVENANCE),),
        )
        profile = registry.get("fixture", "m1")
        self.assertEqual(profile.model_id, "m1")
        self.assertFalse(registry.negotiate("fixture", "m1", CapabilityRequest(frozenset({"text"}))).allowed)

    def test_task_summary_exposes_only_bounded_attributed_progress(self) -> None:
        source = TaskSnapshot(
            task_id="task-1",
            plan_fingerprint="f" * 64,
            status=TaskStatus.RUNNING,
            node_status=(("n1", NodeStatus.SUCCEEDED), ("n2", NodeStatus.RUNNING)),
            attempts=(("n1", 1), ("n2", 1)),
            budget=TaskBudget(10, 3),
            executions=2,
            failures=0,
            sequence=0,
            events=(),
        )
        summary = summarize_task(source)
        self.assertEqual(summary.task_id, "task-1")
        self.assertEqual(summary.state, "running")
        self.assertEqual(summary.node_total, 2)
        self.assertEqual(summary.node_succeeded, 1)
        self.assertEqual(summary.provenance, TASK_RUNTIME_PROVENANCE)
        rendered = json.dumps(summary.__dict__, sort_keys=True)
        self.assertNotIn("plan_fingerprint", rendered)
        self.assertNotIn("attempts", rendered)
        self.assertNotIn("events", rendered)

    def test_unknown_permission_cannot_carry_authoritative_looking_counters(self) -> None:
        with self.assertRaises(ValueError):
            PermissionStatusSummary(
                StatusState.UNKNOWN,
                1,
                None,
                None,
                PERMISSION_CONTROL_PROVENANCE,
            ).validated()
        summary = unobserved_permission(StatusState.UNKNOWN)
        self.assertEqual(summary.state, StatusState.UNKNOWN)
        self.assertEqual(summary.provenance, PERMISSION_CONTROL_PROVENANCE)
        with self.assertRaises(ValueError):
            unobserved_permission(StatusState.READY)

    def test_boolean_values_are_not_valid_numeric_counters(self) -> None:
        with self.assertRaises(ValueError):
            TaskStatusSummary(
                "task",
                "running",
                True,
                0,
                0,
                0,
                TASK_RUNTIME_PROVENANCE,
            ).validated()
        with self.assertRaises(ValueError):
            PermissionStatusSummary(
                StatusState.READY,
                False,
                0,
                0,
                PERMISSION_CONTROL_PROVENANCE,
            ).validated()

    def test_secret_like_observation_keys_fail_closed(self) -> None:
        reject_secret_like_mapping({"provider_id": "fixture", "model_count": 1})
        for key in ("api_key", "credentialValue", "permit", "approval_token", "password"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                reject_secret_like_mapping({key: "do-not-export"})

    def test_output_byte_ceiling_rejects_large_but_individually_valid_graph(self) -> None:
        providers = tuple(
            ProviderStatus(
                f"p{i}",
                tuple((f"m{j}-" + ("x" * 118)) for j in range(MAX_MODELS_PER_PROVIDER)),
                StatusState.READY,
                PROVIDER_CATALOG_PROVENANCE,
            )
            for i in range(MAX_PROVIDERS)
        )
        snapshot = RuntimeStatusSnapshot(
            runtime=StatusSignal(StatusState.READY, RUNTIME_STATUS_PROVENANCE, "Observed by deterministic fixture."),
            providers=providers,
            task=TaskStatusSummary("task", "running", 1, 0, 1, 0, TASK_RUNTIME_PROVENANCE),
            permission=PermissionStatusSummary(
                StatusState.READY,
                1,
                1,
                0,
                PERMISSION_CONTROL_PROVENANCE,
            ),
        )
        with self.assertRaisesRegex(ValueError, "byte ceiling"):
            snapshot.to_json()

    def test_strict_decoder_round_trips_valid_snapshot(self) -> None:
        source = disconnected_snapshot()
        decoded = RuntimeStatusSnapshot.from_json(source.to_json())
        self.assertEqual(decoded, source)

    def test_strict_decoder_rejects_unknown_and_duplicate_fields(self) -> None:
        raw = json.loads(disconnected_snapshot().to_json())
        raw["extra"] = True
        with self.assertRaisesRegex(ValueError, "unexpected fields"):
            RuntimeStatusSnapshot.from_json(json.dumps(raw))
        with self.assertRaisesRegex(ValueError, "duplicate JSON object key"):
            RuntimeStatusSnapshot.from_json('{"schema":"hive-runtime-status-v1","schema":"future"}')

    def test_strict_decoder_rejects_fake_ready_provider(self) -> None:
        raw = json.loads(disconnected_snapshot().to_json())
        raw["providers"] = [
            {
                "providerId": "fixture",
                "modelIds": [],
                "state": "READY",
                "provenance": PROVIDER_CATALOG_PROVENANCE,
            }
        ]
        with self.assertRaisesRegex(ValueError, "READY provider"):
            RuntimeStatusSnapshot.from_json(json.dumps(raw))

    def test_strict_decoder_rejects_boolean_counter(self) -> None:
        raw = json.loads(disconnected_snapshot().to_json())
        raw["permission"] = {
            "state": "READY",
            "policyEpoch": True,
            "activeSessions": 0,
            "pendingApprovals": 0,
            "provenance": PERMISSION_CONTROL_PROVENANCE,
        }
        with self.assertRaisesRegex(ValueError, "out of bounds"):
            RuntimeStatusSnapshot.from_json(json.dumps(raw))

    def test_fail_closed_helpers_emit_fixed_degraded_state_without_error_details(self) -> None:
        invalid = RuntimeStatusSnapshot(
            runtime=StatusSignal(StatusState.READY, RUNTIME_STATUS_PROVENANCE, "secret-value-must-not-leak"),
            providers=(),
            task=TaskStatusSummary("task", "running", True, 0, 0, 0, TASK_RUNTIME_PROVENANCE),
            permission=unobserved_permission(StatusState.UNKNOWN),
        )
        encoded = encode_status_fail_closed(invalid)
        parsed = json.loads(encoded)
        self.assertEqual(parsed["runtime"]["state"], "DEGRADED")
        self.assertNotIn("secret-value-must-not-leak", encoded)
        decoded = decode_status_fail_closed('{"not":"a snapshot"}')
        self.assertEqual(decoded.runtime.state, StatusState.DEGRADED)
        self.assertEqual(decoded.providers, ())
        self.assertIsNone(decoded.task)

    def test_cli_emits_one_disconnected_snapshot_without_external_runtime(self) -> None:
        script = Path(__file__).resolve().parents[2] / "tools" / "runtime" / "status_snapshot.py"
        namespace = runpy.run_path(str(script), run_name="runtime_status_test")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(namespace["main"](), 0)
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["schema"], "hive-runtime-status-v1")
        self.assertEqual(parsed["runtime"]["state"], "DISCONNECTED")
        self.assertEqual(parsed["permission"]["provenance"], PERMISSION_CONTROL_PROVENANCE)


if __name__ == "__main__":
    unittest.main()
