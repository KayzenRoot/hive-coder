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

## Standalone development: no separately installed HIVE
The repository operates independently of the separately installed `KayzenRoot/hive` HIVE context/indexing service. It is **not** a source prerequisite, MCP/context provider, Docker dependency, execution gate or fallback for any Hive Coder Work Order. Do not require its localhost API, `HIVE_PROJECTS_ROOT`, project/task registry, corpus, checkpoint tool, mounts, database, Redis or any HIVE preflight. Compile small context directly from the accepted Project Brain/ADRs, active Work Order/Context Lock and exact Git/code/tests/CI evidence. If local HIVE is absent because it was uninstalled, that is expected, not BLOCKED or a failed check. Preserve the product's own `hive_runtime`, internal protocols and Cua Driver's unrelated MCP integration. This user-directed change is proposed in HCODER-OPS-0001 / DEC-032 and supersedes the unmerged external-HIVE-context proposal PR #94 when approved; historical records remain unchanged.

## Owner-only GitHub workflow (DEC-033 proposed under HCODER-OPS-0001)
No collaborator invitation, second GitHub account, mandatory independent human review or paid review bot may be a prerequisite for current or future Hive Coder development. `KayzenRoot` retains sole responsibility for PR review decisions, guarded merges and acceptance. Keep reviewer and implementer roles as separately documented tasks: when the same account performs them, label the review **OWNER_SELF_AUDIT / NOT_INDEPENDENT**, never manufacture an independent HEDS reviewer/APPROVE. Record an exact-head substantive scope/architecture/security/negative-test audit, applicable GitHub Actions and unresolved findings. For HIGH_ASSURANCE require extra explicit owner risk acceptance and fail-closed challenge evidence. GitHub rule #23768014 already requires 0 approvals but enforces 13 CI checks, base freshness, blocking-thread resolution and squash-only merge; do not weaken these. External bots/reviewers are optional diagnostic input, not acceptance authority. Once this operational PR is accepted, DEC-033 prospectively supersedes the second-account review dependency in living protocols and active WO-0027 Delta 004. Accepted historical independent reviews remain immutable.

## GEF V1 Universal mode
Hive Coder is adopted as a BROWNFIELD repository under GEF Bootstrap V1.0.0. GEF wraps the existing project additively and must not rewrite historical work into fake GEF Work Orders/checkpoints/evidence.

