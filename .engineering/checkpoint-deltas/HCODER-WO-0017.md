# Checkpoint Delta — HCODER-WO-0017

**Source checkpoint:** `HCODER-CP-0016`  
**Target checkpoint:** `HCODER-CP-0017`  
**Target state in this commit:** `APPROVED FOR SQUASH MERGE — FINAL EXACT-HEAD GATES PENDING`  
**Technical head:** `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef`  
**Promotion reviewed head:** `e2ae69e1be2f152eb9ce37b9b05f674dd072f5b5`  
**PR:** `#42`  
**HEDS technical review:** `5215028501`  
**HEDS promotion review:** `5215216401`

## Promotion boundary
Promote the first versioned Hive runtime observability presentation contract. The delta adds bounded runtime/provider/task/permission status reduction and strict JSON validation without connecting the desktop to a live Python child process and without adding any mutation/authorization surface.

## Canonical effects
- `RuntimeStatusSnapshot v1` becomes the approved presentation schema if CP-0017 is finally promoted.
- Runtime/provider/task/permission presentation records carry canonical Hive provenance.
- Provider catalog observation never becomes VERIFIED model capability evidence by itself.
- Unknown/unconnected permission state remains fail-closed rather than reading private control-plane internals.
- Strict decoding rejects unknown/duplicate fields, invalid enum/state values, fake READY provider summaries, boolean counters and unbounded input.
- Rejected status payloads can map to one fixed non-secret DEGRADED presentation snapshot.
- Existing CP-0005 through CP-0016 authorization and desktop privilege boundaries remain unchanged.

## Evidence basis
Exact technical head `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef` passed:
- Governance #225 (`35015244682`): Ubuntu **273/273 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**;
- Desktop Shell #61 (`35015244727`): security gate PASS, frontend **12/12 PASS**, npm audit **0 vulnerabilities**, Rust **11/11 PASS**, RustSec scan of **432** locked crates with **7 warning-class advisories** and no blocking vulnerability, `cargo check --locked` PASS, Tauri release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`;
- HEDS technical review `5215028501`: unresolved HIGH/CRITICAL findings **0**.

Exact promotion head `e2ae69e1be2f152eb9ce37b9b05f674dd072f5b5` passed:
- Governance #234 (`35016227601`): **SUCCESS**;
- Desktop Shell #70 (`35016227612`): **SUCCESS**;
- HEDS promotion review `5215216401`: **APPROVED FOR FINAL APPROVAL MUTATION**, unresolved HIGH/CRITICAL **0**.

The promotion delta from the technical head is documentation/evidence/governance-only.

## Correction
`HCODER-WO-0017-CR-001` MEDIUM is resolved in the technical candidate. The correction completed strict decoder/provenance/type/counter/fail-closed semantics without expanding authority.

## Exclusions and residuals
- No live desktop-to-Python status IPC or child-process lifecycle exists under WO-0017.
- Provider READY is catalog-observation state, not provider availability, authentication or capability certification.
- Permission counts are not exposed while no safe public observer exists.
- `RuntimeStatusSnapshot` is presentation data and cannot authorize an action.
- Seven warning-class RustSec advisories remain existing dependency debt.
- No provider/model execution, credential access, task/permission mutation, terminal/process bridge, file/Git mutation or computer-use mutation is approved.

## Promotion rule
DEC-021 / CP-0017 are approved for squash merge by this documentation-only mutation, subject to fresh exact-head Governance + Desktop Shell and final HEDS on the resulting PR head. Squash merge is allowed only with unresolved HIGH/CRITICAL findings = 0. CP-0017 becomes canonical only after the merged `main` SHA passes post-merge Governance + Desktop Shell and canonical closeout is recorded.
