# Integration Contracts — Hive Coder

External foundations are dependencies, not the Hive-facing architecture.

## Shared runtime/process boundary
Hive owns the child-process and wire-protocol lifecycle. Foundation processes are launched without a shell, receive a least-privilege environment rather than arbitrary ambient secrets, have bounded request/shutdown behavior, and fail closed on unknown/malformed protocol state. Production constructors resolve expected versions from `foundations/foundations.lock.json` and perform exact-version preflight before protocol launch. Unsupported inbound JSON-RPC requests are denied unless a later explicit Hive handler authorizes them.

## Permission & Control Plane boundary
Every future privileged adapter/executor call must cross the Hive-owned `PermissionControlPlane`. Policy evaluation is default-deny; explicit deny wins; capability/action/target scope is bound to a control session; mandatory-approval risk classes cannot be downgraded by policy. Trusted UI/orchestrator approval resolves a request-bound challenge into a signed single-use approval. Successful authorization emits a very short-lived signed execution permit bound to request fingerprint, session, policy epoch, global emergency epoch and expiry. A future executor must consume that permit against the exact same request immediately before mutation and revalidate live target identity. Untrusted model/tool surfaces must never receive the trusted approval operation.

Emergency stop, user takeover, cancellation, session expiry and policy changes invalidate ephemeral authorization. Audit events redact sensitive fields and form a SHA-256 digest chain. HCODER-WO-0004 remains authorization-only: it adds no desktop executor and grants no Cua `tools/call`.

## Interpreter runtime boundary
Hive Coder talks to an `InterpreterAdapter` contract for task execution, tool invocation, events, cancellation, errors and runtime identity. No UI surface depends directly on upstream internals.

Approved foundation pin: Open Interpreter `0.0.43`, tag `rust-v0.0.43`, commit `6e7c4bb78bb1c349b82f584f7e21a529ec39a74f`. Primary transport is ACP v1 / NDJSON JSON-RPC over stdio; `interpreter exec` JSONL remains fallback only. `HCODER-WO-0003` proves initialize, session create, cancellation notification, session-update collection and session close under deterministic mocks. Prompt/model execution is not yet approved or exposed by the bridge.

## Computer-use boundary
`ComputerUseAdapter` exposes observation, accessibility/window context when available, bounded actions, cancellation, capability discovery and permission/error states.

Approved foundation pin: Cua Driver `0.28.1`, tag `cua-driver-rs-v0.28.1`, commit `d8028a7943087ee258dc1b4d19dc12a7cd27669c`. `HCODER-WO-0003` proves modern MCP revision `2026-07-28` `server/discover` over stdio as inventory only. The current `CuaAdapter` intentionally exposes no `tools/call` method. Discovery of privileged tool names is not authorization to execute them. Live computer-control remains a separate HIGH_ASSURANCE capability.

## Provider boundary
`ProviderAdapter` separates Hive orchestration from model/provider APIs. OpenCode Go is an important initial provider path but not a hard dependency.

## Contract rules
Version capabilities; fail closed on unknown privileged capability or unknown pinned version; normalize errors without hiding upstream diagnostics; preserve cancellation/emergency stop; redact secrets; record implementation/runtime identity in evidence; integration upgrades require contract/regression tests; no automatic dependency installation unless a later approved security/recovery design explicitly authorizes it.