Canonical lifecycle:
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> EXACT-HEAD AUDIT -> CHECKPOINT DELTA -> MERGE -> NEXT`.

For substantial work use stable Work Order IDs. Prefer the smallest sufficient context radius and compile executor acceleration capsules rather than forcing repeated whole-repository rediscovery.

## Review law
Verdicts are `APPROVED | CORRECTION_REQUIRED | BLOCKED`. APPROVED requires exact candidate SHA, required gates complete, CRITICAL=0, HIGH=0, no unresolved scope/preservation/evidence mismatch and no stale-head mismatch.

### Review remediation routing — CHAT FIRST, CODEX LAST
This rule applies to **all Hive Coder chats, reviewers and agents** and supersedes any older non-canonical handoff wording that required a Codex PDF after every review.

1. **Fix in chat first.** After a review, if a finding can be corrected safely and completely with the repository/GitHub tools available in the chat, the reviewer must apply the smallest bounded correction directly, stay in the same Work Order/PR when one is active, and then re-inspect the resulting exact head. A `CORRECTION_REQUIRED` verdict by itself is **not** a reason to hand the work to Codex.
2. **Finish approved GitHub lifecycle actions in chat when possible.** If Ready/merge, issue updates, closeout, source-truth reconciliation or other authorized repository actions can be performed safely through connected tools, do them directly instead of adding an unnecessary executor hop.
3. **Codex is the last-resort executor.** Send work back to Codex only when the task materially requires capabilities the chat does not have or cannot use safely, such as substantial local-workspace implementation, local build/toolchain/UI/desktop interaction, machine-specific Codex/toolchain state, execution that requires the user's local environment, or when a governed boundary explicitly requires a separate executor. The handoff must state the concrete reason chat-side correction is insufficient.
4. **PDF prompts are conditional, not universal.** When Codex is genuinely required, deliver the next executable Codex prompt as a generated PDF. `CORRECTION_REQUIRED` and `BLOCKED` remain in the same Work Order/PR until resolved. When the chat can complete the correction itself, no Codex prompt/PDF is required.
5. **Any chat-side mutation creates a new evidence head.** Old exact-head receipts do not transfer. Re-run or re-inspect every required gate on the resulting exact SHA before approval or merge, and never self-declare a skipped/unknown lane as PASS.

No new increment begins before the reviewed predecessor is objectively accepted.

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
**Accepted operational governance:** HCODER-OPS-0001 / merged PR #96 removed all separate installed HIVE context/MCP/mount prerequisites and admitted DEC-032/DEC-033: only the KayzenRoot GitHub account is required; exact-head semantic HEDS activity is OWNER_SELF_AUDIT / NOT_INDEPENDENT with all protected CI, severity and high-assurance risk gates preserved. Product HCODER-WO-0027 PR #93 is now MERGED / PRODUCT POSTVALIDATED as `c25103bdfdfb74e12891fcdc13b0495d3fcf786d`. The only current step is the docs-only conditional CP-0027/DEC-031 promotion, not a new updater implementation. Keep CP-0026/DEC-030 authoritative until the CP-0027 promotion predicate has been separately proven.
`HCODER-CP-0026 — Release trust substrate` is **CANONICAL / SEALED** because `HCODER_CP_0026_EFFECTIVE` has been objectively satisfied. `docs/project-brain/11-CHECKPOINT.md` selects the authoritative checkpoint by predicate and remains the source of truth; this section is a summary, not an independent authority.

Canonical state:
- Checkpoint ladder: `HCODER-CP-0026` / `DEC-030` (release trust substrate) ← `HCODER-CP-0025` / `DEC-029` (native package matrix evidence) ← `HCODER-CP-0024` / `DEC-028` (distribution version, channel and update boundaries) ← `HCODER-CP-0023` / `DEC-027` (governed Git staging). Each checkpoint is selected by its already-declared effectiveness predicate.
- `HCODER_CP_0026_EFFECTIVE = TRUE` was proven for reviewed promotion head `08ce8fe3a1bf189a8118c11b7454cd2fbf36a26d`: independent promotion review `5262643157` at unresolved CRITICAL/HIGH/MEDIUM/LOW `0/0/0/0`; expected-head-protected squash merge preserving reviewed tree `c4f2995c5492920f5f22d4c56550514c78b0d5c2`; resulting exact `main` `3e209faaa96645555fe3ebcddfa6ea8fed13404b` post-validated by Governance `35554327364`, Desktop Shell `35554327412`, Native Package Matrix `35554327449` and Protected Release `35554327398`, all SUCCESS.
- What `CP-0026` admits: the closed `hive-release-provenance-v1` contract, offline fail-closed admission validator, exact package-subject attestation law, protected-release workflow structure, objective environment-protection law and the external provisioning contract without credential values. It inherits the CP-0025 six-target deterministic package evidence unchanged.
- What `CP-0026` still does **not** admit: an actual Windows/macOS publisher signature, notarization/stapling execution, signing/notarization credentials, protected release environments, tag/GitHub Release publication, updater transport, installation, restart, rollback or a production-distributable claim. The release environments remain unproven/absent and `bundle.active` remains `false`.

Runtime authority summary: `HCODER-WO-0023` governed Git staging — exactly `Capability.GIT_WRITE` / `git_stage_paths_v1` — is **SEALED / CANONICAL** under `HCODER-CP-0023` and is no longer an in-flight increment. Workspace file mutation remains bounded to the `CP-0021` create-only `write_file_v1` and the `CP-0022` `replace_file_v1` adapters, both under `Capability.FILESYSTEM_WRITE`, both mandatory trusted-approval gated, both permit-bound and single-use; the `CP-0022` guarantee is bounded-race atomic replacement, explicitly **not** strict CAS. Append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, generic filesystem mutation, shell/terminal/process execution, Tauri/desktop write commands, provider/model execution or credentials, Cua/computer-use mutation beyond prior governed boundaries, remote control, automatic skill activation and billing/purchase authority remain unapproved.

Earlier checkpoint receipts (including `HCODER-CP-0022`, its closeout exact head and its HEDS review, and `CP-0020` and prior) remain historically recorded in their closeout evidence files under `.engineering/evidence/` and are not restated here.

### GEF V1 universal adoption
GEF V1 universal is adopted; review mode is HEDS_DELTA_EXACT_HEAD and proof carry-forward still operates in shadow assurance. The source drift recorded at adoption start (`11-CHECKPOINT.md` still declaring `HCODER-CP-0021`, while Git history contained later proven CP-0022/PLATFORM-001 evidence) has since been reconciled on this line of development, and the same reconciliation has now been carried forward through the canonical `CP-0026`. Read `.engineering/gef/GEF-PROJECT-MASTER.md`, `.engineering/gef/GEF-UNIVERSAL-ADOPTION.md` and `.engineering/gef/GEF-UNIVERSAL-CHECKPOINT.json` for the adoption map, and the `.engineering/gef/` protocols plus `.engineering/gef/GEF-PROJECT-PROFILE.json` for execution, review and evidence law.

### Product-stage and conditional-promotion status
- `HCODER-PLATFORM-001` (Issue #63) native validation matrix is canonical on `main`; its ledger records **CANONICAL / PROVEN_CI MATRIX COMPLETE**. Launch smoke remains PROVEN_CI on Windows only. Release package evidence is now proven under `HCODER-CP-0025`; package **install** behaviour remains UNPROVEN on all platforms, and unsigned packages remain undistributable.
- `HCODER-WO-0026` / Issue `#85` / `HCODER-DIST-001C` is **CLOSED / COMPLETE / CANONICAL / SEALED** under `HCODER-CP-0026`; PR `#86` is merged. Its credential-bearing signing/notarization and publication stages remain unexercised and outside the admitted authority.
- `HCODER-WO-0027` / Issue `#89` / `HCODER-DIST-001D` product PR #93 is MERGED / POSTVALIDATED at exact product main `c25103bdfdfb74e12891fcdc13b0495d3fcf786d`: owner-account high-assurance audit clearly NOT_INDEPENDENT, reviewed tree equal merge tree `39b8f665a4e46341d10b378fb13f867a1a0ae209`, 13 exact-head required checks SUCCESS and fresh product-main Governance `36579684792`, Desktop Shell `36579684754`, Native Package Matrix `36579684765`, Protected Release `36579684818` all SUCCESS. DEC-031 is only CONDITIONAL, pending separately reviewed/merged and postvalidated CP-0027 promotion. No real signed download, key/endpoint, installer/restart, live update, publication or production-distributable claim. Pre-existing Linux glib advisory = Issue #97.

### NEXT EXACT ACTIONS
1. Complete the already-scoped **documentation-only CP-0027/DEC-031 promotion** under `.engineering/work-orders/HCODER-WO-0027-PROMOTION.md` and its exact Context Lock. This stage adds no product capability. CP-0026/DEC-030 remain canonical until the `HCODER_CP_0027_EFFECTIVE` property is proven.
2. Capture the promotion PR's current exact-head source/diff/tree, update only approved docs, obtain all 13 applicable GitHub contexts/four workflows and a substantive high-assurance OWNER_SELF_AUDIT / NOT_INDEPENDENT, with explicit risk acceptance, zero HIGH/CRITICAL and zero blocking threads. Use expected-head-protected squash; then obtain **fresh** exact-promotion-main four-workflow SUCCESS before recording CP-0027 effectiveness. Product-stage receipts do not transfer to promotion.
3. Apply CHAT FIRST, CODEX LAST. No external HIVE server or additional GitHub collaborator is needed. Do not introduce private keys, live endpoints, installer/restart, signing, updater artifact generation, publication or real native update E2E. Treat Issue #97 glib debt as a separate pre-existing production-Linux-distribution blocker.
4. Only after the conditional checkpoint is objectively effective should a successor product increment be considered from a new exact source check.
