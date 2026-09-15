# Evidence Bundle — HCODER-WO-0016

**Work Order:** `HCODER-WO-0016`  
**Issue:** `#34`  
**PR:** `#35`  
**Canonical base:** `330be799eedc3ea2478034039236d4a965f55274` (`HCODER-CP-0015`)  
**Technical reviewed head:** `07dda00f7371bcb02158f0c26258b03fa0dec88d`  
**Status:** APPROVED FOR SQUASH MERGE — FINAL GATES PENDING

## Objective evidence
WO-0016 turns the static Workspace shell into a truthful live read surface without adding a privileged execution path. The user explicitly chooses a folder through the native picker. The frontend supplies no path argument. The trusted Rust application layer validates/canonicalizes the selected directory, retains application-owned workspace identity, and emits bounded presentation state through `DesktopSnapshot v2`.

The approved read surface observes:
- bounded workspace identity/markers/top-level count;
- Git repository, branch/detached state and HEAD by bounded direct `.git` metadata reads, never an external `git` process;
- bounded Hive checkpoint/evidence presence;
- explicit provenance plus READY/UNKNOWN/DISCONNECTED/DEGRADED states.

No terminal/shell command, generic process dispatch, filesystem mutation, provider credential/model execution, runtime spawning, desktop-input mutation, remote control, automatic skill activation, billing/purchase path or permission expansion is introduced.

## Native command boundary
Approved commands at the technical head:
- `get_desktop_snapshot`
- `choose_workspace`

Both commands independently require WebView window label `main`. `choose_workspace` accepts no caller-controlled path or payload. Tauri capability `desktop-read-only` remains scoped to `main` with zero plugin permissions.

## Dependency evidence
`rfd = 0.17.2` is exact-pinned with default features disabled and resolved in the committed Cargo lock. Its upstream `0.17.2` manifest declares license `MIT`. No Tauri filesystem/shell/process plugin and no broad Git library were added.

## Correction evidence
### HCODER-WO-0016-CR-001 — HIGH — RESOLVED
Initial root-containment review found link-following risk in evidence enumeration, dangling-link ambiguity and malformed empty branch-ref handling. Correction commit `edea51a6d5fae051be43754179f33f9f1e4a316c` changed only `apps/desktop/src-tauri/src/lib.rs` and introduced no-follow metadata handling, fail-closed dangling links, empty-branch rejection and deterministic regressions.

### HCODER-WO-0016-CR-002 — MEDIUM — RESOLVED
Review found that metadata-size validation preceded an unbounded `read_to_string()`. Correction commit `d42c280ee1e7e5295119f07112de72c5ab9f2ce3` changed only `apps/desktop/src-tauri/src/lib.rs`, adding no-follow validation plus a physical `max_bytes + 1` read limiter before UTF-8 decoding and a regression test.

## Exact-head Governance evidence
Run `34996930586` (#203) on `07dda00f7371bcb02158f0c26258b03fa0dec88d`: **SUCCESS**.
- Ubuntu source-pack: **256/256 PASS**.
- Windows Server 2025 HIGH_ASSURANCE control-plane: **56/56 PASS**.

## Exact-head Desktop Shell evidence
Run `34996930809` (#39) on the same exact head: **SUCCESS**.

Security gate:
- `DESKTOP_SECURITY_GATE=PASS`
- `TAURI_COMMANDS=choose_workspace,get_desktop_snapshot`
- `FRONTEND_INVOKES=2`
- `WINDOW_SCOPE=main`
- `CAPABILITY_PERMISSIONS=0`
- `WORKSPACE_SELECTION_ARGS=0`
- `FILESYSTEM_MUTATION_PRIMITIVES=0`
- `GENERIC_PROCESS_EXECUTION=0`
- `APPLE_SPECIFIC_FONT_REFERENCES=0`
- committed lockfiles verified.

Frontend/native validation:
- TypeScript typecheck PASS.
- Vitest **12/12 PASS**.
- Vite production build PASS.
- npm audit: **0 vulnerabilities**.
- RustSec scanned **432** locked crate dependencies; no blocking vulnerability, **7 allowed warning-class advisories** remain explicit debt.
- Windows Rust unit tests: **11/11 PASS**.
- `cargo check --locked`: PASS with warnings denied.
- Tauri Windows release build: PASS.
- `DESKTOP_LAUNCH_SMOKE=PASS`.

## HEDS technical review
PR review `5213079423`, anchored to exact head `07dda00f7371bcb02158f0c26258b03fa0dec88d`: **APPROVED FOR PROMOTION CANDIDATE**. Unresolved HIGH/CRITICAL findings: **0**.

## Promotion evidence
Exact promotion head `50c280004b0d869e32fda8f20806082654e63255` passed Governance `34997849021` (#204) and Desktop Shell `34997849241` (#40). Ubuntu remained **256/256 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**, frontend **12/12 PASS**, Windows Rust **11/11 PASS**, npm audit **0 vulnerabilities**, RustSec had no blocking vulnerability with seven warning-class advisories, Tauri release build passed and `DESKTOP_LAUNCH_SMOKE=PASS`.

HEDS promotion review `5213131975` verified that the promotion delta from technical head `07dda00f7371bcb02158f0c26258b03fa0dec88d` is documentation/evidence/governance-only and returned **APPROVED FOR FINAL APPROVAL MUTATION** with unresolved HIGH/CRITICAL findings **0**.

## Explicit residual boundaries
- Native folder-picker click/select interaction is compile/launch proven but not physically automated E2E.
- Two Unix-only symlink regressions do not execute in the Windows desktop job; Windows reparse detection is implemented but has no direct reparse fixture yet.
- Standard path-based observation cannot make a concurrently mutating external workspace transactionally immutable. Static link/reparse admission fails closed and actual read size is physically bounded. Before any future privileged workspace/file operation relies on this authority, handle-relative/no-follow capability I/O requires a separately reviewed design.
- Linked-worktree `.git` pointer files intentionally report DEGRADED rather than following an external gitdir.
- The Rust graph is not claimed warning-free; seven warning-class RustSec advisories remain dependency debt.
- Runtime/provider/permission live adapters, terminal/write paths, installer/signing/updater and full interaction/visual E2E remain outside WO-0016.

## STOP status
Technical implementation and promotion review are complete. `DEC-020` and CP-0016 are approved for the merge candidate, but the Work Order is **not canonical/complete yet**. Remaining gates are fresh exact-head Governance + Desktop Shell on this final approval mutation, final HEDS, squash merge, and post-merge Governance + Desktop Shell on canonical `main`.