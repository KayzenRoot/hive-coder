# Hive Coder Competitive Capability Matrix v1

**Status:** LIVING BASELINE / PRODUCT INPUT
**Date:** 2026-09-16
**Purpose:** Build Hive Coder as one coherent local + remote agentic engineering environment that absorbs proven interaction patterns while differentiating through measurable Hive-owned harness technology.

## Product law

Competitors are a moving baseline, not the architecture. We may reproduce useful product capabilities and workflows, but must not copy proprietary code, private implementation details, branding, protected assets or unverifiable claims. Hive-owned implementations remain behind stable adapters and governed capability contracts.

A capability is not considered a Hive advantage until a repeatable benchmark or objective evidence demonstrates an improvement in at least one relevant dimension: task success, context/token efficiency, latency, cost, security, recoverability, proof quality, user control, portability or multi-agent coordination.

## Baseline products researched

### OpenAI Codex
Publicly documented capabilities to track:
- desktop/app, CLI and IDE surfaces;
- parallel agents and isolated worktrees;
- local and cloud execution;
- long-running tasks;
- Skills;
- Automations and cloud triggers;
- review of agent changes/diffs;
- computer use;
- multiple files and terminals;
- remote devboxes over SSH;
- integrated browser workflows;
- persistent session/history continuity.

### Anthropic Claude / Claude Code
Publicly documented capabilities to track:
- terminal, VS Code/JetBrains and desktop surfaces;
- multiple local and remote sessions in parallel;
- plan mode and editable plan artifact;
- checkpoints and rewind;
- subagents;
- hooks;
- background tasks;
- sandboxed filesystem/network execution;
- permission/auto-mode controls;
- Git workflows including commit/push;
- computer use/browser surfaces;
- Agent SDK / extensibility;
- context editing/compaction and memory mechanisms.

### Cursor
Publicly documented capabilities to track:
- editor Agent mode with multi-file edits and terminal;
- Cloud Agents in isolated VMs;
- local-to-cloud handoff;
- parallel agents and cloud subagents;
- reusable cloud environment snapshots;
- multi-repository environments;
- computer use in cloud desktop/browser;
- remote desktop takeover and handback;
- screenshots, videos and logs as artifacts;
- MCP integrations;
- Skills and hooks;
- scheduled/event-triggered Automations;
- mobile/web/Slack/GitHub/Linear/API initiation;
- PR creation and PR babysitting;
- memories from prior automation runs.

### Z.AI / ZCode ecosystem
Public Z.AI material and current product announcements indicate a baseline including:
- model/provider flexibility through GLM Coding Plan and supported coding tools;
- natural-language planning, coding, debugging and optimization;
- codebase Q&A and intelligent completion;
- automated lint/merge-conflict/release-note tasks;
- Vision, Web Search and Web Reader MCP capabilities;
- Goal Mode for autonomous objective completion;
- subagents for parallel specialist work;
- remote control from another device;
- idle/background task execution.

Where a ZCode-specific capability is not documented in stable first-party technical documentation, keep it as `VERIFY_CURRENT_PRODUCT` rather than treating it as architectural fact.

## Hive target matrix

| Domain | Baseline capability to absorb | Hive target | Differentiating Hive layer |
|---|---|---|---|
| Local coding | read/edit/create/replace, terminal, Git | REQUIRED | Permission & Control Plane + semantic mutation budget |
| Remote coding | isolated remote environments | REQUIRED | Remote Execution Fabric + signed capability leases |
| Local ↔ remote | handoff and resume | REQUIRED | Continuity Capsules with deterministic state/evidence transfer |
| Mobile/web remote | start, inspect, approve, intervene | REQUIRED | Zero-trust remote command envelope and granular takeover |
| Parallel agents | isolated branches/worktrees/VMs | REQUIRED | speculative parallelism + Merge Firewall + consensus review |
| Long tasks | background/idle execution | REQUIRED | stop governor + uncertainty ledger + resumable checkpoints |
| Planning | plans before implementation | REQUIRED | compiled Context Capsules + executable acceptance contracts |
| Context | codebase search/compaction/memory | REQUIRED | ACCE Context Compiler + Context Delta Ledger + entropy controller |
| Models | model selector/providers | REQUIRED | adaptive model router based on task/risk/cost/evidence |
| Tools | MCP/skills/hooks/plugins | REQUIRED | capability-budget compiler + least-authority tool leases |
| Computer use | desktop/browser operation | REQUIRED | governed Cua adapter + action permits + visual evidence |
| Git | stage/commit/branch/PR/push | REQUIRED IN SLICES | request-bound Git authority, no generic Git mutation by default |
| Review | diff review/agent review | REQUIRED | HEDS + proof-carrying execution + cross-model consensus |
| Verification | tests/build/browser validation | REQUIRED | Evidence Graph + counterfactual verification |
| Artifacts | logs/screenshots/video | REQUIRED | evidence-addressed artifact graph tied to exact head/action |
| Rollback | checkpoints/rewind | REQUIRED | Rollback Capsules spanning code, context, authority and evidence |
| Automations | schedules/events/webhooks | REQUIRED | governed automation recipes with risk budgets and stop conditions |
| Multi-repo | coordinated repositories | REQUIRED | repository graph + atomic task decomposition/merge barriers |
| Environments | snapshots/devboxes | REQUIRED | reproducible Environment Capsules with provenance digest |
| Secrets/network | scoped credentials/network | REQUIRED | ephemeral secret leases + destination-bound network permits |
| Observability | progress/status/logs | REQUIRED | causal execution timeline + token/cost/risk/evidence telemetry |
| Learning | memories/prior runs | REQUIRED | evidence-weighted learning, never silently promoting unverified memory |
| UX | editor, desktop, terminal, web/mobile | REQUIRED | one task graph shared across surfaces rather than separate sessions |

