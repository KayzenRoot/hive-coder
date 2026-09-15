# HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface

**Status:** APPROVED FOR EXECUTION  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0019` on `main` at `e4bc74d1ae6c4054cd98cd34b16e6357f911224c`  
**Issue:** `#51`  
**Historical evidence only:** PR `#39` / branch `feat/HCODER-WO-0020-desktop-runtime-status-bridge` MUST NOT be merged or cherry-picked.

## OBJECTIVE
Connect the desktop to the fixed CP-0019 runtime-status sidecar through one named, argument-free Tauri read command and render truthful Runtime/Provider/Task/Permission presentation state in System Truth, while preserving all mutation controls as unavailable.

## CONTEXT
CP-0017 canonicalized the bounded non-authoritative runtime status model, CP-0018 froze the strict one-shot raw-wire protocol, and CP-0019 canonicalized the fixed one-shot helper. WO-0020 is the first desktop process boundary for runtime observation. The historical stacked candidate predates final CP-0018/0019 hardening and is supporting evidence only.

## SCOPE
- Add a fixed Rust runtime-status supervisor module.
- Resolve only a sidecar sibling with fixed basename adjacent to `current_exe()`.
- Reject symlink/reparse/non-file sidecar identity.
- Launch only the fixed sidecar with exact `--stdio-status-v1`, cleared child environment, piped stdin/stdout, discarded stderr and hard timeout.
- Send one fixed canonical CP-0018 status request and physically cap response bytes to the canonical response ceiling.
- Add argument-free `get_runtime_status_envelope` Tauri command, main-window only.
- Frontend bridge admits response only through `decodeRuntimeStatusEnvelope(raw)`.
- Render bounded Runtime/Provider/Task/Permission read-only System Truth when valid.
- Missing/crashed/timed-out/invalid sidecar yields `null` live status / disconnected presentation, never fake READY.
- Keep all execution/safety/mutation controls disabled.
- Narrowly extend the desktop security gate so exactly one audited fixed supervisor process site is permitted and generic process execution elsewhere remains forbidden.
- Add Rust/frontend/security regressions.

## OUT OF SCOPE
Generic process/shell execution, caller-controlled executable/path/args/env, provider/model execution, credentials, task mutation, permit/approval mutation, terminal, filesystem/Git writes, Cua/computer input, remote control, billing/purchases, automatic skill activation, daemon/service lifecycle, sockets/listeners, sidecar packaging/signing/update delivery, process attestation.

## FILES / SOURCES TO READ
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/05-SECURITY.md`
- `apps/desktop/src/contracts/runtimeStatus.ts`
- `tools/runtime/status_sidecar.py`
- `tools/desktop/security_gate.py`
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src/lib/desktopBridge.ts`
- `apps/desktop/src/components/ShellView.tsx`
- historical PR #39 only as non-authoritative evidence

## REQUIREMENTS
1. Frontend sends zero arguments to `get_runtime_status_envelope`.
2. Supervisor executable identity/path/mode/request cannot come from UI/model/task text or ambient environment.
3. Sidecar path is derived only from `current_exe()` sibling + fixed basename; symlink/reparse/non-file identities fail closed.
4. Child environment is cleared; no ambient provider secret inheritance.
5. Request identity and wire are fixed and canonical for CP-0018.
6. Response is read with a physical byte ceiling equal to CP-0018 `MAX_RUNTIME_STATUS_RESPONSE_BYTES` semantics; newline/framing is one-shot.
7. Rust transport performs only framing/size/process checks. TypeScript `decodeRuntimeStatusEnvelope(raw)` is the final strict raw-wire admission boundary; no `JSON.parse(raw)` + semantic-parser bypass is allowed.
8. Missing/crashed/timed-out/nonzero/malformed sidecar returns no live status, never fake READY.
9. Runtime/provider/task/permission status is presentation-only and cannot enable or authorize Run/Pause/Emergency Stop/Take Control.
10. No Tauri shell/process plugin and no generic command string/PATH lookup.
11. Security gate proves exactly one fixed supervisor process site and zero generic process execution elsewhere.
12. Any post-spawn error path must terminate and reap the child before returning.

## ARCHITECTURE RULES
`React -> named argument-free Tauri read command -> fixed RuntimeStatusSupervisor -> fixed CP-0019 sidecar -> CP-0018 one-shot raw wire -> strict TS decoder -> bounded presentation`.

This route transports presentation state only. It does not bypass the Permission & Control Plane because it exposes no mutating operation or execution permit surface.

## CONSTRAINTS
No new dependency; no Tauri shell/process plugin; no shell string; no PATH executable lookup; no frontend path/args/env; no secret environment forwarding; no long-running child; no packaging/signing claim.

## ACCEPTANCE CRITERIA
- Security gate reports one approved fixed supervisor and zero generic process execution.
- Tauri allowlist contains exactly the three named read commands: desktop snapshot, workspace selection, runtime status envelope.
- Rust tests prove fixed sibling identity, fixed mode/request, byte ceiling, child cleanup helpers and no user-controlled process inputs.
- Frontend tests prove strict raw-wire decoder use, null fallback on invalid/unavailable transport, truthful status rendering and disabled mutation controls.
- Existing Governance and Desktop Shell suites remain green on exact head.
- HEDS unresolved HIGH/CRITICAL = 0.

## TESTS
Security gate; Rust unit tests; TypeScript contract/component tests; full Governance; RustSec; `cargo test/check --locked`; Windows Tauri release build + launch smoke.

## DELIVERABLES
- `.engineering/work-orders/HCODER-WO-0020.md`
- `.engineering/context-locks/HCODER-WO-0020.json`
- `apps/desktop/src-tauri/src/runtime_status_supervisor.rs`
- native Tauri command wiring
- desktop bridge/App/System Truth integration
- desktop security-gate hardening
- focused frontend/Rust tests
- evidence/correction/checkpoint artifacts after exact-head proof

## REVIEW FORMAT
HEDS_DELTA HIGH_ASSURANCE exact-head. Generic process execution, caller-controlled process identity/args/env, secret inheritance, unbounded output, raw-wire parser bypass, fake readiness or mutation-plane bypass is HIGH/CRITICAL.

## STOP CONDITION
Exact-head Governance + Desktop Shell green, HEDS approved with unresolved HIGH/CRITICAL = 0, evidence/checkpoint delta accurate, squash merge with expected-head protection, then push-triggered Governance + Desktop Shell green on `main`. CP-0020 is not canonical before post-merge proof and canonical closeout. No generic execution/mutation authority is promoted under WO-0020.
