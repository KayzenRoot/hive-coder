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

## Current execution state at universal-adoption baseline
Main baseline at adoption start: `ccfed1f960c80dc58e4f45cb627451e77c7d5a79`.

Known source drift: the canonical checkpoint document still declares `HCODER-CP-0021`, while Git history/main contains later proven CP-0022/PLATFORM-001 evidence. Universal adoption records this drift and does not fabricate a checkpoint promotion.

Active non-canonical implementation increment: `HCODER-WO-0023 — governed Git staging boundary`, Draft PR `#69`, branch `feat/HCODER-WO-0023-git-stage-capability`. It must reconcile the adopted main before further Codex execution.

Read `.engineering/gef/GEF-PROJECT-MASTER.md`, `.engineering/gef/GEF-UNIVERSAL-ADOPTION.md` and `.engineering/gef/GEF-UNIVERSAL-CHECKPOINT.json` for the GEF adoption map.
