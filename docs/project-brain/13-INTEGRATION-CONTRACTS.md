# Integration Contracts — Hive Coder

External foundations are dependencies, not the Hive-facing architecture.

## Interpreter runtime boundary
Hive Coder talks to an `InterpreterAdapter` contract for task execution, tool invocation, events, cancellation, errors and runtime identity. No UI surface depends directly on upstream internals.

## Computer-use boundary
`ComputerUseAdapter` exposes observation, accessibility/window context when available, bounded actions, cancellation, capability discovery and permission/error states. Cua is the preferred initial implementation candidate.

## Provider boundary
`ProviderAdapter` separates Hive orchestration from model/provider APIs. OpenCode Go is an important initial provider path but not a hard dependency.

## Contract rules
Version capabilities; fail closed on unknown privileged capability; normalize errors without hiding upstream diagnostics; preserve cancellation/emergency stop; redact secrets; record implementation/runtime identity in evidence; integration upgrades require contract/regression tests.
