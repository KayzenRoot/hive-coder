# Checkpoint — Hive Coder

**Checkpoint:** `HCODER-CP-0016`  
**Status:** APPROVED FOR SQUASH MERGE — NOT YET CANONICAL  
**Date:** 2026-09-15  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0016`  
**Issue:** `#34`  
**PR:** `#35` — FINAL APPROVAL CANDIDATE  
**Base checkpoint:** `HCODER-CP-0015`  
**Canonical base main SHA:** `330be799eedc3ea2478034039236d4a965f55274`  
**Technical reviewed head:** `07dda00f7371bcb02158f0c26258b03fa0dec88d`  
**Promotion reviewed head:** `50c280004b0d869e32fda8f20806082654e63255`

## Approved candidate state
- All CP-0005 through CP-0015 permission/security boundaries remain authoritative and unchanged.
- `DesktopSnapshot v2` adds truthful bounded workspace, Git and Hive evidence presentation state.
- The desktop exposes two named native commands: `get_desktop_snapshot` and `choose_workspace`.
- `choose_workspace` is initiated by explicit user interaction and accepts no caller-controlled target/path payload.
- The selected directory is validated/canonicalized inside the trusted Rust application layer and retained as application-owned session state. Its workspace ID is presentation identity, not a permission token.
- Workspace reads are root-contained, bounded and read-only. Parent traversal and static link/reparse escapes fail closed.
- Git branch/detached/HEAD observation reads bounded `.git` metadata directly. Hive does not execute `git` or another generic process for this surface.
- Hive checkpoint/evidence discovery is bounded. Symlinked evidence cannot silently masquerade as trusted in-root evidence.
- Physical text reads enforce actual byte ceilings before UTF-8 decoding.
- Tauri capability `desktop-read-only` remains restricted to window `main` with zero plugin permissions.
- No shell/filesystem/process plugin, filesystem mutation, terminal, provider credential/model execution, Python-runtime spawn, computer-use mutation, remote control, automatic skill activation, purchase/billing authority or CP permission expansion is introduced.

## Corrections
- `HCODER-WO-0016-CR-001` HIGH: **RESOLVED**. Root-containment/no-follow handling and malformed Git-ref fail-closed behavior were corrected and re-audited.
- `HCODER-WO-0016-CR-002` MEDIUM: **RESOLVED**. Physical bounded reads now enforce a hard byte ceiling and revalidate no-follow metadata before reading.

## Technical evidence
Exact technical head `07dda00f7371bcb02158f0c26258b03fa0dec88d`:
- Governance run `34996930586` (#203): Ubuntu **256/256 PASS**, Windows Server 2025 HIGH_ASSURANCE **56/56 PASS**.
- Desktop Shell run `34996930809` (#39): security gate PASS; TypeScript PASS; Vitest **12/12 PASS**; Vite production build PASS; npm audit **0 vulnerabilities**; RustSec scanned **432** locked crate dependencies with **7 allowed warning-class advisories** and no blocking vulnerability; Windows Rust **11/11 PASS**; `cargo check --locked` PASS; Tauri release build PASS; `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS technical review `5213079423`: **APPROVED FOR PROMOTION CANDIDATE**, unresolved HIGH/CRITICAL findings **0**.

## Promotion evidence
Exact promotion head `50c280004b0d869e32fda8f20806082654e63255`:
- Governance run `34997849021` (#204): **SUCCESS**, Ubuntu **256/256 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**.
- Desktop Shell run `34997849241` (#40): **SUCCESS**, security gate PASS, Vitest **12/12 PASS**, npm audit **0 vulnerabilities**, RustSec no blocking vulnerability with **7 allowed warning-class advisories**, Windows Rust **11/11 PASS**, `cargo check --locked` PASS, Tauri release build PASS, `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS promotion review `5213131975`: **APPROVED FOR FINAL APPROVAL MUTATION**, unresolved HIGH/CRITICAL findings **0**.
- Compare from technical reviewed head to promotion head contains documentation/evidence/governance changes only, with no application/workflow/dependency/lock/capability/permission drift.

## Decision
`DEC-020 — Trusted Workspace & Git Read Boundary` is APPROVED. This approval adds no privilege and remains non-canonical until squash merge plus post-merge validation on `main`.

## Explicit residual boundaries
- Native folder-picker click/select is not yet physically automated E2E.
- Unix-only link regressions are not exercised by the Windows desktop job; Windows reparse handling lacks a direct reparse fixture.
- Arbitrarily concurrent external workspace mutation is not transactionally frozen. This read-only presentation residual cannot be inherited by future privileged workspace/file operations without stronger handle-relative/no-follow capability I/O.
- Linked worktrees whose `.git` is an external pointer are intentionally DEGRADED.
- Seven RustSec warning-class transitive advisories remain dependency debt; the graph is not claimed warning-free.
- Runtime/provider/permission live adapters, write/terminal paths, installer/signing/updater, screenshot/pixel fidelity and full native interaction E2E remain unapproved.
- Final Hive Coder project license remains undecided.

## Final gates still required
This checkpoint is approved for squash merge but is **not canonical**. This documentation/governance-only approval mutation must pass exact-head Governance + Desktop Shell and final HEDS with unresolved HIGH/CRITICAL = 0. Then PR #35 may be squash-merged. CP-0016 becomes canonical/COMPLETE only after post-merge Governance + Desktop Shell pass on the resulting `main` SHA and canonical closeout records those receipts.

## Next increment rule
WO-0017 may remain technically staged, but it may not be promoted until CP-0016 is canonical on `main` and its stacked base is reconciled to the canonical merge.