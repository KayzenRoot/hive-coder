# HCODER Harness Benchmark v1

Status: PREBUILT BENCHMARK SPEC
Execution authority: NONE
First consumer: HCODER-WO-0023 and later harness WOs

## Purpose

Turn the Hive Harness Frontier into measurable engineering claims. A feature is not superior because it has a novel name or architecture. A claim is promotable only when repeatable evidence demonstrates an advantage or a materially stronger guarantee against a documented baseline.

## Benchmark law

1. Never collapse safety, quality, speed and cost into one vanity score.
2. A run that violates a safety or correctness gate is invalid, regardless of speed or token cost.
3. Compare identical task corpus, repository state, acceptance tests, platform envelope and authority budget.
4. Pin model/provider/version, harness revision, tool set, dependency graph and runner identity where reproducibility permits.
5. Record retries, corrections and human interventions. Hidden retries are benchmark fraud.
6. External harness comparisons are claims only when their configuration and results are reproducible enough to audit. Otherwise they are descriptive baselines.
7. Prefer medians plus tail behavior over a single best run. Preserve raw run evidence.
8. Benchmark changes against the previous Hive harness before making external superiority claims.

## Hard promotion gates

A candidate harness revision is ineligible for promotion if any representative task has:

- unresolved HIGH or CRITICAL security finding;
- acceptance-test regression;
- authority expansion outside the declared Capability Budget;
- semantic mutation outside the declared Mutation Budget without approved drift handling;
- missing mandatory Evidence Graph edges;
- unrecorded human intervention or retry;
- failed rollback where rollback is required;
- platform result represented as equivalent without native evidence;
- benchmark configuration drift that prevents an apples-to-apples comparison.

## Metric families

### A. Correctness and delivery quality

- accepted_change_success_rate
- first_pass_ci_pass_rate
- correction_rounds
- escaped_defect_count
- acceptance_test_pass_rate
- evidence_completeness_rate
- review_findings_by_severity
- semantic_drift_incidents

### B. Context efficiency

- context_input_tokens
- output_tokens
- tokens_per_accepted_change
- useful_context_ratio
- context_capsule_reuse_rate
- repeated_read_rate
- rediscovery_rate
- stale_source_reuse_count
- context_delta_bytes

### C. Execution efficiency

- wall_time_seconds
- tool_call_count
- repeated_tool_call_count
- retry_count
- model_call_count
- cost_usd_when_available
- correction_time_seconds
- human_intervention_count

### D. Safety and governance

- negative_security_tests_pass_rate
- denied_unapproved_authority_attempts
- capability_budget_violations
- mutation_budget_violations
- permit_binding_failures_detected
- cancellation_fail_closed_rate
- stale_state_fail_closed_rate
- unsupported_platform_fail_closed_rate
- rollback_success_rate
- evidence_graph_required_edges_present_rate
- unresolved_uncertainty_count_at_promotion

### E. Portability and platform fidelity

- model_portability_pass_rate
- provider_portability_pass_rate
- windows_native_pass_rate
- linux_native_pass_rate
- macos_native_pass_rate
- platform_divergence_incidents
- platform_specific_correction_rounds

## Normalization

Report raw values and normalized values where useful. Candidate normalizers include accepted semantic changes, accepted files, accepted symbols, acceptance requirements and wall-clock task units. LOC alone is never a quality denominator.

Recommended derived metrics:

- tokens_per_accepted_requirement = total_tokens / accepted_requirements
- tool_calls_per_accepted_requirement = tool_calls / accepted_requirements
- corrections_per_accepted_change = correction_rounds / accepted_changes
- evidence_density = proven_required_edges / required_evidence_edges
- authority_efficiency = accepted_mutation_operations / granted_mutation_operations

A derived metric must never erase its raw inputs.

## Representative corpus v1

Seed the internal historical corpus with completed, evidence-rich Hive Coder increments:

- HCODER-WO-0021: governed trusted-workspace file creation
- HCODER-WO-0022: governed existing-file atomic replacement
- HCODER-PLATFORM-001: first-class Windows/Linux/macOS validation matrix
- HCODER-WO-0023: governed Git staging, only after completion

Each replay fixture must pin the starting checkpoint and acceptance contract. Historical tasks may be converted into deterministic replay fixtures without rewriting their original evidence.

## Run record schema

Every benchmark run should eventually emit a machine-readable record containing at minimum:

