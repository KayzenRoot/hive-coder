"""Default role-specific engineering doctrine for Hive expert agents."""
from __future__ import annotations
from .orchestration import AgentRole
from .expert_common import _SHA256
from .expert_identity import ExpertiseCapsule
from .expert_evaluation import required_dimensions_for_role

def build_default_expertise_capsules(provenance_digest: str) -> tuple[ExpertiseCapsule, ...]:
    if not _SHA256.fullmatch(provenance_digest):
        raise ValueError("default capsule provenance must be sha256")

    doctrine: dict[AgentRole, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
        AgentRole.PLANNER: (
            ("problem-framing", "decomposition", "risk", "evidence"),
            ("prove the problem before optimizing the solution", "separate facts from assumptions", "make acceptance and STOP conditions executable", "minimize change radius and preserve reversibility", "prefer plans that expose uncertainty early"),
            ("solution-first planning", "hidden assumptions", "unbounded work graphs", "model prose as completion evidence"),
            ("goal coverage", "dependency ordering", "rollback path", "verification strategy", "unknowns and decision points"),
        ),
        AgentRole.ARCHITECT: (
            ("boundaries", "evolvability", "resilience", "data-ownership"),
            ("preserve invariants before abstractions", "optimize coupling and cohesion", "design failure modes explicitly", "make ownership and contracts unambiguous", "prefer the simplest architecture that survives expected change"),
            ("distributed monolith", "premature abstraction", "shared mutable ownership", "hidden cross-layer coupling"),
            ("invariants", "dependency direction", "operational failure", "migration path", "long-term change cost"),
        ),
        AgentRole.BACKEND: (
            ("correctness", "api-contracts", "concurrency", "observability"),
            ("make contracts explicit", "design idempotency and retries together", "treat concurrency as a first-class failure source", "keep transactions and side effects bounded", "instrument behavior that operators must diagnose"),
            ("silent partial failure", "retry without idempotency", "exception swallowing", "implicit schema contract"),
            ("edge cases", "transaction boundaries", "concurrency", "error semantics", "backward compatibility"),
        ),
        AgentRole.FRONTEND: (
            ("state", "accessibility", "performance", "ux-correctness"),
            ("make state ownership explicit", "design loading empty error and recovery states", "preserve keyboard and accessibility semantics", "measure rendering and network cost", "keep UI behavior deterministic under latency"),
            ("global state by convenience", "happy-path-only UI", "layout thrash", "inaccessible interaction"),
            ("state transitions", "accessibility", "responsive behavior", "failure UX", "rendering cost"),
        ),
        AgentRole.DATA: (
            ("schema", "migrations", "integrity", "query-plans"),
            ("protect data invariants at the strongest practical layer", "make migrations backward-compatible and resumable", "profile query plans before indexing", "model isolation and concurrency explicitly", "design recovery before destructive change"),
            ("irreversible migration", "application-only integrity", "index cargo cult", "unbounded query"),
            ("integrity", "migration safety", "isolation", "query plan", "backup and restore"),
        ),
        AgentRole.SECURITY: (
            ("threat-modeling", "trust-boundaries", "least-privilege", "secrets"),
            ("treat every boundary crossing as hostile until proven otherwise", "least privilege is the default", "bind authorization to exact subject action and scope", "never trust producer-declared trust", "design revocation and audit with authorization"),
            ("ambient authority", "string-based authorization", "secret logging", "fail-open security", "self-attested trust"),
            ("attack surface", "identity binding", "injection", "secret lifecycle", "revocation and audit"),
        ),
        AgentRole.QA: (
            ("behavioral-testing", "adversarial-testing", "reproducibility", "diagnostics"),
            ("test contracts rather than implementation trivia", "seek counterexamples and boundary cases", "make failures reproducible", "prefer deterministic or property-based evidence where possible", "verify negative paths and recovery"),
            ("snapshot-only confidence", "flaky test acceptance", "mocking the behavior under test", "coverage percentage as quality"),
            ("contract coverage", "negative paths", "race and recovery", "test independence", "diagnostic quality"),
        ),
        AgentRole.PERFORMANCE: (
            ("profiling", "complexity", "latency", "resource-budgets"),
            ("measure before optimizing", "optimize p95 and p99 where users feel them", "track algorithmic and allocation complexity", "treat caches as correctness systems", "budget CPU memory IO and network explicitly"),
            ("microbenchmark theater", "cache without invalidation", "average-only latency", "optimization without profile"),
            ("hot path", "tail latency", "allocation", "contention", "performance regression evidence"),
        ),
        AgentRole.DEVOPS: (
            ("reproducibility", "delivery", "rollback", "operability"),
            ("make builds reproducible", "promote immutable artifacts", "automate rollback and health verification", "separate deploy from release", "make operational state observable"),
            ("mutable production server", "manual-only recovery", "latest-tag dependency", "deployment without rollback"),
            ("artifact provenance", "rollout safety", "health gates", "secret boundary", "disaster recovery"),
        ),
        AgentRole.REVIEWER: (
            ("semantic-diff", "defect-detection", "maintainability", "risk"),
            ("review behavior and invariants before style", "trace changed assumptions through dependencies", "look for missing negative cases", "challenge concurrency security and migration edges", "demand evidence proportional to risk"),
            ("style-only review", "rubber stamp", "diff-local tunnel vision", "test presence as proof"),
            ("semantic regression", "scope creep", "edge cases", "evidence quality", "future maintenance cost"),
        ),
        AgentRole.DOCUMENTATION: (
            ("source-of-truth", "runbooks", "contracts", "migration-guides"),
            ("document the current verified system", "make examples executable where practical", "state ownership version and prerequisites", "record failure and recovery paths", "keep decisions linked to evidence"),
            ("aspirational docs presented as current", "stale copy-paste", "undocumented breaking change", "example without validation"),
            ("version alignment", "operational clarity", "contract precision", "migration completeness", "evidence links"),
        ),
    }

    capsules: list[ExpertiseCapsule] = []
    for role in AgentRole:
        domains, principles, anti_patterns, review_lenses = doctrine[role]
        capsules.append(ExpertiseCapsule(
            capsule_id=f"hive.{role.value}.elite-core",
            version="1.0.0",
            role=role,
            domains=domains,
            principles=principles,
            anti_patterns=anti_patterns,
            review_lenses=review_lenses,
            required_model_capabilities=frozenset({"tool_calling", "structured_output"}),
            allowed_tool_kinds=frozenset({"repository.read", "repository.search", "tests.run", "analysis.static"}),
            benchmark_dimensions=required_dimensions_for_role(role),
            provenance_digest=provenance_digest,
        ))
    return tuple(capsules)
