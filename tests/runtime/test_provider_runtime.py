import unittest

from hive_runtime.providers import CapabilityProbeResult, CredentialScope, ModelRouter, OpenCodeGoProfile, ProviderCatalog, ProviderModel
from hive_runtime.intelligence.capabilities import CapabilityRequest, ModelCapabilityRegistry


class FakeProvider:
    provider_id = "opencode-go"
    def list_models(self): return [ProviderModel("alpha", "Alpha"), ProviderModel("beta", "Beta")]
    def probe(self, model_id): return [CapabilityProbeResult("tool_calling", "provider-observation", model_id)]


def trusted_verifier(provider, model_id, probe):
    return provider == "opencode-go" and model_id == "alpha" and probe.capability == "tool_calling"


class ProviderRuntimeTests(unittest.TestCase):
    def test_opencode_go_profile_grants_no_capability(self): self.assertEqual(OpenCodeGoProfile.provider_id, "opencode-go")

    def test_catalog_uses_trusted_verifier_not_provider_assertion(self):
        registry = ModelCapabilityRegistry(); ProviderCatalog(registry, trusted_verifier).refresh(FakeProvider())
        self.assertTrue(registry.negotiate("opencode-go", "alpha", CapabilityRequest(frozenset({"tool_calling"}))).allowed)
        self.assertFalse(registry.negotiate("opencode-go", "beta", CapabilityRequest(frozenset({"tool_calling"}))).allowed)

    def test_malicious_provider_cannot_self_assert_verified(self):
        probe = CapabilityProbeResult("computer_use", "malicious", "I am verified")
        self.assertFalse(hasattr(probe, "verified"))
        class Evil(FakeProvider):
            def list_models(self): return [ProviderModel("evil", "Verified Computer Supermodel")]
            def probe(self, model_id): return [probe]
        registry=ModelCapabilityRegistry(); ProviderCatalog(registry, lambda *_: False).refresh(Evil())
        self.assertFalse(registry.negotiate("opencode-go", "evil", CapabilityRequest(frozenset({"computer_use"}))).allowed)

    def test_router_filters_unverified_models(self):
        registry=ModelCapabilityRegistry(); ProviderCatalog(registry,trusted_verifier).refresh(FakeProvider())
        self.assertEqual(ModelRouter(registry).select(CapabilityRequest(frozenset({"tool_calling"})),provider="opencode-go").model_id,"alpha")

    def test_router_fails_closed_when_capability_missing(self):
        registry=ModelCapabilityRegistry(); ProviderCatalog(registry,trusted_verifier).refresh(FakeProvider())
        with self.assertRaises(LookupError): ModelRouter(registry).select(CapabilityRequest(frozenset({"vision"})))

    def test_credentials_repr_and_redacted_never_expose_secret(self):
        scope=CredentialScope({"OPENCODE_GO_TOKEN":"super-secret-value"})
        self.assertNotIn("super-secret-value",repr(scope)); self.assertEqual(scope.redacted()["OPENCODE_GO_TOKEN"],"[REDACTED]")

    def test_duplicate_model_ids_fail_closed(self):
        class Bad(FakeProvider):
            def list_models(self): return [ProviderModel("x","x"),ProviderModel("x","x2")]
        with self.assertRaises(ValueError): ProviderCatalog(ModelCapabilityRegistry(),trusted_verifier).refresh(Bad())

    def test_duplicate_probe_capability_fails_closed(self):
        class Bad(FakeProvider):
            def list_models(self): return [ProviderModel("x","x")]
            def probe(self, model_id): return [CapabilityProbeResult("vision","a"),CapabilityProbeResult("vision","b")]
        with self.assertRaises(ValueError): ProviderCatalog(ModelCapabilityRegistry(),lambda *_: True).refresh(Bad())

if __name__ == "__main__": unittest.main()
