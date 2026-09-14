# Hive Runtime Bridge

`hive_runtime` is the Hive-owned process and protocol boundary for external agent foundations. Upstream internals never become the Hive-facing architecture.

## HCODER-WO-0003 surface

- `ManagedStdioProcess`: shell-free bounded child lifecycle.
- `JsonRpcPeer`: strict newline-delimited JSON-RPC 2.0 transport.
- `InterpreterAdapter`: ACP v1 handshake and non-prompt session lifecycle for Open Interpreter.
- `CuaAdapter`: modern MCP `2026-07-28` discovery for Cua Driver.
- Production `from_binary(...)` constructors verify the exact pinned foundation version before launch.

## Safety boundary

The Cua adapter intentionally has no tool invocation method. Discovery may report privileged tools such as click/type, but the bridge cannot call them in this Work Order. Open Interpreter has no prompt method in this increment. Unsupported inbound requests fail closed by default.

Real desktop control requires a later HIGH_ASSURANCE increment containing permission mediation, emergency stop, user takeover, bounded application/action scope, audit semantics and rollback/containment evidence.
