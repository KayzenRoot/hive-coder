# HCODER-WO-0001 — Source Pack and GEF/HEDS governance bootstrap

**TASK CLASS:** T3  
**CONTEXT RADIUS:** C3  
**RISK:** STANDARD  
**BRANCH:** `governance/HCODER-WO-0001-source-pack`  
**BASE SHA:** `634527dae51f3e04884b145045e845be00a89650`  
**ISSUE:** `#1`

## OBJECTIVE
Create the initial canonical Source Pack and install the current HIVE-style GEF V1 prompt + HEDS Delta review workflow before any product implementation.

## CONTEXT
New empty repository for Hive Coder. Product direction already approved at discovery level: separate product; Open Interpreter + Cua preferred foundations; premium original Hive desktop UX; OpenCode Go is an important provider path.

## SCOPE
Canonical project brain, GEF execution/review/evidence contracts, Work Order/Correction/Review/Evidence/Context Lock templates, executor/reviewer/correction prompts, PR/issue templates, CODEOWNERS and minimal governance CI.

## OUT OF SCOPE
Any runtime/UI/provider/Open Interpreter/Cua product implementation; dependency installation; packaging; final license choice; production claims.

## FILES / SOURCES TO READ
`README.md`; all `docs/project-brain/*`; `.engineering/gef/*`; templates/prompts created by this increment.

## REQUIREMENTS
Preserve source hierarchy, exact-head evidence, delta-first review, same-WO corrections, fail-closed UNKNOWN, and no advancement before approval.

## ARCHITECTURE RULES
Governance artifacts must not hard-code Hive product-specific runtime assumptions. External foundations remain behind future Hive-owned adapters.

## CONSTRAINTS
No fabricated implementation state. No copying old Hive ruleset IDs/blockers. No product code.

## ACCEPTANCE CRITERIA
Required Source Pack files exist; GEF_V1/HEDS_DELTA are declared; templates contain required Work Order fields; Governance workflow verifies canonical files and JSON; checkpoint clearly distinguishes proven vs planned state.

## TESTS
Git delta inspection; required-file presence; JSON parse validation; GitHub Governance workflow on PR.

## DELIVERABLES
Source Pack + governance contracts + issue/branch/PR + exact-head review evidence.

## REVIEW FORMAT
Brazilian-Portuguese HEDS Delta review with exact head and verdict.

## STOP CONDITION
Stop at bootstrap candidate review: `APPROVED | CORRECTION REQUIRED | BLOCKED`. Do not start product implementation.