- benchmark_schema
- benchmark_revision
- task_id
- corpus_fixture_digest
- checkpoint_sha
- harness_sha
- model_identity
- provider_identity
- platform_identity
- tool_manifest_digest
- capability_budget_digest
- mutation_budget_digest
- context_capsule_digest
- start_timestamp
- end_timestamp
- metric_values
- acceptance_result
- security_gate_result
- evidence_graph_digest
- uncertainty_ledger_digest
- rollback_result_if_required
- human_interventions
- retry_count
- final_change_digest

Raw prompts, secrets and private source content must not be required in the benchmark record. Store digests and governed evidence references instead.

## Comparison protocol

For a Hive revision A versus Hive revision B:

1. use the same corpus fixtures;
2. use equivalent authority and tools;
3. run enough repetitions to expose variance;
4. report median, p90 where sample size permits, failures and invalid runs;
5. require hard gates to pass before efficiency comparisons;
6. report regressions as well as improvements;
7. promote only the dimensions supported by evidence.

For Hive versus an external harness, additionally record every known configuration mismatch and capability mismatch. Do not manufacture parity by disabling a safety feature that is part of the product claim.

## Anti-gaming rules

The benchmark rejects:

- excluding failed runs after execution starts;
- silently increasing authority, tools or context for one candidate;
- counting generated code as accepted code before tests/review;
- using fewer acceptance requirements to improve speed;
- hiding model retries behind orchestration;
- treating skipped tests as passes;
- treating unsupported platform behavior as success;
- optimizing only the benchmark corpus without a held-out validation set;
- claiming global superiority from a single task or metric.

## Frontier proof map

The following Hive-native mechanisms should have explicit benchmark hypotheses before implementation:

- ACCE Context Compiler: lower context tokens and rediscovery without reducing acceptance/evidence quality.
- Context Delta Ledger: lower repeated-read and stale-context rates across sequential agents.
- Capability Budget Compiler: zero undeclared authority while preserving task completion.
- Semantic Mutation Budget: fewer out-of-scope semantic changes and review corrections.
- Proof-Carrying Execution: higher evidence completeness with bounded evidence overhead.
- Evidence Graph: fewer missing requirement-to-proof links at promotion.
- Counterfactual Verification Engine: higher detection rate for stale state, tampering, cancellation and authority-expansion faults.
- Uncertainty Ledger: fewer assumptions silently converted into implementation facts.
- Speculative Parallelism + Merge Firewall: lower wall time without increasing semantic conflicts or correction rounds.
- Adaptive Model Router: lower cost/latency at equal or better hard-gate outcomes.
- Entropy Controller: fewer repeated reads/tool calls/retry loops.
- Rollback Capsule: higher deterministic restoration success with smaller rollback scope.
- Autonomous Stop Governor: earlier termination of unproductive or unsafe strategies without reducing valid completion rate.
- Cross-Model Consensus Review: higher independently reproduced finding rate without excessive false positives.
- Harness Self-Benchmark Loop: measurable improvement over prior Hive revisions without benchmark drift.

## Superiority claim levels

Use dimension-specific evidence labels rather than a global score:

- DESIGNED: mechanism specified, no benchmark evidence yet.
- PROVEN_INTERNAL: repeatable advantage or stronger guarantee against previous Hive baseline.
- PROVEN_REPRODUCIBLE_EXTERNAL: repeatable comparable evidence against a documented external harness configuration.
- REGRESSED: candidate loses a previously proven dimension.
- INCOMPARABLE: configurations/capabilities differ enough that a fair claim cannot be made.

Never convert DESIGNED into PROVEN by narrative.

## WO-0023 boundary

This document does not grant Git mutation authority and does not authorize a dependency, subprocess, hook, network access or arbitrary `.git` write. HCODER-WO-0023 remains blocked from promotion until its backend is selected, implemented under the Context Lock, skipped security tests are replaced by objective evidence, native platform gates are green and HEDS approves the exact head.

## Next implementation WOs

After WO-0023, split executable harness mechanisms into small governed increments. Recommended order:

1. benchmark telemetry schema + deterministic recorder;
2. Context Capsule compiler + Context Delta Ledger;
3. Capability Budget + Semantic Mutation Budget compilers;
4. Evidence Graph + Uncertainty Ledger;
5. Counterfactual Verification Engine;
6. Entropy Controller + Autonomous Stop Governor;
7. speculative multi-agent execution + Merge Firewall;
8. Adaptive Model Router + heterogeneous consensus review;
9. continuous benchmark replay and held-out corpus.

STOP CONDITION: no claim that Hive Coder is globally superior to another harness may be promoted from this specification alone. Only repeatable benchmark evidence can promote a dimension-specific superiority claim.