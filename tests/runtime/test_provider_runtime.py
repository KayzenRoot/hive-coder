import unittest

from hive_runtime.providers import (
    CapabilityProbeResult, CredentialScope, ModelRouter, OpenCodeGoProfile, ProviderCatalog, ProviderModel,
)
from hive_runtime.intelligence.capabilities import CapabilityRequest, ModelCapabilityRegistry


class FakeProvider:
    provider_id = "opencode-go"
    def list_models(self):
        return [ProviderModel("alpha", "Alpha"), ProviderModel("beta", "Beta")]
    def probe(self, model_id):
        if model_id == "alpha":
            return [CapabilityProbeResult("tool_calling", True, "deterministic-probe")]
        return [CapabilityProbeResult("tool_calling", False, "deterministic-probe")]


class ProviderRuntimeTests(unittest.TestCase):
    def test_opencode_go_profile_grants_no_capability(self):
        self.assertEqual(OpenCodeGoProfile.provider_id, "opencode-go")

    def test_catalog_registers_only_probe_verified_capability(self):
        registry = ModelCapabilityRegistry(); catalog = ProviderCatalog(registry)
        catalog.refresh(FakeProvider())
        self.assertTrue(registry.negotiate("opencode-go", "alpha", CapabilityRequest(frozenset({"tool_calling"}))).allowed)
        self.assertFalse(registry.negotiate("opencode-go", "beta", CapabilityRequest(frozenset({"tool_calling"}))).allowed)

    def test_router_filters_unverified_models(self):
        registry = ModelCapabilityRegistry(); ProviderCatalog(registry).refresh(FakeProvider())
        selected = ModelRouter(registry).select(CapabilityRequest(frozenset({"tool_calling"})), provider="opencode-go")
        self.assertEqual(selected.model_id, "alpha")

    def test_router_fails_closed_when_capability_missing(self):
        registry = ModelCapabilityRegistry(); ProviderCatalog(registry).refresh(FakeProvider())
        with self.assertRaises(LookupError): ModelRouter(registry).select(CapabilityRequest(frozenset({"vision"})))

    def test_credentials_repr_and_redacted_never_expose_secret(self):
        scope = CredentialScope({"OPENCODE_GO_TOKEN": "super-secret-value"})
        self.assertNotIn("super-secret-value", repr(scope))
        self.assertEqual(scope.redacted()["OPENCODE_GO_TOKEN"], "[REDACTED]")
        self.assertEqual(scope.get("OPENCODE_GO_TOKEN"), "super-secret-value")

    def test_duplicate_model_ids_fail_closed(self):
        class Bad(FakeProvider):
            def list_models(self): return [ProviderModel("x", "x"), ProviderModel("x", "x2")]
        with self.assertRaises(ValueError): ProviderCatalog(ModelCapabilityRegistry()).refresh(Bad())


if __name__ == "__main__": unittest.main()
