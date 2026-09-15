# HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface

**Status:** APPROVED FOR EXECUTION — STACKED  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Stacked base:** `HCODER-WO-0019`  
**Canonical dependency:** CP-0019 must be canonical before promotion.

## OBJECTIVE
Connect the desktop to the fixed Hive runtime-status sidecar through one named, argument-free Tauri command and render truthful Runtime/Provider/Task/Permission presentation state in System Truth, while preserving all mutation controls as unavailable.

## CONTEXT
WO-0017 defines bounded status data, WO-0018 freezes the one-shot IPC protocol and WO-0019 defines the fixed sidecar helper. This increment is the first desktop process boundary for runtime observation, so generic process execution remains forbidden everywhere except one audited supervisor module.

## SCOPE
- Add a fixed sidecar supervisor resolving only `hive-runtime-status-sidecar(.exe)` adjacent to the Hive desktop executable.
- Launch with one fixed mode `--stdio-status-v1`, absolute derived path, `env_clear`, piped stdin/stdout, discarded stderr and a hard timeout.
- Send one constant status request; bound stdout before it reaches the frontend.
- Add argument-free `get_runtime_status_envelope` Tauri command scoped to window `main`.
- Parse the envelope through the strict WO-0018 TypeScript contract; transport errors fall back to no live runtime status.
- Render live read-only runtime/provider/task/permission truth in the inspector when available.
- Extend the desktop security gate to permit exactly this fixed supervisor and reject process execution elsewhere.
- Add Rust/frontend regressions.

## OUT OF SCOPE
Generic process/shell execution, caller-controlled executable/path/args/env, provider/model execution, credentials, task mutation, permit/approval mutation, terminal, filesystem/Git writes, Cua/computer input, remote control, billing/purchases, automatic skill activation, sidecar packaging/signing.

## FILES / SOURCES TO READ
- `tools/desktop/security_gate.py`
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src/lib/desktopBridge.ts`
- `apps/desktop/src/App.tsx`
- `apps/desktop/src/components/ShellView.tsx`
- `apps/desktop/src/contracts/runtimeStatus.ts`
- `tools/runtime/status_sidecar.py`

## REQUIREMENTS
1. Frontend sends zero arguments to the runtime status command.
2. Supervisor executable identity/path/mode cannot come from UI/model/task text or ambient env.
3. Sidecar path is derived only from `current_exe()` sibling + fixed basename and link/reparse inputs fail closed.
4. Child environment is cleared; no ambient provider secret inheritance.
5. Request is constant and response is physically byte-bounded with one-line framing and timeout.
6. Missing/crashed/malformed sidecar yields DISCONNECTED/no live status, never fake READY.
7. TypeScript strict parser remains final presentation contract validation.
8. Safety actions, task mutation, provider/model execution and file/computer mutation remain disabled.
9. The security gate proves generic process execution count remains zero outside the single fixed supervisor.

## ARCHITECTURE RULES
`React -> named Tauri read command -> fixed RuntimeStatusSupervisor -> fixed Hive sidecar -> status IPC v1 -> bounded presentation contract`. This route cannot bypass the Permission & Control Plane because it exposes no mutating operation.

## CONSTRAINTS
No Tauri shell/process plugin; no command string/shell; no PATH executable lookup; no frontend path/args; no secret environment forwarding; no long-running child; no sidecar packaging in this WO.

## ACCEPTANCE CRITERIA
Security gate reports fixed supervisor 1 / generic execution 0; Rust tests prove fixed path/mode/request and fail-closed missing helper; frontend tests prove runtime truth rendering and no safety/action enablement; Tauri Windows build/launch smoke and all existing suites pass; HEDS 0 unresolved HIGH/CRITICAL.

## TESTS
Security gate, Rust unit tests, TS contract/component tests, Governance, RustSec, cargo locked check, Tauri Windows build + launch smoke.

## DELIVERABLES
Fixed supervisor module, named Tauri command, bridge/UI integration, security-gate hardening, tests, evidence after proof.

## REVIEW FORMAT
HEDS_DELTA HIGH_ASSURANCE exact-head. Generic process execution, user-controlled process identity/args, secret inheritance, unbounded output, fake readiness or mutation-plane bypass is CRITICAL/HIGH.

## STOP CONDITION
Exact-head Governance + Desktop Shell green and HEDS approved. Promotion BLOCKED until CP-0019 canonical. No execution/mutation authority beyond fixed read-only sidecar observation may be promoted.
