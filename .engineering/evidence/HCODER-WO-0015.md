# Evidence Bundle — HCODER-WO-0015

**Work Order:** `HCODER-WO-0015`  
**Risk Class:** ELEVATED  
**Evidence state:** `PROMOTION APPROVED — FINAL EXACT-HEAD VALIDATION PENDING`  
**Base checkpoint:** `HCODER-CP-0014`  
**Base SHA:** `58442e5220a6242927c4103eded3366dc17d8938`  
**PR:** `#32`  
**Technical reviewed head:** `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`  
**HEDS technical review:** `5211566651` — APPROVED FOR PROMOTION CANDIDATE  
**Promotion candidate head:** `e3b24420f7057272fbe15a4ddae88ce65a190e50`  
**HEDS promotion review:** `5211785907` — APPROVED FOR FINAL APPROVAL MUTATION

## Executed acceptance
- Desktop source is isolated under `apps/desktop/`; no existing `hive_runtime/` implementation file was modified by WO-0015.
- Frontend uses one bounded Tauri invoke path: `get_desktop_snapshot`.
- Native command accepts no execution payload, revalidates the invoking WebView window as `main`, and returns presentation-only `DesktopSnapshot v1` state.
- Tauri capability `desktop-read-only` targets only `main` and grants zero plugin permissions.
- No Tauri shell/filesystem/process plugin, `std::process::Command`, generic command bridge, provider credential path, CP permit minting, skill activation, arbitrary file mutation, desktop-input mutation, remote-control authority or billing authority is introduced.
- Runtime/provider/Git/evidence/permission state remains truthful UNKNOWN/DISCONNECTED until later governed adapters exist.
- Pause/Emergency Stop/Take Control and unavailable navigation/task execution remain disabled without an actionable trusted session.
- npm and Cargo lockfiles are committed and CI uses exact locked installation/build paths.
- Windows release executable builds and survives a five-second launch smoke.

## Technical exact-head evidence
### Governance run `34982417149` (#187)
Exact checkout: `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`.
- Ubuntu: **256/256 PASS**.
- Windows Server 2025 HIGH_ASSURANCE: **56/56 PASS**.

### Desktop Shell run `34982422090` (#23)
Exact checkout: `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`.
- desktop security gate: PASS;
- command allowlist: `get_desktop_snapshot`;
- capability: `desktop-read-only`;
- window scope: `main`;
- capability permissions: `0`;
- Apple-specific font references: `0`;
- lockfiles committed;
- TypeScript: PASS;
- Vitest: **8/8 PASS**;
- Vite production build: PASS;
- npm audit: **0 vulnerabilities**;
- Rust unit tests: **3/3 PASS**;
- `cargo check --locked`: PASS;
- Tauri release build: PASS;
- `DESKTOP_LAUNCH_SMOKE=PASS`.

HEDS technical review `5211566651`: **APPROVED FOR PROMOTION CANDIDATE**, unresolved HIGH/CRITICAL **0**.

## Promotion exact-head evidence
Promotion candidate `e3b24420f7057272fbe15a4ddae88ce65a190e50` differs from the technical head only in documentation/governance. The final compare preserves historical Test & Benchmark Plan content and changes no application source, workflow, dependency manifest, lockfile, Tauri command/capability or security-gate implementation.

### Governance run `34985024390` (#189)
Exact checkout: `e3b24420f7057272fbe15a4ddae88ce65a190e50`.
- Ubuntu: **256/256 PASS**.
- Windows Server 2025 HIGH_ASSURANCE: **56/56 PASS**.

### Desktop Shell run `34985024599` (#25)
Exact checkout: `e3b24420f7057272fbe15a4ddae88ce65a190e50`.
- desktop security gate: PASS;
- TypeScript: PASS;
- Vitest: **8/8 PASS**;
- Vite production build: PASS;
- npm audit: **0 vulnerabilities**;
- pinned/checksummed `cargo-audit 0.22.2`: PASS;
- RustSec scan: command SUCCESS over **431 locked crate dependencies** and 1246 loaded advisories;
- Rust unit tests: **3/3 PASS**;
- `cargo check --locked`: PASS;
- Tauri release build: PASS;
- `DESKTOP_LAUNCH_SMOKE=PASS`.

HEDS promotion review `5211785907`: **APPROVED FOR FINAL APPROVAL MUTATION**, unresolved HIGH/CRITICAL **0**.

## RustSec warning-class residuals
The successful audit reports **7 allowed warnings**. They remain explicitly recorded rather than represented as a warning-free graph:
1. `proc-macro-error 1.0.4` — unmaintained — `RUSTSEC-2024-0370`.
2. `unic-char-property 0.9.0` — unmaintained — `RUSTSEC-2025-0081`.
3. `unic-char-range 0.9.0` — unmaintained — `RUSTSEC-2025-0075`.
4. `unic-common 0.9.0` — unmaintained — `RUSTSEC-2025-0080`.
5. `unic-ucd-ident 0.9.0` — unmaintained — `RUSTSEC-2025-0100`.
6. `unic-ucd-version 0.9.0` — unmaintained — `RUSTSEC-2025-0098`.
7. `glib 0.18.5` — unsoundness warning — `RUSTSEC-2024-0429`.

WO-0015 does not claim those transitive warnings are unreachable. Dependency refresh/target-chain analysis remains follow-up debt before any warning-free Rust supply-chain claim.

## Corrections
- `HCODER-WO-0015-CR-001` — Vite/Vitest configuration typing failure: **RESOLVED**.
- `HCODER-WO-0015-CR-002` — missing Tauri icon + bootstrap lock determinism: **RESOLVED**.
- `HCODER-WO-0015-CR-003` — app-command window-scope defense in depth: **RESOLVED**.
- `HCODER-WO-0015-CR-004` — unavailable UI affordances/fake readiness: **RESOLVED**.
- `HCODER-WO-0015-CR-005` — unnecessary Apple-specific font references: **RESOLVED**.

## Explicit residual boundaries
- RustSec warning-class transitive dependency debt remains as listed above.
- Desktop CSP still contains `style-src 'unsafe-inline'`; no `dangerouslySetInnerHTML` sink is admitted, but stricter style CSP is later hardening.
- Native launch is proven; pixel/screenshot visual validation and full desktop interaction E2E are not yet proven.
- `bundle.active=false`; installer, signing, updater, release package and rollback/roll-forward packaging evidence remain out of scope/unproven.
- Live runtime/provider/Git/evidence/permission adapters are not connected in WO-0015.
- No real provider credential, privileged computer-use mutation, remote control, automatic skill activation or autonomous billing/purchase path is approved.
- Final Hive Coder project license is still undecided; dependency/release attribution remains a release gate.

## Final approval mutation rule
DEC-019 / HCODER-CP-0015 are approved by the promotion evidence above, but the documentation mutation that records that approval must independently pass exact-head Governance + Desktop Shell and final HEDS before merge. No privilege expansion is part of this mutation.
