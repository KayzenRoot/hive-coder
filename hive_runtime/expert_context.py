"""Minimum-sufficient context, provenance-backed truth, and architecture invariants."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Protocol
from .orchestration import AgentRole, ProjectDigitalTwin
from .expert_common import _SAFE_ID, _SAFE_TOKEN, _SHA256, _sha, ContextKind

class ContextTrustVerifier(Protocol):
    def __call__(self, item: "ContextItem") -> bool: ...


@dataclass(frozen=True)
class ContextItem:
    item_id: str
    kind: ContextKind
    source: str
    tags: frozenset[str]
    digest: str
    token_cost: int
    priority: int = 50

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.item_id) or not self.source.strip():
            raise ValueError("invalid context item")
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in self.tags):
            raise ValueError("invalid context tag")
        if not _SHA256.fullmatch(self.digest):
            raise ValueError("context digest must be sha256")
        if not 1 <= self.token_cost <= 2_000_000 or not 0 <= self.priority <= 100:
            raise ValueError("invalid context cost/priority")


@dataclass(frozen=True)
class ContextRequest:
    role: AgentRole
    required_tags: frozenset[str]
    preferred_tags: frozenset[str] = frozenset()
    mandatory_ids: frozenset[str] = frozenset()
    token_budget: int = 32_000
    allow_untrusted_data: bool = True

    def validate(self) -> None:
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in self.required_tags | self.preferred_tags):
            raise ValueError("invalid requested context tag")
        if any(not _SAFE_ID.fullmatch(item) for item in self.mandatory_ids):
            raise ValueError("invalid mandatory context id")
        if not 512 <= self.token_budget <= 2_000_000:
            raise ValueError("invalid context request budget")


@dataclass(frozen=True)
class ContextBinding:
    item_id: str
    digest: str
    trusted: bool
    mode: str
    score: int


@dataclass(frozen=True)
class ContextPack:
    role: AgentRole
    bindings: tuple[ContextBinding, ...]
    total_tokens: int
    required_tags: frozenset[str]

    def fingerprint(self) -> str:
        return _sha({
            "role": self.role.value,
            "bindings": [
                {"id": item.item_id, "digest": item.digest, "trusted": item.trusted,
                 "mode": item.mode, "score": item.score}
                for item in self.bindings
            ],
            "tokens": self.total_tokens,
            "required_tags": sorted(self.required_tags),
        })


class ContextLens:
    """Greedy minimum-sufficient context selector with explicit trust labels."""

    def __init__(self, trust_verifier: ContextTrustVerifier) -> None:
        self._verifier = trust_verifier

    def _score(self, item: ContextItem, request: ContextRequest) -> int:
        role_tag = f"role:{request.role.value}"
        return (
            item.priority
            + (120 if role_tag in item.tags else 0)
            + 60 * len(item.tags & request.required_tags)
            + 15 * len(item.tags & request.preferred_tags)
        )

    def select(self, items: Iterable[ContextItem], request: ContextRequest) -> ContextPack:
        request.validate()
        by_id: dict[str, ContextItem] = {}
        trusted: dict[str, bool] = {}
        for item in items:
            item.validate()
            if item.item_id in by_id:
                raise ValueError("duplicate context item")
            by_id[item.item_id] = item
            trusted[item.item_id] = self._verifier(item) is True
        if not request.mandatory_ids.issubset(by_id):
            raise ValueError("mandatory context item missing")

        selected: dict[str, ContextBinding] = {}
        total = 0

        def add(item: ContextItem) -> None:
            nonlocal total
            if item.item_id in selected:
                return
            is_trusted = trusted[item.item_id]
            if not is_trusted and not request.allow_untrusted_data:
                raise PermissionError("untrusted context is not allowed for this request")
            if total + item.token_cost > request.token_budget:
                raise RuntimeError("context budget cannot satisfy required context")
            selected[item.item_id] = ContextBinding(
                item.item_id,
                item.digest,
                is_trusted,
                "trusted_context" if is_trusted else "untrusted_data",
                self._score(item, request),
            )
            total += item.token_cost

        for item_id in sorted(request.mandatory_ids):
            add(by_id[item_id])

        def covered_required() -> frozenset[str]:
            covered: set[str] = set()
            for item_id, binding in selected.items():
                if binding.trusted:
                    covered.update(by_id[item_id].tags & request.required_tags)
            return frozenset(covered)

        while covered_required() != request.required_tags:
            missing = request.required_tags - covered_required()
            candidates = [
                item for item in by_id.values()
                if item.item_id not in selected and trusted[item.item_id] and item.tags & missing
                and total + item.token_cost <= request.token_budget
            ]
            if not candidates:
                raise RuntimeError("trusted context cannot satisfy all required tags within budget")
            candidates.sort(
                key=lambda item: (
                    -len(item.tags & missing),
                    -(self._score(item, request)),
                    item.token_cost,
                    item.item_id,
                )
            )
            add(candidates[0])

        # Add at most one best item for each preferred tag. This keeps the pack minimum-sufficient
        # instead of filling the remaining context window merely because it is available.
        for tag in sorted(request.preferred_tags):
            if any(tag in by_id[item_id].tags for item_id in selected):
                continue
            candidates = [
                item for item in by_id.values()
                if item.item_id not in selected and tag in item.tags
                and (trusted[item.item_id] or request.allow_untrusted_data)
                and total + item.token_cost <= request.token_budget
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda item: (not trusted[item.item_id], -self._score(item, request), item.token_cost, item.item_id))
            add(candidates[0])

        bindings = tuple(sorted(selected.values(), key=lambda item: (-item.score, item.item_id)))
        return ContextPack(request.role, bindings, total, request.required_tags)


class TruthFactVerifier(Protocol):
    def __call__(self, fact: "TruthFact") -> bool: ...


@dataclass(frozen=True)
class TruthFact:
    fact_id: str
    subject: str
    predicate: str
    object_digest: str
    provenance_digest: str
    tags: frozenset[str] = frozenset()

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.fact_id) or not self.subject.strip() or not self.predicate.strip():
            raise ValueError("invalid truth fact")
        if not _SHA256.fullmatch(self.object_digest) or not _SHA256.fullmatch(self.provenance_digest):
            raise ValueError("truth fact digests must be sha256")
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in self.tags):
            raise ValueError("invalid truth fact tag")

    def fingerprint(self) -> str:
        self.validate()
        return _sha({
            "id": self.fact_id,
            "subject": self.subject,
            "predicate": self.predicate,
            "object": self.object_digest,
            "provenance": self.provenance_digest,
            "tags": sorted(self.tags),
        })


class CodeTruthMap:
    """Provenance-backed fact index. Only host-verified facts are authoritative."""

    def __init__(self, facts: Iterable[TruthFact], verifier: TruthFactVerifier) -> None:
        self._facts: dict[str, TruthFact] = {}
        self._verified: set[str] = set()
        for fact in facts:
            fact.validate()
            if fact.fact_id in self._facts:
                raise ValueError("duplicate truth fact")
            self._facts[fact.fact_id] = fact
            if verifier(fact) is True:
                self._verified.add(fact.fact_id)

    def is_verified(self, fact_id: str) -> bool:
        return fact_id in self._verified

    def fact_fingerprint(self, fact_id: str) -> str:
        if fact_id not in self._verified:
            raise PermissionError("truth fact is not host verified")
        return self._facts[fact_id].fingerprint()

    def query(self, tags: Iterable[str], *, verified_only: bool = True) -> tuple[TruthFact, ...]:
        wanted = frozenset(tags)
        if any(not _SAFE_TOKEN.fullmatch(tag) for tag in wanted):
            raise ValueError("invalid truth query tag")
        facts = [fact for fact in self._facts.values() if wanted.issubset(fact.tags)]
        if verified_only:
            facts = [fact for fact in facts if fact.fact_id in self._verified]
        return tuple(sorted(facts, key=lambda fact: fact.fact_id))

    def fingerprint(self) -> str:
        return _sha([self._facts[item].fingerprint() for item in sorted(self._verified)])


@dataclass(frozen=True)
class ArchitecturalInvariant:
    invariant_id: str
    statement_digest: str
    node_ids: frozenset[str]
    fact_ids: frozenset[str]
    critical: bool = False

    def validate(self) -> None:
        if not _SAFE_ID.fullmatch(self.invariant_id) or not _SHA256.fullmatch(self.statement_digest):
            raise ValueError("invalid architectural invariant")
        if not self.node_ids or any(not _SAFE_ID.fullmatch(item) for item in self.node_ids):
            raise ValueError("architectural invariant requires valid nodes")
        if not self.fact_ids or any(not _SAFE_ID.fullmatch(item) for item in self.fact_ids):
            raise ValueError("architectural invariant requires provenance facts")


class ArchitecturalGenome:
    """Evidence-bound architectural invariants with deterministic drift checks."""

    def __init__(self, twin: ProjectDigitalTwin, truth: CodeTruthMap,
                 invariants: Iterable[ArchitecturalInvariant]) -> None:
        self.twin_fingerprint = twin.fingerprint()
        self.truth_fingerprint = truth.fingerprint()
        self._invariants: dict[str, ArchitecturalInvariant] = {}
        self._fact_fingerprints: dict[str, dict[str, str]] = {}
        for invariant in invariants:
            invariant.validate()
            if invariant.invariant_id in self._invariants:
                raise ValueError("duplicate architectural invariant")
            twin.validate_targets(invariant.node_ids)
            fact_fingerprints = {fact_id: truth.fact_fingerprint(fact_id) for fact_id in invariant.fact_ids}
            self._invariants[invariant.invariant_id] = invariant
            self._fact_fingerprints[invariant.invariant_id] = fact_fingerprints
        if not self._invariants:
            raise ValueError("architectural genome requires invariants")

    def fingerprint(self) -> str:
        return _sha({
            "twin": self.twin_fingerprint,
            "truth": self.truth_fingerprint,
            "invariants": [
                {
                    "id": item.invariant_id,
                    "statement": item.statement_digest,
                    "nodes": sorted(item.node_ids),
                    "facts": self._fact_fingerprints[item.invariant_id],
                    "critical": item.critical,
                }
                for item in sorted(self._invariants.values(), key=lambda inv: inv.invariant_id)
            ],
        })

    def detect_drift(self, current_twin: ProjectDigitalTwin, current_truth: CodeTruthMap) -> tuple[str, ...]:
        drifted: list[str] = []
        twin_changed = current_twin.fingerprint() != self.twin_fingerprint
        for invariant_id, invariant in sorted(self._invariants.items()):
            fact_changed = False
            for fact_id, old_fingerprint in self._fact_fingerprints[invariant_id].items():
                try:
                    fact_changed = fact_changed or current_truth.fact_fingerprint(fact_id) != old_fingerprint
                except (KeyError, PermissionError):
                    fact_changed = True
            if twin_changed or fact_changed:
                drifted.append(invariant_id)
        return tuple(drifted)
