# HCODER-OPS-0001 — Remove dependency on separately installed HIVE

**State:** USER-REQUESTED / PROPOSED GOVERNANCE CHANGE; NOT YET CANONICAL  
**Issue:** #95  
**Base:** `main a9b48bce43fcc2c1a14b70036ed4555f52ba3537`  
**Risk:** ELEVATED (project-wide development-source policy and integration boundary)  
**Class:** NECESSARY operational prerequisite before further HCODER-WO-0027 work  
**Context Lock:** `.engineering/context-locks/HCODER-OPS-0001.md`

## OBJECTIVE

Allow all Hive Coder development, builds, reviews and releases to proceed without the separate, locally installed `KayzenRoot/hive` HIVE context service, its MCP/REST server, Docker containers, PostgreSQL/pgvector, Redis, indexing/corpus or project registry. Eliminate any current instruction that makes it a prerequisite.

The internal `hive_runtime/` package, product identity, `hive-*` wire/provenance identifiers, Cua Driver's **independent** MCP transport, Open Interpreter ACP, own Git/source pack/GEF/HEDS, Tauri product and its security contracts are **not** the separately installed HIVE service and must remain functional.

## CONTEXT

The user explicitly decided to uninstall the *separately installed* HIVE and requested decoupling before continuing. `HCODER-CP-0026` remains canonical. The active product Work Order HCODER-WO-0027 (Issue #89, Draft PR #93) is held for independent review, not discarded. Draft PR #94 proposes an external HIVE v1.0.3 MCP-first context workflow and must be closed without merging. The HIVE repo's Issue #166/PR #167 proposes a local mount made unnecessary by this user decision.

Repository source investigation on the base commit found no active implementation import or GitHub Actions prerequisite for the **external** HIVE server; a HIVE_PROJECTS_ROOT mention in a historical HCODER-WO-0025 Context Lock is historical evidence, not executable configuration. Reconfirm in exact-head audit.

## SCOPE

1. Version this Work Order, its Context Lock and the proposed DEC-032 standalone-development decision.
2. Update current AGENTS/README and affected current Project Brain documents so only repository-local canonical Git, ADRs, Work Orders, Context Locks, actual tests, GitHub workflows and approved provider/foundation adapters are required for development. Remove misleading bootstrapping/HIVE-first prerequisites; keep GEF/HEDS.
3. Append a bounded forward-only delta to the active HCODER-WO-0027 Context Lock overriding its obsolete local external-HIVE reconciliation prerequisite. Do not alter historical snapshot text or expand updater authority.
4. Identify and eliminate only **actual live integration hooks**, if any, for external HIVE, with proof and separately authorized small code correction if outside the locked change set. Keep internal product and third-party foundation MCP paths untouched.
5. Mark the now-obsolete unmerged HIVE-context PR in this repo and the independently proposed HIVE mount PR/Issue as superseded by the explicit user decision, without deleting repositories/branches or modifying HIVE's active WO-032.
6. Produce exact-head CI evidence, an audit record and a proposed checkpoint delta. No canonical status promotion before governed approval.

## OUT OF SCOPE

Uninstalling software from the user's machine; deleting or rewriting historical documents; renaming Hive Coder, its internal `hive_runtime`, npm/crate names, IPC/provenance/manifest identifiers, changing Cua MCP or Open Interpreter ACP; new model/agent capability; Tauri updater implementation; releases, secrets, signing, registry/index changes, broad cleanup or force-push.

## FILES / SOURCES TO READ

Read in authority order: canonical checkpoint; Decisions Ledger/approved ADRs; Scope and Requirements; DoD; Architecture; Security; active HCODER-WO-0027 and Context Lock; AGENTS; HIVE-specific draft PR #94; HIVE Issue #166 / PR #167; then runtime/foundation manifests and GitHub workflows for evidence of real external dependencies.

**Allowed tracked surface (closed):**
- `.engineering/work-orders/HCODER-OPS-0001.md`
- `.engineering/context-locks/HCODER-OPS-0001.md`
- `docs/project-brain/adrs/DEC-032-STANDALONE-NO-EXTERNAL-HIVE.md`
- `AGENTS.md`, `README.md`
- `docs/project-brain/02-REQUIREMENTS.md`, `03-SCOPE.md`, `04-ARCHITECTURE.md`, `07-DEPLOYMENT.md`, `08-BACKLOG.md`, `10-DECISIONS-LEDGER.md`, `13-INTEGRATION-CONTRACTS.md`
- `.engineering/context-locks/HCODER-WO-0027.md` (append-only forward delta)
- `.engineering/evidence/HCODER-OPS-0001.md` (exact-head audit/update only).

No other tracked code/file changes unless a correction delta first proves a real runtime dependency and specifies exact scope and tests.

## REQUIREMENTS / ARCHITECTURE RULES

- No code, build, CI, dev bootstrap, local GitHub review, Work Order planning, checkpoint source access or execution gate needs a running **external HIVE** container, MCP server, HIVE_PROJECTS_ROOT, project registry, corpus or database.
- Keep canonical sources Git-first. Optional Codex/Cursor optimization uses focused repository files and local deterministic tooling; neither requires external HIVE.
- Preserve existing internal Hive Coder capability/permission/credential barriers and unchanged contracts. Cua's own MCP server is unrelated to removed external HIVE.
- Historical decisions, receipts and Context Locks remain immutable facts. Append explicit superseding direction rather than rewriting them as if they never existed.
- A GitHub Draft PR is a proposal, not canonical admission. No next product increment until required exact-head checks and a substantive semantic audit. For this operational PR, that audit is the DEC-033 owner self-audit explicitly labeled NOT_INDEPENDENT; it does not need a second account.

## ACCEPTANCE CRITERIA

1. An executor reading the current AGENTS/README/current canonical source pack will not be instructed to connect, mount, index or consult the separately installed HIVE.
2. No live executable external-HIVE dependency in the checked repository/dependency manifests/workflows, with exact-path evidence and no false-positive deletion of product-owned code or Cua MCP.
3. HCODER-WO-0027 can undergo exact-head HEDS semantic audit, by KayzenRoot as an explicitly NOT_INDEPENDENT owner self-audit after DEC-033's acceptance, and proceed without local HIVE. All updater-specific HIGH_ASSURANCE tests, risk and release restrictions remain unchanged.
4. Obsolete external-context and external-mount PRs are closed as superseded and their history retained; no branch is force-pushed or deleted.
5. All four applicable Hive Coder hosted workflows pass on the exact review head. Skipped credential-bearing protected-release jobs remain SKIPPED. The full suite is NOT RUN locally unless independently demonstrated.
6. A DEC-033 exact-head owner semantic self-audit (NOT_INDEPENDENT) reports no unresolved HIGH/CRITICAL, all required exact-head checks succeed and no blocking review threads remain; only then consider governed squash merge. Keep CP-0026 canonical until exact-main postmerge checks prove otherwise.

## TESTS / EVIDENCE

Snapshot exact base/head, changed-path allowlist, static search for HIVE_PROJECTS_ROOT, external HIVE server URLs, `/workspace/projects`, HIVE v1.0.3 MCP preflight instructions in *active* files, inspect `.github/workflows/**`, pinned manifests and local import graph. Check focused negative cases: internal `hive_runtime`, standalone local status sidecar and Cua MCP remain unchanged. Obtain Governance, Desktop Shell, Native Package Matrix and Protected Release exact-head checks. Report check run IDs, tests, source fingerprints, unknowns and SKIPPED lanes truthfully.

## DELIVERABLES / REVIEW FORMAT

Versioned Work Order/Context Lock, proposed DEC-032, minimal living-source deltas, Issue #95 / linked Draft PR, exact-head Evidence Bundle with diff/scope and a proposed checkpoint delta **NONE until approved**. Review in Brazilian Portuguese with APPROVED / CORRECTION REQUIRED / BLOCKED.

## STOP CONDITION

STOP if removal would delete internal product capabilities, break a frozen contract, silently rewrite an approved decision/historical source, require external HIVE to execute tests, weaken a security gate, or conflict with another unmerged product branch. Do not merge an unreviewed PR, claim local uninstall, auto-close HCODER-WO-0027 or advance the product version before this operational prerequisite is audited.

## Scope Correction Delta 001 — account-owner-only GitHub governance (owner directive 2026-09-29)

**User directive:** `KayzenRoot` alone must be able to plan, review, correct and merge its own repository work; no collaborator, second human account, approval invitation or paid review bot may be a **mandatory** development/acceptance prerequisite, for this migration and future Hive Coder Work Orders.

**Source check:** the active `hive-main-governed` GitHub ruleset #23768014 requires **0** approving reviews, no specific reviewers and no code-owner approval; it requires all 13 registered exact-head status checks, strict-up-to-date base, pull-request flow, squash-only and review-thread resolution. It cannot count a GitHub PR author's self-APPROVE as another person's review. The pre-existing `kayzenweb3` request on PR #96 has been removed. The owner does not need a collaborator to complete this PR under that ruleset.

**Additional allowed paths:** `.engineering/gef/GEF-REVIEW-PROTOCOL.md`, `.engineering/gef/GEF-EXECUTION-PROTOCOL.md`, `docs/project-brain/09-DEFINITION-OF-DONE.md`, `docs/project-brain/adrs/DEC-033-OWNER-ONLY-GOVERNANCE.md`, plus previously allowed AGENTS/README/Decisions Ledger/active WO-0027 Context Lock/Evidence Bundle and this Work Order/Context Lock. The additional paths may change *only* to document forward-looking owner-only merge/review identity, current HEDS audit semantics and exact-head gates. No product source, GitHub Actions YAML, ruleset/branch-protection setting, security permission, signed release rule, historical accepted decision/checkpoint, or external HIVE project may change. This delta also authorizes resolving the verified CodeRabbit issue in the existing Evidence Bundle through a bounded exact-source inspection of the current candidate.

**Proposed DEC-033:** maintain distinct planning, execution and reviewing responsibilities but permit all GitHub lifecycle actions from `KayzenRoot`; the author must write an objectively sourced **OWNER SELF-AUDIT, NOT INDEPENDENT**, bound to the exact current HEAD, with changed-scope review, challenge/negative-test coverage, all applicable GitHub status gates, unresolved CRITICAL/HIGH = 0 and no open blocking review threads. Never describe owner review, a trial-quota bot message or a green test as independent human review. The substantive evidence/permission/release barriers stay unchanged. For HIGH_ASSURANCE work, require an explicit owner-recorded risk acceptance and extra challenge/negative-test evidence before the merge; keep secrets and signing externally provisioned/blocked. Third-party reviewers may contribute optionally but are never mandatory.

**Future application:** amend the existing HCODER-WO-0027 Context Lock **forward-only** to remove its prospective second-account HEDS acceptance prerequisite after this operational PR is governed-accepted, without changing its updater threat model, production trust prerequisites, held Draft PR #93 code, missing real signing/endpoint credentials, release publication state, or historical HEDS receipts. Other repositories require their own policy/source reconciliation: this Work Order does not silently amend 37 other repository histories or GitHub rules.

**Acceptance update:** The original acceptance-criterion 3/6 and earlier requirements wording have been reconciled in this unmerged proposal. DEC-033's exact-head owner self-audit (NOT_INDEPENDENT) satisfies the semantic-review function for this same operational PR, with unchanged objective CI and review-thread gates. Earlier closeout predicates/independent receipts remain historical and untouched. Any reviewer finding is handled as same-PR scoped correction with fresh exact-head CI. Postmerge exact-main gates remain mandatory before completion is claimed.
