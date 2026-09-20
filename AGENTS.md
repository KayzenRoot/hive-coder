# AGENTS.md — Hive Coder

## Source hierarchy
Read canonical truth in this order before implementation or review:
1. current accepted `docs/project-brain/11-CHECKPOINT.md` / proven production state;
2. `docs/project-brain/10-DECISIONS-LEDGER.md` plus approved ADRs under `docs/project-brain/adrs/`;
3. `docs/project-brain/03-SCOPE.md` and `docs/project-brain/02-REQUIREMENTS.md`;
4. `docs/project-brain/09-DEFINITION-OF-DONE.md`;
5. `docs/project-brain/04-ARCHITECTURE.md`;
6. `docs/project-brain/05-SECURITY.md`;
7. active Work Order / Context Lock;
8. remaining Project Brain / `.engineering` sources.

Material contradictions are recorded, not silently resolved. Git/code/tests/evidence beat conversation memory.

## GEF V1 Universal mode
Hive Coder is adopted as a BROWNFIELD repository under GEF Bootstrap V1.0.0. GEF wraps the existing project additively and must not rewrite historical work into fake GEF Work Orders/checkpoints/evidence.

Canonical lifecycle:
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> EXACT-HEAD AUDIT -> CHECKPOINT DELTA -> MERGE -> NEXT`.

For substantial work use stable Work Order IDs. Prefer the smallest sufficient context radius and compile executor acceleration capsules rather than forcing repeated whole-repository rediscovery.

## Review law
Verdicts are `APPROVED | CORRECTION_REQUIRED | BLOCKED`. APPROVED requires exact candidate SHA, required gates complete, CRITICAL=0, HIGH=0, no unresolved scope/preservation/evidence mismatch and no stale-head mismatch.

Every review response must also deliver the next executable Codex prompt as a generated PDF. `CORRECTION_REQUIRED` stays in the same Work Order. No new increment begins before the reviewed predecessor is objectively accepted.

## Authority rules
- Models/tools cannot mint approvals, permissions, trusted evidence or competence.
- Computer-use mutation remains behind the approved Permission & Control Plane.
- New architecture/toolchain authority requires a governed decision/checkpoint.
- Never silently rewrite historical Decisions or Context Locks.
- Never weaken tests/security/governance to obtain green CI.
- Never expose secrets discovered during repository inspection.

## Brownfield preservation rules
Preserve existing architecture, history, tests, CI, release semantics and naming unless a governed migration explicitly changes them. No mass-formatting or module renaming for GEF aesthetics. Legacy facts may be mapped, never retroactively certified.

## Cross-chat continuation
If the user says `continue`, `continue do chat anterior`, or equivalent for Hive Coder:
1. Open GitHub Issue `#30` first.
2. Reconcile it against canonical Checkpoint, Decisions/ADRs, active Work Order/PR and exact-head CI/HEDS.
3. Canonical Git evidence wins if Issue #30 is stale.
4. Continue autonomously from its NEXT EXACT ACTIONS.

## Current execution state
`HCODER-CP-0025 — Native package matrix evidence` is **CANONICAL / SEALED**, and it is the authoritative checkpoint while `HCODER_CP_0025_EFFECTIVE` holds. `docs/project-brain/11-CHECKPOINT.md` selects the checkpoint by predicate and remains the source of truth for that question; this section is a summary of it, not an independent authority.

Canonical state:
- Checkpoint ladder: `HCODER-CP-0025` / `DEC-029` (native package matrix evidence) ← `HCODER-CP-0024` / `DEC-028` (distribution version, channel and update boundaries) ← `HCODER-CP-0023` / `DEC-027` (governed Git staging). Each is effective only under its own predicate, and no repository text asserts that a predicate holds.
- Canonical `main` base at the time of writing: `1a56224eeb9bc07f032df1ede23bdda9d74f8d12` (`HCODER-WO-0025` closeout seal), post-validated on that exact `main` by Governance, Desktop Shell and Native Package Matrix.
- What `CP-0025` admits: the declared six native package targets — Windows `msi`+`nsis`, macOS `app`+`dmg`, Linux `appimage`+`deb` — produced deterministically under CI and bound to a closed `hive-package-inventory-v1` manifest. A digest proves byte identity and integrity for evidence transport, and nothing more.
- What it does not admit: signing, notarization, publisher authenticity, release or tag creation, publication, updater transport, installation, restart or rollback. `bundle.active` remains `false`, and nothing here is evidence that Hive Coder is signed, installable or production-distributable.

