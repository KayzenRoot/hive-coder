# Integration Contracts — Hive Coder

External foundations are dependencies, not the Hive-facing architecture.

## Shared runtime/process boundary
Hive owns child-process and wire-protocol lifecycle. Foundation processes launch without a shell, receive a least-privilege environment, have bounded request/shutdown behavior and fail closed on unknown/malformed state. Production constructors resolve expected versions from `foundations/foundations.lock.json` and perform exact-version preflight before protocol launch.

## Permission & Control Plane boundary
Every privileged adapter/executor call crosses the Hive-owned `PermissionControlPlane`. Policy is default-deny; explicit deny wins; capability/action/target scope is session-bound; mandatory-approval risk cannot be downgraded. Trusted approval creates request-bound authorization and a short-lived signed single-use execution permit. The executor consumes that permit against the exact request immediately before mutation and revalidates live target identity. Model/tool surfaces never receive the trusted approval operation.

Emergency stop, user takeover, cancellation, expiry and policy changes invalidate ephemeral authorization. Audit events redact sensitive fields and form a SHA-256 digest chain.

## Interpreter runtime boundary
Hive talks to `InterpreterAdapter`, never upstream internals directly. Approved pin: Open Interpreter `0.0.43`, tag `rust-v0.0.43`, commit `6e7c4bb78bb1c349b82f584f7e21a529ec39a74f`. Primary transport is ACP v1 / NDJSON JSON-RPC over stdio; exec JSONL is fallback. Prompt/model execution remains separately governed.

## Computer-use boundary
Approved pin: Cua Driver `0.28.1`, tag `cua-driver-rs-v0.28.1`, commit `d8028a7943087ee258dc1b4d19dc12a7cd27669c`.

Modern MCP revision `2026-07-28` is per-request negotiated over stdio. `server/discover` proves protocol/capability envelope; canonical tool inventory comes from a separate `tools/list` request. Hive preserves each advertised `inputSchema`, capability tokens and annotations. Production does not infer executable tools from discovery names or model text.

`HCODER-WO-0005` approves only Hive semantic actions `pointer.click` and `keyboard.type_text`. `HCODER-WO-0006` resolves their concrete Cua tool names from the pinned driver's advertised capabilities and validates required argument properties before wiring. Every `tools/call` carries modern MCP metadata plus a Hive request fingerprint and remains permit-gated.

The real Windows harness is opt-in (`HIVE_ENABLE_REAL_CUA=1`), requires an explicitly supplied pinned binary and sandbox application, and obtains foreground HWND/PID/process image through Win32 rather than model input. The application/window identity is revalidated before dispatch. No automatic binary installation occurs. Hosted CI contract success is not evidence of physical desktop mutation; physical E2E stays UNKNOWN until an explicitly provisioned safe runner proves it.

## Skills/resource boundary
Cua Driver may advertise MCP skills/resources, but resource discovery/read does not itself activate a Hive skill or grant permissions. Hive will own skill provenance, verification, activation, permission requirements and rollback in a later governed Skills Engine increment.

## Provider boundary
`ProviderAdapter` separates Hive orchestration from model/provider APIs. OpenCode Go is an important initial provider path but not a hard dependency. A later Model Capability Negotiator will expose only capabilities proven for the selected provider/model.

## Remote-control boundary
Remote Hive control will be a separate HIGH_ASSURANCE subsystem. It must use authenticated encrypted device/session semantics, least privilege, revocation, audit and emergency stop. A raw Cua/RDP/VNC endpoint must never be exposed directly to the public internet by Hive.

## Contract rules
Version capabilities; fail closed on unknown privileged capability/version/schema; normalize errors without hiding diagnostics; preserve cancellation/emergency stop; redact secrets; record runtime identity; integration upgrades require regression evidence; no automatic dependency installation without a later approved design.