# Checkpoint Delta / Promotion Candidate — HCODER-WO-0023

**Status:** PROMOTION CANDIDATE — NOT CANONICAL  
**Work Order:** `HCODER-WO-0023 — Governed Git Staging Capability`  
**Decision:** `DEC-027` — promotion candidate, still PROPOSED  
**Issue:** `#68`  
**PR:** `#69` — remains OPEN / DRAFT  
**Technical head:** `b904b473416786e72c7e805e2e8c8b557d377166`  
**Canonical main at promotion preflight:** `aaa75242826db33442cd96cdc1d550d69bd25faa`

## Purpose
Record a bounded promotion **candidate** state for the first Hive-owned Git index-mutation authority, without mutating the canonical checkpoint, promoting `DEC-027`, or changing any product behavior. This delta creates no new authority and does not seal anything.

## What is admitted at the technical head
- Exactly one capability: `Capability.GIT_WRITE = "git.write"`, risk HIGH, materially sensitive, mandatory trusted approval, required target field `workspace`.
- Exactly one action under it: `git_stage_paths_v1`, target state `index_update`, for explicit regular files in the already-proven ordinary local SHA-1 repository envelope, maximum 128 paths.
- The only product effect is publishing the approved content-addressed blob objects into the repository-local `.git/objects` store and then atomically publishing the approved candidate index to `.git/index`.

## What remains explicitly unapproved
Commit, tag, ref, branch, remote, credential, reset, checkout, restore, clean, stash, merge, rebase, cherry-pick, generic Git argv, shell/terminal/process execution, hooks, executable clean/smudge/process filters, network, arbitrary `.git` writer, generic filesystem mutation, desktop/Tauri mutation expansion, provider/model execution or credential expansion, computer-use mutation expansion beyond prior governed boundaries, remote control, automatic skill activation and billing/purchase authority. No expansion to linked worktrees, submodules/nested repos, bare repos, sparse/split index, conflicts, alternates/shared object DB, promisor/partial clone, SHA-256 repositories, deleted-path staging or unproven extensions.

`FILESYSTEM_WRITE` and `SHELL_EXECUTE` are not reused and cannot satisfy a `git.write` rule.

## Promotion evidence carried to the candidate
- Technical head `b904b473416786e72c7e805e2e8c8b557d377166`.
- Governance run `35159183327`: SUCCESS.
- Desktop Shell run `35159183326`: SUCCESS.
- Native governed Git staging proof, independent per platform: Linux SUCCESS, Windows HIGH_ASSURANCE SUCCESS, macOS SUCCESS.
- Local assurance: compileall PASS; authority lane 48 tests PASS; security lane 21 tests PASS with 13 platform/capability skips and no implementation skip; full Python suite 533 PASS; foundations lock/doctor and governed dependency verifier PASS.
- Final technical HEDS: CRITICAL `0`, HIGH `0`, MEDIUM `0`, LOW `3` — all three LOW findings were source-accuracy prose corrections applied before the HEDS head, plus one accepted bounded-race statement.

## Residual bounded-race statement
Publication is an atomic same-filesystem **publication**, not strict CAS. An uncooperative external process may act between the last successful revalidation and the atomic call. This is stated in the ADR, the Context Lock, the implementation docstrings and this delta, and must never be represented as strict CAS.

## Not changed by this delta
No product behavior, runtime authority, workflow behavior, dependency state, test semantics, canonical checkpoint, ADR status or release state was changed. The canonical checkpoint document is untouched.

## Promotion gate
This candidate itself must pass exact-head Governance + Desktop Shell on the promotion-candidate head and an independent review before any promotion mutation. Only after that review may the canonical checkpoint be advanced, `DEC-027` be promoted and PR #69 leave Draft. This delta does not perform any of those.

## STOP CONDITION
Do not treat this delta as acceptance, approval or canonical promotion. Do not merge PR #69, do not mark it ready, and do not promote `DEC-027` on the strength of this file.
