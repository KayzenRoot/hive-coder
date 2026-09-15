from __future__ import annotations

import contextlib
import io
import json
import runpy
import unittest
from pathlib import Path

from hive_runtime.agent_tasks import NodeStatus, TaskBudget, TaskSnapshot, TaskStatus
from hive_runtime.intelligence.capabilities import ModelCapabilityRegistry
from hive_runtime.providers import CapabilityProbeResult, ProviderCatalog, ProviderModel
from hive_runtime.runtime_status import (
    MAX_MODELS_PER_PROVIDER,
    MAX_PROVIDERS,
    PermissionStatusSummary,
    ProviderStatus,
    RuntimeStatusSnapshot,
    StatusSignal,
    StatusState,
    TaskStatusSummary,
    disconnected_snapshot,
    reject_secret_like_mapping,
    summarize_provider_catalog,
    summarize_task,
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
    def test_disconnected_snapshot_is_truthful_and_non_authoritative(self) -> None:
        raw = disconnected_snapshot().to_json()
        parsed = json.loads(raw)
        self.assertEqual(parsed["runtime"]["state"], "DISCONNECTED")
        self.assertEqual(parsed["permission"]["state"], "DISCONNECTED")
        self.assertIsNone(parsed["permission"]["policyEpoch"])
        self.assertEqual(parsed["providers"], [])
        self.assertIsNone(parsed["task"])
        for forbidden in ("permit", "credential", "password", "approvalToken", "prompt", "modelOutput"):
            self.assertNotIn(forbidden, raw)

    def test_ready_provider_requires_concrete_model_observation(self) -> None:
        with self.assertRaises(ValueError):
            ProviderStatus("fixture", (), StatusState.READY).validated()
        observed = ProviderStatus("fixture", ("model-a",), StatusState.READY).validated()
        self.assertEqual(observed.model_ids, ("model-a",))

    def test_empty_provider_catalog_is_unknown_not_ready(self) -> None:
        registry = ModelCapabilityRegistry()
        catalog = ProviderCatalog(registry, lambda provider, model, probe: False)
        result = summarize_provider_catalog(catalog, ("fixture",))
        self.assertEqual(result[0].state, StatusState.UNKNOWN)
        self.assertEqual(result[0].model_ids, ())

    def test_observed_provider_catalog_is_bounded_and_does_not_verify_by_name(self) -> None:
        registry = ModelCapabilityRegistry()
        catalog = ProviderCatalog(registry, lambda provider, model, probe: False)
        catalog.refresh(FakeProvider((ProviderModel("m1", "Model One"),)))
        result = summarize_provider_catalog(catalog, ("fixture",))
        self.assertEqual(result, (ProviderStatus("fixture", ("m1",), StatusState.READY),))
        profile = registry.get("fixture", "m1")
        self.assertIsNotNone(profile)
        self.assertFalse(registry.negotiate("fixture", "m1", frozenset({"text"})).allowed)

    def test_task_summary_exposes_only_bounded_progress(self) -> None:
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
        rendered = json.dumps(summary.__dict__, sort_keys=True)
        self.assertNotIn("plan_fingerprint", rendered)
        self.assertNotIn("attempts", rendered)
        self.assertNotIn("events", rendered)

    def test_unknown_permission_cannot_carry_authoritative_looking_counters(self) -> None:
        with self.assertRaises(ValueError):
            PermissionStatusSummary(StatusState.UNKNOWN, 1, None, None).validated()
        PermissionStatusSummary(StatusState.UNKNOWN, None, None, None).validated()

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
            )
            for i in range(MAX_PROVIDERS)
        )
        snapshot = RuntimeStatusSnapshot(
            runtime=StatusSignal(StatusState.READY, "fixture-runtime", "Observed by deterministic fixture."),
            providers=providers,
            task=TaskStatusSummary("task", "running", 1, 0, 1, 0),
            permission=PermissionStatusSummary(StatusState.READY, 1, 1, 0),
        )
        with self.assertRaisesRegex(ValueError, "byte ceiling"):
            snapshot.to_json()

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


if __name__ == "__main__":
    unittest.main()
