# Checkpoint Delta — HCODER-WO-0015

**Source checkpoint:** `HCODER-CP-0014`  
**Target checkpoint:** `HCODER-CP-0015`  
**Target state in this commit:** `CANDIDATE`  
**Technical head:** `9e212c6f8c959f3d3cb19cc5146485f39bd6c8fd`  
**PR:** `#32`  
**HEDS technical review:** `5211566651`

## Promotion boundary
Promote the first Windows-buildable Hive desktop shell and bounded read-only application bridge. The delta establishes the desktop substrate, `DesktopSnapshot v1`, one main-window-scoped read command, original Hive visual foundation, committed npm/Cargo lock graphs, dedicated desktop security gate and Windows native build/launch evidence.

## Canonical effects
- Tauri 2 + React/TypeScript/Vite becomes the approved first desktop-shell foundation if CP-0015 is finally promoted.
- `DesktopSnapshot v1` is presentation state only and grants no execution authority.
- `get_desktop_snapshot` is the only WO-0015 Tauri command and is restricted to the `main` window.
- The desktop capability grants zero plugin permissions.
- Future privileged desktop/runtime operations remain subordinate to the existing Permission & Control Plane and require later governed Work Orders.
- CP-0005 through CP-0014 security/authority decisions remain unchanged.

## Evidence basis
Exact technical head passed:
- Governance #187: Ubuntu **256/256 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**.
- Desktop Shell #23: frontend **8/8 PASS**, TypeScript/build/security gate/full npm audit PASS, npm vulnerabilities `0`, Rust **3/3 PASS**, RustSec audit command PASS, `cargo check --locked` PASS, Tauri release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS technical review found unresolved HIGH/CRITICAL findings: **0**.

## Exclusions and residuals
- RustSec still reports 7 warning-class transitive advisories; the graph is not claimed warning-free.
- CSP still allows `style-src 'unsafe-inline'`; stricter CSP remains future hardening.
- Launch smoke is not pixel/screenshot validation or full interaction E2E.
- Installer/signing/updater/release packaging remain unapproved and unproven.
- Live runtime/provider/Git/evidence/permission adapters are not connected.
- No privileged computer-use mutation, credentials, remote control, automatic skill activation, billing or purchases are authorized.
- Final Hive Coder project license remains undecided.

## Promotion rule
CP-0015 remains only `CANDIDATE` until this documentation/governance delta itself passes exact-head Governance + Desktop Shell, receives promotion HEDS with no unresolved HIGH/CRITICAL finding, and is subsequently marked APPROVED before squash merge and post-merge validation on `main`.
