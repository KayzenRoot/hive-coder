# DEC-024 — Desktop Runtime Status Supervisor Boundary

**Status:** APPROVED FOR SQUASH MERGE / NOT CANONICAL  
**Work Order:** `HCODER-WO-0020`  
**Source checkpoint:** `HCODER-CP-0019`  
**Target checkpoint:** `HCODER-CP-0020`  
**Technical head:** `86c6e956985e0b51e0f56b3568a3fe9db61fef90`  
**HEDS technical:** `5216871217`  
**Promotion head:** `bf76c2a451763d7bc361437028e819d2df5f97ba`  
**HEDS promotion:** `5216925860`

## Decision
Hive Coder may introduce exactly one audited desktop child-process observation boundary for runtime status. The process is not a generic executor. It is a fixed supervisor whose only admitted target is the CP-0019 status helper adjacent to the current Hive desktop executable.

## Process law
- Helper basename is fixed by platform and resolved only as a sibling of `current_exe()`.
- Symlink/reparse/non-file helper identity fails closed.
- The sole argument is fixed `--stdio-status-v1`.
- Child environment is cleared; frontend/model/task data cannot add arguments, executable paths or environment entries.
- Exactly one production `Command::new` site is admitted and statically enforced.
- stdin/stdout are piped, stderr is discarded, response is physically capped at the canonical CP-0018 `33,024`-byte response ceiling, and the child has a hard timeout/termination path.
- The request is the exact canonical CP-0018 `desktop-runtime` `status.snapshot` request.

## Tauri/UI law
- The only new Tauri command is argument-free `get_runtime_status_envelope` and remains bound to the authorized `main` window.
- Tauri capability `desktop-read-only` keeps zero plugin permissions; no shell/process plugin is admitted.
- The frontend may admit status only through `decodeRuntimeStatusEnvelope(raw)`; `JSON.parse(raw)` + semantic-parser bypass is forbidden.
- Invalid/missing/crashed/timed-out/noncanonical status yields no live runtime status, never fake READY.
- Runtime/provider/task/permission data is read-only System Truth presentation. It cannot enable Run/Pause/Emergency Stop/Take Control or any other mutation by itself.

## Truth law
- Null permission counters remain unknown; they are never rendered as zero observations.
- Provider and Permission Plane cards preserve canonical subsystem provenance from the validated snapshot.
- Provider READY remains a catalog observation, not provider reachability/authentication and not VERIFIED model capability.

## Authority law
This decision does not grant generic process/shell execution, provider/model execution, credential access, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, automatic skill activation or billing/purchase authority. The canonical Permission & Control Plane remains the mutation choke point.

## Explicitly not approved
- packaged/signed/attested sidecar distribution;
- automatic polling daemon, restart/health manager or generic process supervisor;
- dynamic executable/path/argv/env selection;
- live provider/authentication or VERIFIED model-capability claims;
- any privileged mutation path;
- installer/updater/release signing.

## Evidence
Technical exact head `86c6e956985e0b51e0f56b3568a3fe9db61fef90` passed Governance #263 (**288/288 Ubuntu**, **61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #99 (security gate PASS, frontend **26/26**, Rust **13/13**, locked audits/checks, Windows release build + launch smoke). HEDS `5216871217` approved promotion with unresolved HIGH/CRITICAL `0`.

Promotion head `bf76c2a451763d7bc361437028e819d2df5f97ba` changed only 7 documentation/evidence/governance files, then passed Governance #264 (**288/288 Ubuntu**, **61/61 Windows HIGH_ASSURANCE**) and Desktop Shell #100, including release build + launch smoke. HEDS `5216925860` approved the final state mutation with unresolved HIGH/CRITICAL `0`.

`HCODER-WO-0020-CR-001` and `HCODER-WO-0020-CR-002` are resolved.

## Approval result
DEC-024 is **APPROVED FOR SQUASH MERGE / NOT CANONICAL**. It becomes canonical only with CP-0020 after the final approval head passes exact-head gates/HEDS, product squash merge passes post-merge validation, and documentation-only canonical closeout is itself gated, reviewed, merged and push-validated.