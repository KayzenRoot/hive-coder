# Evidence Bundle — HCODER-WO-0020

**Work Order:** `HCODER-WO-0020 — Desktop Runtime Status Supervisor & System Truth Surface`  
**Issue:** `#51`  
**PR:** `#54`  
**Canonical base:** `HCODER-CP-0019` / `e4bc74d1ae6c4054cd98cd34b16e6357f911224c`  
**Technical exact head:** `86c6e956985e0b51e0f56b3568a3fe9db61fef90`  
**Technical HEDS:** `5216871217` — APPROVED FOR PROMOTION CANDIDATE, H/C `0`  
**Promotion head:** `bf76c2a451763d7bc361437028e819d2df5f97ba`  
**Promotion HEDS:** `5216925860` — APPROVED FOR FINAL APPROVAL MUTATION, H/C `0`

## Scope receipt
WO-0020 was reconstructed directly on canonical CP-0019. Historical PR #39 / branch `feat/HCODER-WO-0020-desktop-runtime-status-bridge` was supporting evidence only and was not merged or cherry-picked.

The technical implementation adds the first governed desktop child-process observation boundary:
- one fixed Rust supervisor module;
- one argument-free `get_runtime_status_envelope` Tauri command bound to the existing `main` window;
- fixed sibling helper basename and fixed `--stdio-status-v1` mode;
- `env_clear`, piped stdin/stdout, discarded stderr, hard timeout and bounded response;
- exact canonical CP-0018 request `{"op":"status.snapshot","protocol":"hive-runtime-status-ipc-v1","requestId":"desktop-runtime"}`;
- exact total response ceiling `33,024` bytes;
- frontend admission only through public `decodeRuntimeStatusEnvelope(raw)`;
- read-only Runtime/Provider/Task/Permission System Truth rendering;
- all mutation controls remain unavailable.

No generic process/shell command, PATH executable lookup, caller/model-selected executable/path/args/env, provider/model execution, credential authority, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, skill activation or billing/purchase authority was added.

## Corrections
- `HCODER-WO-0020-CR-001` MEDIUM — **RESOLVED**: System Truth no longer fabricates zero permission counters from null observations; provider/permission cards render canonical subsystem provenance.
- `HCODER-WO-0020-CR-002` MEDIUM — **RESOLVED**: the desktop security gate enforces the single process site, canonical request, exact byte ceiling, zero caller process payload and strict raw-wire decoder/no `JSON.parse(raw)` bypass.

## Technical exact-head receipt
Governance #263 (`35035152518`) on exact `86c6e956985e0b51e0f56b3568a3fe9db61fef90`: **SUCCESS**.
- Ubuntu source-pack: **288/288 PASS**, ResourceWarning fatal.
- Windows Server 2025 HIGH_ASSURANCE: **61/61 PASS**.

Desktop Shell #99 (`35035152526`) on the same exact head: **SUCCESS**.
- security gate: `DESKTOP_SECURITY_GATE=PASS`;
- `TAURI_COMMANDS=choose_workspace,get_desktop_snapshot,get_runtime_status_envelope`;
- frontend invokes **3**, runtime-status args **0**, capability permissions **0**;
- `RUNTIME_STATUS_RAW_DECODER=STRICT`;
- `GENERIC_PROCESS_EXECUTION=0`, `FIXED_RUNTIME_SIDECAR_PROCESS=1`;
- frontend **26/26 PASS**, typecheck/build PASS, npm audit **0 vulnerabilities**;
- RustSec scanned **432** locked dependencies; the known **7 warning-class** residuals remain explicit;
- Rust **13/13 PASS**, locked `cargo check` PASS;
- Tauri Windows release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`.

HEDS technical `5216871217`: **APPROVED FOR PROMOTION CANDIDATE**, unresolved HIGH/CRITICAL `0`.

## Promotion exact-head receipt
Promotion head `bf76c2a451763d7bc361437028e819d2df5f97ba` is one documentation/evidence/governance-only commit after the technical head, exactly 7 changed files with zero product/runtime/workflow/dependency/capability change.

- Governance #264 (`35035821821`): **SUCCESS** — Ubuntu **288/288 PASS**, Windows HIGH_ASSURANCE **61/61 PASS**.
- Desktop Shell #100 (`35035821714`): **SUCCESS** — strict security gate PASS, frontend **26/26 PASS**, locked Rust audit/tests/check PASS, Tauri Windows release build PASS and launch smoke PASS.
- HEDS promotion `5216925860`: **APPROVED FOR FINAL APPROVAL MUTATION**, unresolved HIGH/CRITICAL `0`.

## Truth/authority proof
- Tauri command accepts only the invoking `WebviewWindow`; no process/path/string/value payload can be supplied by frontend.
- The supervisor derives helper identity only from `current_exe()` sibling + fixed basename and rejects symlink/reparse/non-file targets.
- Exactly one production `Command::new` site exists and is statically enforced by the security gate.
- Child environment is cleared and no dynamic `.args`, `.env`, ambient env lookup or shell surface is admitted.
- Rust owns transport identity/lifecycle/size/framing only; semantic protocol admission stays in the canonical CP-0018 TypeScript raw decoder.
- Missing/crashed/nonzero/timed-out/invalid helper output reduces to `null` at the bridge; no fake READY signal is constructed.
- Runtime/provider/task/permission status remains presentation state and cannot mint CP permits, approvals, skills or mutation authority.

## Explicit residuals
- The sidecar is not yet packaged/signed/attested adjacent to the desktop executable. Hosted launch smoke therefore proves desktop startup and fail-closed behavior, not a packaged live sidecar session.
- No automatic polling/restart/health daemon is canonicalized; the current app performs a bounded one-shot status observation on load.
- Binary authenticity/update provenance and process containment policy beyond fixed sibling/reparse checks remain future release-hardening work.
- Provider reachability/authentication and VERIFIED model capability remain separate evidence domains.
- Existing RustSec warning-class dependency debt, CSP `style-src 'unsafe-inline'`, native/full E2E, visual/accessibility, installer/signing/updater and final-license residuals remain unchanged.

## Final approval state
This evidence authorizes creation of a minimal state/evidence-only **FINAL APPROVAL CANDIDATE / NOT CANONICAL** head. Product/runtime/workflow changes are not permitted in that mutation.

Canonical status still requires final exact-head Governance + Desktop Shell + HEDS, squash product merge, product post-merge validation, and documentation-only canonical closeout with its own gates/HEDS/merge/push validation.