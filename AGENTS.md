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
`HCODER-CP-0022 — Governed Existing-File Replacement Capability` is **APPROVED / CANONICAL**.

Canonical state:
- `HCODER-CP-0022` / `DEC-026 — Governed Existing-File Replacement Capability` is **CANONICAL**, promoted by closeout merge `795ed101eaf5d770f63a96db7f01a82369be34f1`.
- Canonical base `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`.
- Product PR #62 squash-merged as `06c68611a42e07b85ae765145d94bb613110ac14`; post-merge Governance #324 and Desktop Shell #160 passed.
- CP-0022 closeout exact head `a777ac207b42059a33ce9d73d8287122ff43c0a9` passed Governance #325 and Desktop Shell #161 with HEDS closeout review `5222180870`, unresolved HIGH/CRITICAL `0/0`.
- `HCODER-WO-0022-CR-001` is resolved; the canonical guarantee is bounded-race atomic replacement, explicitly **not** strict CAS.
- Hive runtime has two privileged workspace file mutation adapters: CP-0021 create-only `write_file_v1` and CP-0022 `replace_file_v1`, both under `Capability.FILESYSTEM_WRITE`, both mandatory trusted-approval gated, both permit-bound and single-use.

CP-0022 authority remains replacement-only: append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, generic filesystem mutation, shell/terminal/process execution, Tauri/desktop write commands, provider/model execution or credentials, Cua/computer-use mutation beyond prior governed boundaries, remote control, automatic skill activation and billing/purchase authority remain unapproved. Git mutation authority is governed separately by `HCODER-WO-0023` (below) and is not part of CP-0022.

Earlier checkpoint receipts (CP-0020 and prior) remain historically recorded in their closeout evidence files under `.engineering/evidence/` and are not restated here.

### GEF V1 universal adoption
GEF V1 universal is adopted; review mode is HEDS_DELTA_EXACT_HEAD and proof carry-forward still operates in shadow assurance. The source drift recorded at adoption start (`11-CHECKPOINT.md` still declaring `HCODER-CP-0021`, while Git history contained later proven CP-0022/PLATFORM-001 evidence) has since been reconciled on this line of development, which now declares CP-0022. Read `.engineering/gef/GEF-PROJECT-MASTER.md`, `.engineering/gef/GEF-UNIVERSAL-ADOPTION.md` and `.engineering/gef/GEF-UNIVERSAL-CHECKPOINT.json` for the adoption map, and the `.engineering/gef/` protocols plus `.engineering/gef/GEF-PROJECT-PROFILE.json` for execution, review and evidence law.

### In-flight increments (not checkpoints, not canonical-complete)
- `HCODER-PLATFORM-001` (Issue #63) native validation matrix is canonical on `main`; its ledger records **CANONICAL / PROVEN_CI MATRIX COMPLETE**. Launch smoke remains PROVEN_CI on Windows only, and release package/install remains UNPROVEN on all platforms.
- `HCODER-WO-0023` (Issue #68, PR #69 Draft) governed Git staging is an active Work Order with its own Context Lock. Its bounded Git index-mutation authority — exactly `Capability.GIT_WRITE` / `git_stage_paths_v1` — **is implemented** and covered by activated acceptance gates, including native Windows/Linux/macOS staging proof. It is **not promoted**: `DEC-027` remains PROPOSED, no HEDS is approved, and the PR remains Draft.

### NEXT EXACT ACTIONS
1. Continue the active Work Order from its own Context Lock and Work Order sources; do not infer scope from historical branches.
2. Require exact-head Governance + Desktop Shell on every promotion head; any new head invalidates old exact-head evidence.
3. Perform HEDS with unresolved HIGH/CRITICAL `0/0` before promotion.
4. Refresh Issue #30 with fully sealed receipts once the active Work Order reaches a governed closeout.
