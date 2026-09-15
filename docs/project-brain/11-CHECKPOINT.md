# Checkpoint — Hive Coder

**Canonical approved checkpoint:** `HCODER-CP-0014`  
**Promotion candidate:** `HCODER-CP-0015`  
**Candidate status:** `CANDIDATE`  
**Date:** 2026-09-15  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0015`  
**PR:** `#32`  
**Technical reviewed head:** `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`

## Canonical authority while candidate is under promotion
`HCODER-CP-0014` remains the latest APPROVED checkpoint until CP-0015 itself passes its promotion gates and receives a separate APPROVED mutation. All CP-0005 through CP-0014 authority/security boundaries therefore remain in force unchanged.

## CP-0015 candidate delta
- First Windows-buildable Hive Coder desktop shell under `apps/desktop/` using Tauri 2 + React/TypeScript/Vite.
- Original Hive visual foundation and workspace/status shell; no Apple proprietary assets, SF Symbols or Apple-specific font references.
- Versioned `DesktopSnapshot v1` read model with explicit `READY`, `UNKNOWN`, `DISCONNECTED` and `DEGRADED` presentation states.
- Exactly one desktop application command in WO-0015: `get_desktop_snapshot`.
- The command accepts no execution payload and rejects callers whose WebView window label is not `main`.
- Declarative Tauri capability `desktop-read-only` targets only `main` and grants zero plugin permissions.
- No Tauri shell/filesystem/process plugin, generic command bridge, arbitrary filesystem mutation, desktop-input mutation, provider credential path, remote-control authority, skill activation or billing/purchase authority is introduced.
- Safety controls remain visible but inactive when no actionable trusted session exists; unavailable product surfaces remain disabled rather than pretending readiness.
- npm/Cargo lockfiles are committed. Desktop CI validates exact locked graphs, security rules, TypeScript, tests, production web build, dependency audit, Rust tests/check, Windows Tauri release build and native launch smoke.

## Corrections staged for promotion
- `HCODER-WO-0015-CR-001`: Vite/Vitest configuration typing — RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-002`: deterministic Tauri icon + lock bootstrap — RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-003`: main-window read-model scope — RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-004`: truthful inactive desktop affordances — RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-005`: Apple-specific font-reference removal — RESOLVED IN CANDIDATE.

## Technical evidence already proven
Exact technical head `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`:
- Governance run `34982417149` (#187): Ubuntu **256/256 PASS**, Windows Server 2025 HIGH_ASSURANCE **56/56 PASS**.
- Desktop Shell run `34982422090` (#23): security gate PASS; TypeScript PASS; Vitest **8/8 PASS**; Vite production build PASS; npm audit **0 vulnerabilities**; Rust **3/3 PASS**; `cargo check --locked` PASS; Tauri release build PASS; `DESKTOP_LAUNCH_SMOKE=PASS`.
- RustSec scan command succeeded over 431 locked crate dependencies, while explicitly reporting 7 warning-class advisories. The dependency graph is therefore not claimed warning-free.
- HEDS technical review `5211566651`: **APPROVED FOR PROMOTION CANDIDATE**; unresolved HIGH/CRITICAL findings: **0**.

## Explicit residual boundaries
- Seven RustSec warning-class transitive advisories remain dependency debt and require later refresh/target-chain analysis before a warning-free supply-chain claim.
- Desktop CSP still permits `style-src 'unsafe-inline'`; stricter CSP remains later hardening.
- Native launch is proven, but screenshot/pixel fidelity validation and full desktop interaction E2E remain unproven.
- `bundle.active=false`; installer, signing, updater, production packaging and rollback/roll-forward release evidence remain unapproved.
- Live runtime/provider/Git/evidence/permission adapters are not connected by WO-0015.
- No real provider credentials, privileged computer-use mutation, remote control, automatic skill activation, autonomous billing/purchases or permission expansion is approved.
- Final Hive Coder project license remains undecided.

## Candidate promotion rule
CP-0015 remains `CANDIDATE` until this documentation/governance head independently passes exact-head Governance + Desktop Shell and receives promotion HEDS with no unresolved HIGH/CRITICAL finding. Only then may DEC-019/CP-0015 be mutated to APPROVED, revalidated again, marked ready and squash-merged. Post-merge Governance + Desktop Shell must pass on canonical `main` before WO-0015 is closed.

## Next necessary increment
No WO-0016 is authorized while CP-0015 is only CANDIDATE. After final promotion and post-merge validation, source-check CP-0015 before choosing the next NECESSARY product increment.