Runtime authority summary: `HCODER-WO-0023` governed Git staging — exactly `Capability.GIT_WRITE` / `git_stage_paths_v1` — is **SEALED / CANONICAL** under `HCODER-CP-0023` and is no longer an in-flight increment. Workspace file mutation remains bounded to the `CP-0021` create-only `write_file_v1` and the `CP-0022` `replace_file_v1` adapters, both under `Capability.FILESYSTEM_WRITE`, both mandatory trusted-approval gated, both permit-bound and single-use; the `CP-0022` guarantee is bounded-race atomic replacement, explicitly **not** strict CAS. Append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, generic filesystem mutation, shell/terminal/process execution, Tauri/desktop write commands, provider/model execution or credentials, Cua/computer-use mutation beyond prior governed boundaries, remote control, automatic skill activation and billing/purchase authority remain unapproved.

Earlier checkpoint receipts (including `HCODER-CP-0022`, its closeout exact head and its HEDS review, and `CP-0020` and prior) remain historically recorded in their closeout evidence files under `.engineering/evidence/` and are not restated here.

### GEF V1 universal adoption
GEF V1 universal is adopted; review mode is HEDS_DELTA_EXACT_HEAD and proof carry-forward still operates in shadow assurance. The source drift recorded at adoption start (`11-CHECKPOINT.md` still declaring `HCODER-CP-0021`, while Git history contained later proven CP-0022/PLATFORM-001 evidence) has since been reconciled on this line of development, and the same reconciliation has now been carried forward past `CP-0022`/`CP-0023`/`CP-0024` to the declared `CP-0025`. Read `.engineering/gef/GEF-PROJECT-MASTER.md`, `.engineering/gef/GEF-UNIVERSAL-ADOPTION.md` and `.engineering/gef/GEF-UNIVERSAL-CHECKPOINT.json` for the adoption map, and the `.engineering/gef/` protocols plus `.engineering/gef/GEF-PROJECT-PROFILE.json` for execution, review and evidence law.

### In-flight increments (not checkpoints, not canonical-complete)
- `HCODER-PLATFORM-001` (Issue #63) native validation matrix is canonical on `main`; its ledger records **CANONICAL / PROVEN_CI MATRIX COMPLETE**. Launch smoke remains PROVEN_CI on Windows only. Release package evidence is now proven under `HCODER-CP-0025`; package **install** behaviour remains UNPROVEN on all platforms, and unsigned packages remain undistributable.
- `HCODER-WO-0026` (Issue `#85`, slice `HCODER-DIST-001C`) release trust substrate is ACTIVE as a candidate in a Draft PR: the `hive-release-provenance-v1` contract, the offline validator `tools/desktop/release_provenance.py`, the `Protected Release` lane and `DEC-030`, which is **PROPOSED / NOT CANONICAL**. No `HCODER-CP-0026` may be claimed from it, and its credential-bearing stages are structurally present but unexercised: no signing credential, no protected environment and no notarization credential exist on the host.

### NEXT EXACT ACTIONS
1. Continue the active Work Order from its own Context Lock and Work Order sources; do not infer scope from historical branches.
2. Require exact-head `Governance` + `Desktop Shell` + `Native Package Matrix` + `Protected Release` preflight on every promotion head; any new head invalidates old exact-head evidence.
3. Perform HEDS with unresolved HIGH/CRITICAL `0/0` before promotion.
4. Before any credentialed release stage runs, the external provisioning named in the Work Order's executor brief must exist and be proved by the environment-protection probe: publisher signing identity, Apple Developer notarization credentials, and GitHub release environments with required reviewers that cannot be bypassed by admins. Report credential class, documented slot name and verification condition — never a value, and never a request for one.
5. Refresh Issue #30 with fully sealed receipts once the active Work Order reaches a governed closeout.
