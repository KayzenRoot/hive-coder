# HCODER-WO-0025 — Executor Brief

**Status:** FROZEN EXECUTION BRIEF — the contract it describes is materialized in source; whether a given head satisfies its obligations is external evidence
**Base:** `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Issue:** `#82`  
**Prior reviewed-head facts:** historical only; mutable current review and gate state is external in the active PR and Issues #30 and #82.

## Start here
Read, in order:
1. `.engineering/work-orders/HCODER-WO-0025.md`
2. `.engineering/context-locks/HCODER-WO-0025.md`
3. `.engineering/prebuilt/HCODER-WO-0025-IMPLEMENTATION-PACK.md`
4. `.engineering/prebuilt/HCODER-WO-0025-ACCEPTANCE-SECURITY-MAP.md`
5. `.engineering/evidence/HCODER-WO-0025.md`
6. `.github/workflows/desktop-shell.yml` (the lane conventions this workflow must parallel, not weaken)

## Mandatory order for completion work
A. Keep `apps/desktop/src-tauri/tauri.conf.json` untouched. No tracked `bundle.icon`, no `bundle.active` change, no version bump.
B. Use the pinned CLI's split-build model: `build --no-bundle`, then `bundle --bundles <targets> --config <overlay>`.
C. Keep the overlay runner-local, non-tracked, never uploaded, and prove tracked source unchanged afterwards.
D. Interrogate `tauri -- build --help` and `tauri -- bundle --help` on each native runner and support the targets that runner advertises; do not assume cross-platform parity of `--bundles` values.
E. Bound every artifact discovery to an explicit package root created fresh per job. No repository-wide wildcards.
F. Preserve the Linux GTK/rfd feature requirement used by the existing Linux lane.
G. Never execute an installer or an AppImage as acceptance.
H. Keep digests as integrity evidence only; never describe them as signing or publisher authenticity.
I. Keep every existing Governance and Desktop Shell lane green and unweakened.

## Forbidden shortcuts
No signing, codesign, notarization, stapling, key or secret access; no release/tag creation or GitHub Release upload; no updater plugin, endpoint or artifact; no product network fetch; no install/restart/rollback path; no new dependency or plugin; no app-icon or other product-artifact config change; no installer execution; no matrix reduction without an explicit governed decision; no weakening or skipping of an existing gate.

## Definition of Done for execution
Inventory tool and its adversarial tests pass; `version_drift.py` reports `LOCKED`; `security_gate.py` passes; the desktop and Python suites stay green; the new workflow is exact-head aware, root-bounded and deterministic; each package lane's native canary evidence is posted externally to the PR and Issue #82; Governance, Desktop Shell and Native Package Matrix are all green on the final exact head; and an independent HEDS review reports unresolved HIGH/CRITICAL `0/0`.

## STOP
If any native lane requires a tracked config or icon-format change, a new dependency, signing/release authority, installer execution, or a reduced matrix, STOP and report the exact native evidence instead of making that change. Do not begin `HCODER-DIST-001C`.
