# HCODER-CP-0023 — Canonical Closeout

**Status:** SEALED / CANONICAL — closeout PR #75 merged and post-closeout exact-main validated  
**Work Order:** `HCODER-WO-0023 — Governed Git Staging Capability`  
**Decision:** `DEC-027 — Governed Git Staging Boundary`  
**Issue:** `#68` — CLOSED / COMPLETED at `2026-09-17T10:35:38Z`  
**Product PR:** `#69` — MERGED  
**Base checkpoint:** `HCODER-CP-0022`  
**Canonical product merge SHA:** `1f09520fbd92c7e65f9726b65a854f918507c895`  
**Closeout merge SHA:** `1b83666699acc8fdbd5270d811f1bf263d55ef47`  
**Final-seal merge SHA (immutable):** `b6297fbe4de4681fc92093f3691f693dc2de0dc1`  
**Validated `main` at final-seal validation:** `b6297fbe4de4681fc92093f3691f693dc2de0dc1`  
**Post-seal exact-main validation:** Governance `35210910407` SUCCESS; Desktop Shell `35210910423` SUCCESS

## Canonical bounded authority
HCODER-CP-0023 canonicalizes exactly one repository-mutation action: `Capability.GIT_WRITE` / `git_stage_paths_v1`, target state `index_update`, for explicit regular files in the already-proven ordinary local SHA-1 repository envelope, maximum 128 paths. The capability is HIGH risk, materially sensitive, mandatory trusted approval, and consumes a request-bound single-use permit at the final safe boundary.

Its only product effect is publishing the approved content-addressed blob objects into the repository-local `.git/objects` store and then atomically publishing the approved candidate index to `.git/index`.

## Canonical product state
- All CP-0005 through CP-0022 permission/security/status boundaries remain authoritative and unchanged except where CP-0023 deliberately adds the bounded Git index-mutation authority below.
- Hive runtime now has three privileged mutation adapters: CP-0021 create-only `write_file_v1` and CP-0022 `replace_file_v1` under `Capability.FILESYSTEM_WRITE`, and CP-0023 `git_stage_paths_v1` under `Capability.GIT_WRITE`. All three are mandatory trusted-approval gated and permit-bound.
- The approval fingerprint commits to 17 frozen argument keys. Declared paths, observed worktree paths and path-binding paths must be identical after canonical normalization, and contradiction is rejected before permit consumption.
- Raw worktree, index and compressed object bytes have no representation in approval, audit or receipt.
- A canonical OID pathname is never opened for writing: the complete compressed object is materialized and digest-verified in Hive-owned private storage outside `.git/objects` and promoted with an atomic create-if-absent primitive. An existing object is never overwritten and never deleted.
- The index is published only by the capability-owned `index.lock` transaction; a foreign lock fails closed and is never removed.

## Explicitly unapproved authority
Commit, tag, ref, branch, remote, credential, reset, checkout, restore, clean, stash, merge, rebase, cherry-pick, generic Git argv, shell/terminal/process execution, hooks, executable clean/smudge/process filters, network, arbitrary `.git` writes, generic filesystem mutation, desktop/Tauri mutation expansion, provider/model execution or credentials, computer-use mutation expansion, remote control, automatic skill activation and billing/purchase authority remain outside CP-0023. `FILESYSTEM_WRITE` and `SHELL_EXECUTE` are not reused and cannot satisfy a `git.write` rule.

## Evidence chain
- Last behavior-changing implementation head: `b904b473416786e72c7e805e2e8c8b557d377166`.
- Independently reviewed promotion-candidate head: `b827cb2eaa04eb2efa3ffb0b9aa7a82cbb7c672a`.
- Independent A4/HEDS review `5229345968`: CRITICAL `0` / HIGH `0`.
- Prompt 10 review artifact `5230035319`: APPROVED for the governed merge sequence.
- Pre-merge product head `2dde9bb5690f22820ab9fe952aa2672e97c0f36f`: Governance `35169861228` SUCCESS, Desktop Shell `35169861254` SUCCESS.
- Pre-merge canonical main: `aaa75242826db33442cd96cdc1d550d69bd25faa`.
- Product PR #69 squash-merged with expected-head protection as `1f09520fbd92c7e65f9726b65a854f918507c895`.
- Post-merge exact-main validation on `1f09520fbd92c7e65f9726b65a854f918507c895`: Governance `35171215292` SUCCESS (source-pack plus native Linux, Windows HIGH_ASSURANCE and macOS governed Git staging proof), Desktop Shell `35171215429` SUCCESS (desktop web, Windows, Linux, macOS).
- Native three-OS proof: Linux, Windows HIGH_ASSURANCE and macOS pass independently; no platform is inferred from another.

## Canonical decision
`DEC-027 — Governed Git Staging Boundary` is canonical on `main` under `HCODER-CP-0023`.

## Residual bounded-race law
Publication is atomic same-filesystem **publication**, explicitly **not** strict CAS. An uncooperative external process may act between the last successful revalidation and the atomic call. A crash after blob publication but before index publication may leave an unreachable content-addressed blob; that is never reported as success, is never rolled back, and leaves no partial bytes at a canonical OID pathname.

## Seal evidence
- Closeout head `204aa32ac26003082366588bc9e5d5399473c3b6`: Governance `35174158942` SUCCESS, Desktop Shell `35174158986` SUCCESS.
- Closeout PR #75 squash-merged with expected-head protection as `1b83666699acc8fdbd5270d811f1bf263d55ef47`.
- Post-closeout exact-main validation on `1b83666699acc8fdbd5270d811f1bf263d55ef47`: Governance `35204919678` SUCCESS (source-pack plus native Linux, Windows HIGH_ASSURANCE and macOS governed Git staging proof), Desktop Shell `35204919616` SUCCESS (desktop web, Windows, Linux, macOS). That SHA was the **validated `main` at closeout validation** — an immutable lifecycle-stage fact, not a live repository pointer.

## Final step (completed)
The final-seal PR #76 squash-merged with expected-head protection as `b6297fbe4de4681fc92093f3691f693dc2de0dc1`, and that exact `main` passed Governance `35210910407` and Desktop Shell `35210910423`. Issue #68 was then closed as COMPLETED at `2026-09-17T10:35:38Z`. No further lifecycle step remains.

## STOP CONDITION (final sealed state)
The lifecycle for `HCODER-WO-0023` is **complete**. Issue #68 is **CLOSED / COMPLETED** at `2026-09-17T10:35:38Z`; final-seal PR #76 is **merged** as `b6297fbe4de4681fc92093f3691f693dc2de0dc1`, and that exact `main` passed post-seal exact-main validation.

This closeout grants **no** additional authority, scope or behavior change under `HCODER-WO-0023`. The admitted authority is unchanged: exactly `Capability.GIT_WRITE` / `git_stage_paths_v1`, with atomic publication rather than strict CAS. Broader Git mutation, shell/terminal execution, commit/ref/branch/remote/network/credential capability and arbitrary `.git` writes remain unapproved.

Any new product behavior requires a **newly governed Work Order** with its own Context Lock, allowed files and exact-head gates. The evidence SHAs, HEDS provenance and bounded-race law recorded above are unchanged.
