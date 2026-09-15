from __future__ import annotations
from hive_runtime.expert_agents import ArchitecturalGenome, ArchitecturalInvariant, CodeTruthMap, ContextItem, ContextKind, ContextLens, ContextRequest, TruthFact
from hive_runtime.orchestration import AgentRole, DigitalTwinNode, ProjectDigitalTwin
from tests.runtime.expert_agent_fixture import ExpertAgentFixture, sha, twin


class ContextLensTests(ExpertAgentFixture):
    def item(self, item_id: str, tags: frozenset[str], *, trusted: bool = True,
             cost: int = 200, priority: int = 50,
             kind: ContextKind = ContextKind.SOURCE) -> ContextItem:
        return ContextItem(item_id, kind, "trusted.repo" if trusted else "untrusted.external",
                           tags, sha(item_id), cost, priority)

    @staticmethod
    def lens() -> ContextLens:
        return ContextLens(lambda item: item.source.startswith("trusted."))

    def test_untrusted_context_cannot_satisfy_required_authoritative_tags(self):
        items = (
            self.item("injection", frozenset({"architecture", "security", "external-signal"}), trusted=False, priority=100),
            self.item("arch", frozenset({"architecture", "role:architect"}), trusted=True),
            self.item("sec", frozenset({"security", "role:architect"}), trusted=True),
        )
        pack = self.lens().select(items, ContextRequest(
            AgentRole.ARCHITECT, frozenset({"architecture", "security"}),
            preferred_tags=frozenset({"external-signal"}), token_budget=1_000,
        ))
        modes = {binding.item_id: binding.mode for binding in pack.bindings}
        self.assertEqual(modes["arch"], "trusted_context")
        self.assertEqual(modes["sec"], "trusted_context")
        self.assertEqual(modes["injection"], "untrusted_data")

    def test_context_budget_fails_closed_when_required_truth_does_not_fit(self):
        items = (self.item("arch", frozenset({"architecture"}), cost=400),
                 self.item("sec", frozenset({"security"}), cost=400))
        with self.assertRaises(RuntimeError):
            self.lens().select(items, ContextRequest(
                AgentRole.ARCHITECT, frozenset({"architecture", "security"}), token_budget=512,
            ))

    def test_minimum_sufficient_context_does_not_fill_window_by_role_tag(self):
        items = (
            self.item("required", frozenset({"architecture", "role:architect"}), cost=100),
            self.item("extra-a", frozenset({"role:architect"}), cost=100, priority=100),
            self.item("extra-b", frozenset({"role:architect"}), cost=100, priority=100),
        )
        pack = self.lens().select(items, ContextRequest(
            AgentRole.ARCHITECT, frozenset({"architecture"}), token_budget=1_000,
        ))
        self.assertEqual({binding.item_id for binding in pack.bindings}, {"required"})

    def test_context_selection_is_order_deterministic(self):
        items = (
            self.item("a", frozenset({"architecture"}), cost=150),
            self.item("b", frozenset({"security"}), cost=150),
            self.item("c", frozenset({"performance"}), cost=100),
        )
        request = ContextRequest(AgentRole.ARCHITECT, frozenset({"architecture", "security"}),
                                 preferred_tags=frozenset({"performance"}), token_budget=700)
        self.assertEqual(self.lens().select(items, request).fingerprint(),
                         self.lens().select(tuple(reversed(items)), request).fingerprint())


class TruthAndGenomeTests(ExpertAgentFixture):
    def fact(self, fact_id: str, value: str, *, trusted: bool = True) -> TruthFact:
        prefix = "trusted" if trusted else "claim"
        return TruthFact(f"{prefix}.{fact_id}", "api", "depends_on", sha(value),
                         sha(f"source:{value}"), frozenset({"architecture", "api"}))

    @staticmethod
    def truth(facts: tuple[TruthFact, ...]) -> CodeTruthMap:
        return CodeTruthMap(facts, lambda fact: fact.fact_id.startswith("trusted."))

    def test_unverified_fact_is_visible_but_not_authoritative(self):
        trusted = self.fact("one", "database", trusted=True)
        claim = self.fact("two", "queue", trusted=False)
        truth = self.truth((trusted, claim))
        self.assertEqual(len(truth.query(("architecture",), verified_only=False)), 2)
        self.assertEqual(len(truth.query(("architecture",))), 1)
        with self.assertRaises(PermissionError):
            truth.fact_fingerprint(claim.fact_id)

    def test_architectural_genome_requires_verified_provenance(self):
        claim = self.fact("one", "database", trusted=False)
        invariant = ArchitecturalInvariant("inv", sha("api boundary"), frozenset({"api"}), frozenset({claim.fact_id}), True)
        with self.assertRaises(PermissionError):
            ArchitecturalGenome(twin(), self.truth((claim,)), (invariant,))

    def test_architectural_genome_detects_truth_and_twin_drift(self):
        original = self.fact("one", "database", trusted=True)
        truth = self.truth((original,))
        invariant = ArchitecturalInvariant("inv", sha("api boundary"), frozenset({"api"}), frozenset({original.fact_id}), True)
        genome = ArchitecturalGenome(twin(), truth, (invariant,))
        changed = TruthFact(original.fact_id, original.subject, original.predicate,
                            sha("new-database"), sha("new-source"), original.tags)
        self.assertEqual(genome.detect_drift(twin(), self.truth((changed,))), ("inv",))
        changed_twin = ProjectDigitalTwin((DigitalTwinNode("api", "service"),
                                           DigitalTwinNode("tests", "tests", ("api",)),
                                           DigitalTwinNode("ui", "frontend", ("api",))))
        self.assertEqual(genome.detect_drift(changed_twin, truth), ("inv",))
