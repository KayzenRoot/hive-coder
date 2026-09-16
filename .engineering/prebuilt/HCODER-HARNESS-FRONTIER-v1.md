# Hive Harness Frontier v1

**Status:** PREBUILT PRODUCT/ENGINEERING SPEC  
**Execution authority:** NONE  
**First consumer:** HCODER-WO-0023

## Goal
Build a model-independent coding harness that competes on measurable engineering outcomes rather than UI imitation. The target is lower context waste, lower rework, stronger evidence, safer autonomy, faster convergence and better cross-model portability.

## Baseline we must at least match
Current leading coding harnesses publicly expose combinations of persistent threads/tasks, sandboxed filesystem/process execution, approval policies, managed network boundaries, tool/extension systems, repository instructions, checkpoints/rewind, subagents, hooks/background tasks, MCP/tool integrations, long-running cloud execution and agent-to-agent review.

These are baseline capabilities, not differentiation.

## Hive-native frontier technologies

### 1. ACCE Context Compiler
Compile a task-specific **Context Capsule** from immutable project anchors + dependency graph + symbol graph + prior Context Delta Ledger. Context is selected by relevance, authority and freshness, then deduplicated and budgeted. Full transcript replay is fallback only.

Target metrics: useful-context ratio, cache/reuse ratio, tokens per accepted change, rediscovery rate.

### 2. Capability Budget Compiler
Every task compiles into an explicit capability budget before model execution. Tools, paths, network domains, mutation classes and approval floors become machine-checkable constraints. Models can request a budget delta but cannot self-expand it.

### 3. Semantic Mutation Budget
Go beyond file allowlists. Bind expected modules, symbols, APIs, schemas and semantic radius. A change outside expected semantic neighborhoods triggers drift review even when it is in an allowed file.

### 4. Proof-Carrying Execution
Privileged actions emit compact proof records linking request digest, authorization/permit, observed pre-state, resulting post-state, platform evidence and responsible task. Raw secrets/content remain excluded. A successful action without required proof is incomplete.

### 5. Evidence Graph
Represent `requirement → decision → contract → implementation symbol → test → CI job → review finding → checkpoint` as a navigable graph. Promotion requires all mandatory graph edges, not just a green aggregate check.

### 6. Counterfactual Verification Engine
For security/reliability-sensitive work, automatically derive negative variants from the approved contract: stale state, extra authority, tampered arguments, race windows, cancellation, unsupported platform and dependency drift. Promotion requires expected denial/failure evidence.

### 7. Uncertainty Ledger
Models must externalize unresolved assumptions as typed gates with owner, evidence needed, risk and expiry. The harness forbids silently turning an assumption into implementation fact. Resolved uncertainty becomes a decision/delta, not conversation debris.

### 8. Context Delta Ledger
Persist only new decisions, changed facts, evidence and invalidated assumptions after each round. Subsequent agents consume immutable anchors + deltas. This is the primary defense against long-session context bloat and repeated discovery.

### 9. Speculative Parallelism + Merge Firewall
Allow multiple agents/models to investigate, test, review or propose patches concurrently. Mutations do not directly collide: one governed integration lane validates semantic overlap, evidence completeness, conflict risk and capability budgets before convergence.

### 10. Adaptive Model Router
Route discovery, architecture, coding, security review, visual QA and cheap verification to different models based on observed quality/cost/latency for that task class. Policy and evidence contracts remain model-independent, so model replacement does not rewrite the harness.

### 11. Entropy Controller
Track context duplication, stale-source reuse, repeated tool calls, unbounded logs, retry loops and oscillating edits. Treat excess entropy as a first-class harness failure and trigger compaction, source re-grounding or strategy switch.

### 12. Rollback Capsule
Before mutation-heavy phases, compile the smallest rollback boundary: source identities, changed objects, generated state and restoration verification. Rollback is evidence-driven and scoped, not a blind workspace reset.

### 13. Autonomous Stop Governor
The harness stops not only on permission denial but also on evidence debt, uncertainty debt, semantic drift, repeated failed strategy, cost/token budget breach, platform divergence or inability to prove rollback. This prevents endless agent loops that are technically authorized but no longer productive.

### 14. Cross-Model Consensus Review
For high-risk work, reviewers may use heterogeneous models and independent context capsules. The harness compares findings by evidence identity rather than prose similarity, reducing correlated blind spots.

### 15. Harness Self-Benchmark Loop
Every accepted WO contributes telemetry to a benchmark corpus: context tokens, tool calls, wall time, correction rounds, CI failures, security findings, rollback events and accepted-change size. Harness changes must prove improvement on representative historical tasks before canonical promotion.

## Design law
Novel names are not proof of novelty. A Hive frontier feature is called differentiated only after objective benchmark evidence demonstrates an advantage or a materially different guarantee against a documented baseline. Until then it is a candidate innovation.

## Security law
No frontier mechanism may bypass the Permission & Control Plane. Optimization layers can reduce prompts/context/tool calls but cannot weaken capability isolation, request binding, permit semantics, native platform proof or audit redaction.

## Implementation sequence
1. Specify benchmark and metrics.
2. Build Context Capsule + Delta Ledger foundation.
3. Add Capability/Mutation Budget compilers.
4. Add Evidence Graph + Uncertainty Ledger.
5. Add Counterfactual Verification.
6. Add Entropy/Stop Governor.
7. Add speculative multi-agent lanes + Merge Firewall.
8. Add adaptive model routing and heterogeneous review.
9. Continuously benchmark against the previous Hive harness and documented external baselines.

## STOP
Do not claim Hive is globally superior to Codex, Claude or another harness from feature design alone. Claim superiority only for dimensions where repeatable benchmark evidence supports it.