# HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface

**Status:** COMPLETE / CANONICAL — CLOSEOUT SEAL PENDING  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0019` / `e4bc74d1ae6c4054cd98cd34b16e6357f911224c`  
**Issue:** `#51`  
**PR:** `#54`

## OBJECTIVE
Connect the desktop to the canonical CP-0019 one-shot runtime-status helper through exactly one fixed, argument-free Tauri read command and render bounded Runtime/Provider/Task/Permission truth without granting execution or mutation authority.

## CONTEXT
CP-0017 defines truthful status data, CP-0018 freezes the strict canonical wire and CP-0019 canonicalizes the fixed one-shot helper. Historical PR #39 is supporting evidence only and predates the final canonical-wire hardening.

## SCOPE
- one fixed Rust supervisor module;
- helper identity derived only from `current_exe()` sibling + fixed basename;
- fixed `--stdio-status-v1` argument;
- cleared child environment, piped stdin/stdout, discarded stderr, hard timeout;
- canonical constant `status.snapshot` request and response byte ceiling aligned to CP-0018;
- one argument-free `get_runtime_status_envelope` command bound to window `main`;
- frontend admission only through `decodeRuntimeStatusEnvelope(raw)`;
- read-only System Truth rendering for runtime/provider/task/permission;
- security gate hardening so process execution exists only in the audited supervisor;
- Rust/frontend regressions and exact-head CI/HEDS.

## OUT OF SCOPE
Generic process/shell execution, caller-selected executable/path/args/env, daemon/listener/socket/generic RPC, provider/model execution, credentials, task/permission mutation, terminal/filesystem/Git writes, Cua/computer input, remote control, billing/purchases, automatic skill activation, sidecar packaging/signing/updater.

## FILES / SOURCES TO READ
Checkpoint CP-0019, Decisions Ledger, Architecture, Security, Backlog, Integration Contracts, `apps/desktop/src/contracts/runtimeStatus.ts`, `tools/runtime/status_sidecar.py`, `tools/desktop/security_gate.py`, desktop Tauri bridge/UI sources.

## REQUIREMENTS
1. Frontend supplies zero process arguments or paths.
2. Process identity/mode cannot come from UI/model/task text or ambient environment.
3. Sidecar path is a fixed sibling of `current_exe()` and symlink/reparse input fails closed.
4. Child environment is cleared.
5. Request is the canonical CP-0018 request for `desktop-runtime`; response is physically bounded to the canonical response ceiling.
6. Missing/crashed/nonzero/timed-out/malformed/noncanonical helper output yields `null`/DISCONNECTED presentation, never READY.
7. Raw response admission uses only the public strict decoder `decodeRuntimeStatusEnvelope(raw)`.
8. Safety/task/provider/file/computer mutation controls remain unavailable.
9. Security gate permits process execution only in the fixed supervisor and reports generic process execution zero.

## ARCHITECTURE RULES
`React -> named argument-free Tauri read command -> fixed RuntimeStatusSupervisor -> fixed CP-0019 helper -> CP-0018 wire -> strict TS raw decoder -> presentation-only System Truth`.

This route exposes no mutation and cannot mint Permission & Control Plane authority.

## CONSTRAINTS
No Tauri shell/process plugin; no shell command string; no PATH lookup; no frontend process payload; no ambient secret forwarding; no long-running child; no helper packaging in this WO.

## ACCEPTANCE CRITERIA
- security gate: one fixed supervisor process site, generic execution zero;
- Rust tests: fixed sibling identity, fixed mode/request/ceiling, bounded fail-closed behavior;
- frontend tests: raw decoder path, truthful runtime/provider/task/permission rendering, mutation controls disabled;
- all existing Governance/Desktop suites green, including RustSec, locked Rust check, Tauri Windows release build and launch smoke;
- HEDS unresolved HIGH/CRITICAL = 0.

## TESTS
Security gate, Rust unit tests, TS contract/component tests, Governance Ubuntu + HIGH_ASSURANCE Windows, RustSec, cargo locked check, Tauri Windows release build + launch smoke.

## DELIVERABLES
Supervisor, named Tauri command, raw-wire bridge, System Truth integration, security gate, tests, Evidence Bundle, governed decision/checkpoint if promoted.

## REVIEW FORMAT
HEDS_DELTA HIGH_ASSURANCE exact-head. Generic process execution, caller-controlled process identity/args/env, secret inheritance, unbounded output, fake readiness or mutation-plane bypass is HIGH/CRITICAL.

## STOP CONDITION
Exact-head Governance + Desktop Shell green; HEDS approved; no unresolved HIGH/CRITICAL; promotion/checkpoint only after evidence; squash merge and post-merge validation; canonical closeout before advancing.

## TECHNICAL RECEIPT
Technical exact head `86c6e956985e0b51e0f56b3568a3fe9db61fef90` passed Governance #263 (**288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #99 (security gate PASS, frontend **26/26**, Rust **13/13**, locked audits/checks, Tauri Windows release build and launch smoke). Technical HEDS `5216871217` approved promotion with unresolved HIGH/CRITICAL `0`.

`HCODER-WO-0020-CR-001` MEDIUM and `HCODER-WO-0020-CR-002` MEDIUM are resolved.

## PROMOTION RECEIPT
Promotion head `bf76c2a451763d7bc361437028e819d2df5f97ba` changed exactly 7 documentation/evidence/governance files and no product/runtime/workflow/dependency/capability file. It passed Governance #264 (**288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #100, including strict security gate, frontend **26/26**, locked Rust audit/tests/check, Windows release build + launch smoke. Promotion HEDS `5216925860` approved the final-approval state mutation with unresolved HIGH/CRITICAL `0`.

## FINAL APPROVAL STATE
Final reviewed product head `344130199536e33a656d49a365e746610f89e245` passed Governance #265 (**288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #101 (strict security gate, frontend **26/26**, npm audit 0, Rust **13/13**, locked RustSec/check, Windows release build and launch smoke). Final HEDS `5217039528` approved squash merge with unresolved HIGH/CRITICAL `0`.

## CANONICAL CLOSEOUT APPENDIX
PR #54 was squash-merged with expected-head protection as GitHub-signed product commit `621732c00ba1f3325272dfa1631fddbbabf3dfc4`, parented directly on canonical CP-0019 `e4bc74d1ae6c4054cd98cd34b16e6357f911224c`.

Post-merge on exact product SHA `621732c00ba1f3325272dfa1631fddbbabf3dfc4`:
- Governance #266 (`35037526420`): SUCCESS — **288/288 Ubuntu + 61/61 Windows HIGH_ASSURANCE**.
- Desktop Shell #102 (`35037526361`): SUCCESS — security gate PASS, frontend **26/26**, npm audit 0, RustSec executed over 432 locked dependencies with 7 warning-class residuals, Rust **13/13**, locked cargo check, Windows release build and launch smoke PASS.

The Work Order product STOP conditions are satisfied. This document records `COMPLETE / CANONICAL` subject only to the documentation-only closeout branch itself passing exact-head Governance + Desktop Shell + HEDS, squash merge and push validation. The original WO scope, exclusions, requirements and authority boundaries above remain immutable and fully applicable.