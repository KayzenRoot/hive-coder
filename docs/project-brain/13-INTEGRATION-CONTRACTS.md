# Integration Contracts — Hive Coder

External foundations are dependencies, not the Hive-facing architecture.

## Interpreter runtime boundary
Hive Coder talks to an `InterpreterAdapter` contract for task execution, tool invocation, events, cancellation, errors and runtime identity. No UI surface depends directly on upstream internals.

Approved first foundation pin: Open Interpreter `0.0.43`, tag `rust-v0.0.43`, commit `6e7c4bb78bb1c349b82f584f7e21a529ec39a74f`. Primary transport is ACP / JSON-RPC over stdio; `interpreter exec` JSONL is fallback only. Version mismatch fails closed.

## Computer-use boundary
`ComputerUseAdapter` exposes observation, accessibility/window context when available, bounded actions, cancellation, capability discovery and permission/error states.

Approved first foundation pin: Cua Driver `0.28.1`, tag `cua-driver-rs-v0.28.1`, commit `d8028a7943087ee258dc1b4d19dc12a7cd27669c`. Primary transport is MCP carried in JSON-RPC 2.0 over stdio. No live computer-control capability is approved merely by pinning this dependency; action execution requires a separate HIGH_ASSURANCE Work Order.

## Provider boundary
`ProviderAdapter` separates Hive orchestration from model/provider APIs. OpenCode Go is an important initial provider path but not a hard dependency.

## Contract rules
Version capabilities; fail closed on unknown privileged capability or unknown pinned version; normalize errors without hiding upstream diagnostics; preserve cancellation/emergency stop; redact secrets; record implementation/runtime identity in evidence; integration upgrades require contract/regression tests; no automatic dependency installation unless a later approved security/recovery design explicitly authorizes it.
