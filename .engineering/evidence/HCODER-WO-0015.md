# Evidence Bundle — HCODER-WO-0015

**Work Order:** `HCODER-WO-0015`  
**Risk Class:** ELEVATED  
**Evidence state:** `TECHNICAL EVIDENCE VERIFIED — PROMOTION CANDIDATE`  
**Base checkpoint:** `HCODER-CP-0014`  
**Base SHA:** `58442e5220a6242927c4103eded3366dc17d8938`  
**PR:** `#32`  
**Technical reviewed head:** `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`  
**HEDS technical review:** `5211566651` — APPROVED FOR PROMOTION CANDIDATE

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

## Exact-head evidence inventory
### Governance run `34982417149` (#187)
Exact checkout: `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`.
- Ubuntu `source-pack` job `104425829741`: **256/256 PASS**.
- Windows Server 2025 `control-plane-windows` job `104425829548`: **56/56 PASS**.
- Existing CP-0005 through CP-0014 control-plane/runtime regression remains green.

### Desktop Shell run `34982422090` (#23)
Exact checkout: `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`.

`desktop-web` job `104425835308`:
- desktop security gate: PASS;
- command allowlist: `get_desktop_snapshot`;
- capability: `desktop-read-only`;
- window scope: `main`;
- capability permissions: `0`;
- Apple-specific font references: `0`;
- lockfiles committed and package graph verified;
- TypeScript typecheck: PASS;
- Vitest: **8/8 PASS** across 2 files;
- Vite production build: PASS;
- full npm dependency audit: **0 vulnerabilities**.

`desktop-windows` job `104425834840`:
- Rust `1.98.1`, warnings denied by CI: PASS;
- pinned/checksummed `cargo-audit 0.22.2`: installed successfully;
- RustSec scan: command SUCCESS over **431 locked crate dependencies** and 1246 loaded advisories;
- Rust unit tests: **3/3 PASS**;
- `cargo check --locked`: PASS;
- Tauri release build: PASS;
- built executable: `apps/desktop/src-tauri/target/release/hive-coder-desktop.exe`;
- launch smoke: `DESKTOP_LAUNCH_SMOKE=PASS` after five-second live-process check.

## RustSec warning-class residuals
The successful audit reports **7 allowed warnings**. They are recorded rather than represented as a warning-free graph:
1. `proc-macro-error 1.0.4` — unmaintained — `RUSTSEC-2024-0370`.
2. `unic-char-property 0.9.0` — unmaintained — `RUSTSEC-2025-0081`.
3. `unic-char-range 0.9.0` — unmaintained — `RUSTSEC-2025-0075`.
4. `unic-common 0.9.0` — unmaintained — `RUSTSEC-2025-0080`.
5. `unic-ucd-ident 0.9.0` — unmaintained — `RUSTSEC-2025-0100`.
6. `unic-ucd-version 0.9.0` — unmaintained — `RUSTSEC-2025-0098`.
7. `glib 0.18.5` — unsoundness warning — `RUSTSEC-2024-0429`.

WO-0015 does not claim those transitive warnings are unreachable. Dependency refresh/target-chain analysis remains follow-up debt before any claim of a warning-free Rust supply chain.

## Corrections
- `HCODER-WO-0015-CR-001` — Vite/Vitest configuration typing failure: RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-002` — missing Tauri icon + bootstrap lock determinism: RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-003` — app-command window-scope defense in depth: RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-004` — unavailable UI affordances/fake readiness: RESOLVED IN CANDIDATE.
- `HCODER-WO-0015-CR-005` — unnecessary Apple-specific font references: RESOLVED IN CANDIDATE.

## HEDS technical verdict
Review `5211566651` audited governance, architecture, permission/control-plane separation, command surface, truthful state, supply chain, correctness, Windows buildability, regression, evidence integrity and safety UX.

Verdict: **APPROVED FOR PROMOTION CANDIDATE**.  
Unresolved HIGH findings: **0**.  
Unresolved CRITICAL findings: **0**.

## Explicit residual boundaries
- RustSec warning-class transitive dependency debt remains as listed above.
- Desktop CSP still contains `style-src 'unsafe-inline'`; no `dangerouslySetInnerHTML` sink is admitted, but stricter style CSP is later hardening.
- Native launch is proven; pixel/screenshot visual validation and full desktop interaction E2E are not yet proven.
- `bundle.active=false`; installer, signing, updater, release package and rollback/roll-forward packaging evidence remain out of scope/unproven.
- Live runtime/provider/Git/evidence/permission adapters are not connected in WO-0015.
- No real provider credential, privileged computer-use mutation, remote control, automatic skill activation or autonomous billing/purchase path is approved.
- Final Hive Coder project license is still undecided; dependency/release attribution remains a release gate.

## Proposed checkpoint delta
Promote `HCODER-CP-0014` -> candidate `HCODER-CP-0015` only for the read-only desktop shell foundation and its CI/security boundary. No privilege expansion is part of the delta.