## Remote-first architecture target

Remote capability is a first-class product pillar, not a later add-on.

Target flow:

`Any Surface → Hive Control Plane → Task Graph → Execution Placement → Local / Remote Machine / Cloud Sandbox → Evidence Stream → Review / Takeover → Governed Promotion`

Execution placement must support policy-based choice among:
1. local trusted machine;
2. user-owned remote machine/devbox;
3. Hive-managed isolated cloud runner;
4. self-hosted worker;
5. future ephemeral high-assurance runner.

The task identity, Context Capsule, authority budget, model policy, checkpoint chain and Evidence Graph must survive placement changes. Remote handoff must not mean re-prompting the model from scratch.

## Proposed Hive-only frontier technologies

These are candidate inventions until separately implemented and benchmarked:

1. **Continuity Capsule Protocol (CCP):** transfers minimal sufficient task/context/authority/evidence state between local and remote execution while preserving exact provenance.
2. **Execution Placement Optimizer (EPO):** chooses local vs remote vs cloud based on hardware, latency, data sensitivity, required tools, cost and expected duration.
3. **Capability Lease Mesh (CLM):** short-lived, destination-bound and task-bound authority leases that follow an agent across machines without copying broad credentials.
4. **Evidence Streaming Fabric (ESF):** streams causal proof events, diffs, tests, screenshots and logs into a content-addressed graph while a task is running.
5. **Deterministic Takeover Protocol (DTP):** human or parent-agent takeover freezes a checkpoint, authority state and environment identity before control changes hands, then allows governed handback.
6. **Shadow Executor:** for high-risk mutations, a second isolated executor can simulate or independently verify the intended effect before publication.
7. **Semantic Merge Firewall:** compares intent, contracts, tests and behavioral deltas across parallel agent branches before allowing convergence, not merely textual Git conflicts.
8. **Risk-Adaptive Autonomy:** autonomy expands or contracts dynamically according to capability class, evidence quality, uncertainty, blast radius and rollback confidence.
9. **Proof Budget Scheduler:** spends verification compute where uncertainty and impact are highest instead of running every expensive verifier uniformly.
10. **Portable Task Twin:** a live machine-readable twin of the task that can be opened from desktop, web or mobile and contains goal, state, blockers, authority, evidence and next safe action.

## Benchmark law

The future Hive Harness Benchmark Suite must compare Hive against available competitor workflows using equivalent repositories/tasks where licensing and terms permit. At minimum measure:
- successful task completion;
- wall-clock time;
- model input/output tokens;
- retries/rework;
- unnecessary file/tool reads;
- unsafe or out-of-scope action attempts;
- human approvals/interventions;
- rollback/recovery success;
- test/regression escape rate;
- evidence completeness;
- cost per accepted task;
- remote handoff loss and resume latency.

No marketing statement such as `superior to Codex/Claude/Cursor/ZCode` becomes canonical from feature count alone.

## Planned product epics after current governed Git slices

1. `HCODER-REMOTE-001` Remote Execution Fabric foundation.
2. `HCODER-CONTEXT-001` ACCE Context Compiler + Context Capsule runtime.
3. `HCODER-ORCH-001` Task Graph and multi-agent isolation/orchestration.
4. `HCODER-REMOTE-002` Continuity Capsule local↔remote handoff.
5. `HCODER-EVIDENCE-001` Evidence Streaming Fabric + Evidence Graph.
6. `HCODER-TAKEOVER-001` remote desktop/task takeover and governed handback.
7. `HCODER-AUTOMATION-001` schedules/events/background/idle execution.
8. `HCODER-BENCH-001` competitor-neutral harness benchmark suite.

Each epic must be decomposed into narrow Work Orders. None of this document itself expands current runtime authority.

## STOP

Do not turn competitor parity into one giant capability. Preserve least authority and incremental native evidence. Remote execution, shell/process, Git commit/push, network, credentials, computer use and automation each require explicit governed boundaries.