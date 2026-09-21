# Checkpoint Delta / Closeout — HCODER-WO-0026

**Status:** PROPOSED / REVIEW PENDING AT THIS REVISION — CONDITIONAL CANDIDATE (`HCODER_CP_0026_EFFECTIVE`); this line states the standing of the revision that carries it, mints no approval, and confers no canonical force by being read  
**Work Order:** `HCODER-WO-0026 — Signing, Notarization, Release Provenance And Protected Release Workflow`  
**Declared decision state:** `DEC-030` — APPROVED FOR PROMOTION CANDIDATE / NOT CANONICAL ON MAIN until `HCODER_CP_0026_EFFECTIVE`  
**Issue:** `#85`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001C`  
**Predecessor checkpoint:** `HCODER-CP-0025` / `DEC-029` — CANONICAL / SEALED, authoritative on `main`  
**Canonical base:** `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`  
**Independently reviewed technical head:** `0a1b8375e5c950d321f898b6d455eb874583c9a4` (tree `d939c9f83034ee1eeebe78bc0b8c74b118dbfab7`)  
**Independent technical HEDS:** `5262493714` — APPROVED FOR GOVERNED PROMOTION-CANDIDATE PREPARATION, CRITICAL `0` / HIGH `0` / MEDIUM `0` / LOW `0`  
**Product PR:** `#86` — OPEN / DRAFT / UNMERGED  
**Repository:** `KayzenRoot/hive-coder`  
**Disclosed conflicts:** none

> **This is a candidate declaration, not a promotion.** The branch copy of `docs/project-brain/11-CHECKPOINT.md` carries the conditional `HCODER-CP-0026` rung so that the ladder computes effectiveness by predicate and needs no later rewrite to state it. `main` is unchanged until a governed merge lands, and `HCODER-CP-0025` remains authoritative on `main` until `HCODER_CP_0026_EFFECTIVE` is objectively proven. The executor of this increment cannot self-promote or self-approve this delta; approval belongs to an independent exact-head review of the promotion head, and canonical force belongs to that review plus a governed merge and post-validation.

## Effectiveness predicate

`HCODER_CP_0026_EFFECTIVE` is satisfied if and only if all three conditions hold for one and the same promotion/closeout revision:

- (A) that exact revision was independently reviewed at that exact head with unresolved CRITICAL `0` / HIGH `0` and no unresolved scope, preservation or evidence mismatch;
- (B) that exact reviewed revision was governed-merged into `main` under expected-head protection, and the resulting merge preserved the reviewed tree;
- (C) the resulting exact `main` SHA passed fresh `Governance`, `Desktop Shell`, `Native Package Matrix` **and** `Protected Release`, each launched from that `main` SHA. No PR-head run, no adjacent SHA and no earlier head may satisfy condition (C).

**Before** the predicate is satisfied, `HCODER-CP-0025` and the non-canonical `DEC-030` state remain authoritative. **Once** it is satisfied, `HCODER-CP-0026` and `DEC-030` carry canonical force under the declaration in this document, with no repository-document rewrite required merely to flip phase or status wording.

The predicate deliberately depends on no merge SHA, run ID, review ID, Issue state, PR state or moving `current main` field, because a law that encodes its own evidence can never fail. Evidence of whether it is satisfied is external lifecycle evidence referenced by Issues #30 and #85 and by the closeout PR carrying the evaluated revision, whose state this document does not depend on. It therefore stays true whether or not the predicate has been satisfied.

`Protected Release` belongs in this predicate and not in its predecessor's: this is the slice that introduces the release lane, so a closeout that canonicalized it while its own gate could go unverified on `main` would assert a release-trust capability on the strength of runs belonging to a different stage.

## Purpose

Declare what `HCODER-CP-0026` would mean if its predicate is later proven: the governed promotion of the release-trust **substrate** — a closed provenance contract, its offline admission gate, and a release workflow whose credential-bearing stages are provable structure rather than YAML intent.

This delta creates no new authority and changes no behaviour. It records lifecycle and canonical status only, and only conditionally.

## What is admitted if the predicate becomes true

`HCODER-DIST-001C`, as release-trust substrate and nothing more:

- **One closed release-provenance contract.** `hive-release-provenance-v1` with its offline, stdlib-only, fail-closed admission validator: closed key sets, one exception type, refusal of unknown keys, duplicates, traversal, absolute paths, wrong source SHA or version, impossible state combinations and fabricated publication claims, and no wall-clock field so a receipt cannot age into a different claim.
- **Five guarantees kept apart.** Artifact integrity, build provenance, publisher signing, platform trust/notarization and publication are separate fields with separate admission rules, computed per field, so no rule may infer one claim from another. A digest satisfies neither signing nor trust; an attestation satisfies no signing requirement.
- **Package-subject attestation law.** Attestation subjects are **derived** from the validated `hive-package-inventory-v1` document and use its recorded digest identities; they are never rediscovered from the filesystem and never widened by a glob. The signed statement's subject set must equal the package set exactly — same names, same digests, no extra, no omission — and the equality is re-checked offline against the inventory rather than taken from a log line.
- **Protected Release workflow structure.** Workflow and job least privilege with `contents: read` at the top and `id-token: write` reaching only the attestation jobs; full SHA pinning; no `pull_request_target`; trigger separation so untrusted PR code can never reach a credential stage; an objective environment-protection probe that reads the platform's own protection record (existence, `required_reviewers` with at least one reviewer, `prevent_self_review`, `can_admins_bypass` false) instead of trusting a name written in YAML; and fail-closed signing and publication barriers that refuse independently of whether provisioning exists.
- **The complete external provisioning contract, without any value.** For each future signing and notarization stage: the credential class, the documented configuration identity or slot name, the mechanism that makes it exist, and the verification condition that would prove its result — Apple API-key notarization identity including its issuer, and the Azure/Entra application, tenant, subscription, federated trust, profile-scoped role assignment and service instances. No value, no request for one, and no structure in this slice that could resolve one.

