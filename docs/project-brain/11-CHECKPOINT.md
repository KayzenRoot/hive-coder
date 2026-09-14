# Checkpoint — Hive Coder

**Checkpoint:** HCODER-CP-0003  
**Status:** APPROVED  
**Date:** 2026-09-14  
**Repository:** `KayzenRoot/hive-coder`  
**Approved Work Order:** `HCODER-WO-0003`  
**PR:** `#7`

## Proven canonical state
- HCODER-CP-0002 foundation pins and provenance remain authoritative.
- A Hive-owned shell-free stdio child-process lifecycle exists for external foundations.
- A strict newline-delimited JSON-RPC 2.0 peer exists with correlated request IDs, bounded timeouts, notifications, remote errors, maximum line size, fail-closed malformed/unknown responses and bounded shutdown.
- Unsupported inbound JSON-RPC requests are denied by default.
- Runtime production constructors derive expected versions from canonical `foundations/foundations.lock.json` and run exact-version preflight before launching ACP/MCP mode.
- Child processes and version probes receive a least-privilege environment allowlist; ambient provider/API secrets are not inherited implicitly. Cua telemetry is forced off in the current production constructor.
- Open Interpreter ACP v1 initialize, session create, session cancellation notification, session-update collection and session close are implemented and mock-contract tested without model/prompt execution.
- Cua Driver modern MCP `2026-07-28` `server/discover` is implemented and mock-contract tested as inventory only.
- `CuaAdapter` exposes no `tools/call` surface in this checkpoint.
- Governance now explicitly checks out and verifies the exact PR/push SHA instead of relying on GitHub's synthetic PR merge ref.
- `HCODER-WO-0003-CR-001`, `CR-002` and `CR-003` were resolved in the same Work Order.
- HEDS approved implementation head `95058d820d9ee330a4b89d0a935e32689f008b98` after Governance run `34910600726` proved `EXACT_HEAD_OK` and 26/26 passing tests with `ResourceWarning` treated as error.

## Product state
Foundation process/protocol lifecycle is now implemented behind Hive-owned adapters. No proven Open Interpreter prompt execution, model/provider integration, Cua desktop action execution, permission engine, emergency-stop runtime, user-takeover runtime, desktop UI, packaging or production deployment exists yet.

## Safety state
- No foundation source repository or binary is vendored.
- Automatic dependency installation remains disabled.
- OmniParser/Ultralytics remain excluded from the approved foundation set.
- Cua tool names may be inventoried but cannot be invoked through the approved adapter.
- Real mouse/keyboard/screen/window/browser/clipboard control remains forbidden and HIGH_ASSURANCE.
- Ambient credentials are not implicitly forwarded to foundation subprocesses.

## Next necessary increment
Implement the Hive Permission & Control Plane as a HIGH_ASSURANCE prerequisite before any real Cua action: capability taxonomy/policy, default-deny action authorization, application/workspace allowlists, emergency stop, user takeover, bounded sessions, audit trail/redaction, replay-resistant approvals, cancellation propagation, adversarial prompt-injection tests and deterministic mocked action gates. Keep real desktop mutation disabled until that control plane itself is approved.
