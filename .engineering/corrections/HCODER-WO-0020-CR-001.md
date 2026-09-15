# HCODER-WO-0020-CR-001 — Fix sidecar child working directory

**Severity:** MEDIUM  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0020`

## Finding
The first canonical supervisor candidate fixed the sidecar executable identity, mode, request and environment, but `std::process::Command` would still inherit the desktop process working directory.

That inherited working directory is implicit process input outside the intended fixed supervisor contract. A desktop process launched from a user-controlled directory could therefore pass contextual filesystem influence into a future packaged helper even though explicit arguments/environment are locked down.

## Correction
- Derive `sidecar_dir` only from the already validated fixed sibling sidecar path.
- Set `.current_dir(sidecar_dir)` on the child process.
- Keep sidecar path, mode, request and environment fixed and non-caller-controlled.
- Do not add any frontend/model/task working-directory input.

## Authority impact
None. The correction removes an implicit input; it grants no process selection, filesystem mutation, provider/model execution or Permission & Control Plane authority.

## Closure gate
Resolved only if the corrected exact head passes Governance + Desktop Shell and HEDS finds no unresolved HIGH/CRITICAL issue in the supervisor boundary.