## What remains explicitly unapproved

No package is signed, notarized, stapled, trusted, published, installable or production-distributable, and none may be described that way. No credential or private key is held, read, requested, decoded or imported. No protected environment is asserted to exist; its absence fails closed and is never a reason to publish unsigned. No signing or notarization executor exists or runs. No Azure or Apple account provisioning. No tag, no GitHub Release, no asset upload, no publication. No updater plugin, endpoint, transport, download, install, restart or rollback behaviour, and no `HCODER-DIST-001D` through `HCODER-DIST-001G` work. No new product or runtime capability, permission, control-plane path or dependency. No generic shell, filesystem, Git, credential or network authority; `Capability.GIT_WRITE` and `Capability.FILESYSTEM_WRITE` are untouched, and a CI release lane confers no runtime authority. `bundle.active` remains `false`.

## Evidence is not trust, and structure is not execution

A conforming provenance document is evidence **about a build**, produced by an admission gate that structurally cannot mint a signing, notarization, attestation or publication claim. The credential-bearing stages of the workflow are deliberately present but **unexercised**: they are reached only behind a proven protection verdict, and this increment has never executed one. A green lane that did not sign is evidence about text and structure, not about signatures, and `SKIPPED` and `UNKNOWN` are never reported as `PASS`.

## Evidence carry-forward semantics

Review `5262493714` at `0a1b8375` proves the **technical** bytes only. That proof carries forward to the promotion head **solely** while the technical freeze holds — every workflow, tool, test, contract, product and configuration path byte-identical, proven by git blob/object hashes or an exact path-set comparison — and while the later head's added content is governance text. It carries forward to neither the promotion decision nor canonical status: the new governance head requires fresh exact-`main` hosted gates and a fresh independent exact-head review of its own, and any technical change whatsoever voids the carry-forward and returns the increment to correction review.

Superseded evidence is preserved, not rewritten. The Prompt 43 review of `374e642fb901ce21e1b8886fb80addccbfe89add` returned `CORRECTION_REQUIRED` with HIGH `1` / MEDIUM `2`; that record stands as history alongside the correction that closed it.

## Rollback and roll-forward truth

No release, tag, publication, signing or notarization was executed, so this checkpoint creates **no** artifact to roll back and **no** update-rollback or roll-forward authority. Nothing here moves a channel, replaces a running installation, or makes any promise about recovery after a failed update; those remain unapproved slices of the parent epic. The only rollback-relevant fact this substrate establishes is negative and useful: an unsigned, unpublished candidate cannot be mistaken for a shipped release, because the stages that would create one refuse unconditionally.

## Lifecycle evidence (immutable stage facts)

| Stage | Fact |
|---|---|
| Reviewed technical head | `0a1b8375e5c950d321f898b6d455eb874583c9a4` |
| Reviewed-head tree | `d939c9f83034ee1eeebe78bc0b8c74b118dbfab7` |
| Independent technical HEDS | `5262493714` — APPROVED FOR GOVERNED PROMOTION-CANDIDATE PREPARATION, CRITICAL `0` / HIGH `0` / MEDIUM `0` / LOW `0` |
| Predecessor `main` | `1a56224eeb9bc07f032df1ede23bdda9d74f8d12` — `HCODER-CP-0025` closeout seal |
| Technical exact-head receipts at the reviewed head | Governance `35545347036`, Desktop Shell `35545347009`, Native Package Matrix `35545346966`, Protected Release `35545347058` — all SUCCESS on a PR head, with `build-attest-*`, `sign-*` and `publish` SKIPPED by design |
| Governed merge | none: PR `#86` is OPEN / DRAFT / UNMERGED and its executor does not merge |
| Post-merge exact-`main` gates | none: condition (C) is unproven and unrecorded |

The receipts above belong to a PR head at a superseded-on-merge stage and are recorded as the technical-stage facts they are. They are **not** condition (C) evidence, which requires runs launched from the exact `main` SHA produced by the governed merge. The promotion head's own run IDs are not written into canonical law: they do not exist yet, and they belong to mutable external evidence in PR `#86` and Issues #85 and #30 once they do.

## Not changed by this delta

No product behaviour, runtime authority, contract law, workflow behaviour, test semantics, dependency state or technical byte changes; that is a precondition of the carry-forward above, not a side effect. The contract, validator law, five-guarantee separation, attestation subject model, least-privilege boundaries, protection-probe semantics and the credential-stage refusals are exactly as independently reviewed at `0a1b8375`. What this declaration governs is lifecycle and canonical status, and only through the predicate above. `HCODER-CP-0025` and `DEC-029` are not amended, and no earlier checkpoint record is rewritten.

## STOP CONDITION

This declaration grants no authority, capability, scope or behaviour change — it is a proposal awaiting an independent reviewer. `HCODER-CP-0026` and `DEC-030` carry no canonical force while `HCODER_CP_0026_EFFECTIVE` is unsatisfied, and no repository text asserts that it is satisfied. Any promotion requires an independent exact-head review of the new head, a governed merge under expected-head protection, and fresh exact-`main` gates. Any change to a frozen technical path, any executed or provisioned credential stage, any published artifact, or any new product behaviour requires a newly governed Work Order with its own Context Lock, allowed files and exact-head gates.
