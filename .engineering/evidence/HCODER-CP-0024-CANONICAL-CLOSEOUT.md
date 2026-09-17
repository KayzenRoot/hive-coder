# HCODER-CP-0024 — Canonical Closeout

**Status:** DURABLE CLOSEOUT DECLARATION — CONDITIONAL EFFECTIVENESS (`HCODER_CP_0024_EFFECTIVE`)  
**Work Order:** `HCODER-WO-0024`  
**Decision:** `DEC-028`, CANONICAL / SEALED under `HCODER-CP-0024` while the predicate below is satisfied  
**Canonical predecessor:** `HCODER-CP-0023`  
**Product PR:** `#80` — SQUASH MERGED (expected-head protected)  
**Product merge SHA:** `c7f2a5f21369fd92b3493bea0be0192bbd7298b4`  
**Issue:** `#77`

## Effectiveness predicate

`HCODER_CP_0024_EFFECTIVE` is satisfied if and only if all three hold for one and the same closeout revision:

- (a) that exact closeout candidate revision was independently reviewed with unresolved HIGH/CRITICAL `0/0`;
- (b) that exact revision was governed-merged with expected-head protection;
- (c) the resulting exact `main` SHA passed fresh Governance and Desktop Shell.

Before the predicate is satisfied, `HCODER-CP-0023` and the non-canonical `DEC-028` state remain authoritative. Once it is satisfied, `HCODER-CP-0024` and `DEC-028` are CANONICAL / SEALED under this declaration with no repository-document rewrite required. The predicate depends on no merge SHA, run ID, review ID, Issue state, PR state or moving `current main` field: evidence of whether it holds lives externally in the active closeout PR and Issues #30 and #77.

## Canonical boundary

`HCODER-CP-0024` closes the first governed slice of Hive Coder's distribution and version contract. It canonicalizes a **contract and seam** layer only: the product-version law, the release-channel law, the update-state and authenticity law, the persisted-event law, the bounded read-only About read model, and a Hive-owned inert `UpdateService` boundary.

It admits **no** runtime authority, no capability, no permission and no control-plane path. Nothing in this checkpoint performs, schedules or authorises a network request, download, install, restart, signature check, release call, process spawn or filesystem mutation.

## Canonical version law

Exactly one canonical version source exists: `apps/desktop/src-tauri/tauri.conf.json` → `version`. The Tauri application version identifies the shipped artifact and is the value a future updater would compare against; `Cargo.toml` and `package.json` are **exact mirrors** that must equal it and must never be edited independently, enforced by `tools/desktop/version_drift.py` deterministically and offline.

The acceptance profile is **toolchain-compatible bounded SemVer 2.0.0**: each core `major`/`minor`/`patch` within `0..9007199254740991`, and the whole version string at most 128 characters. The core bound is the intersection of the declared mirror consumers — npm's `node-semver` rejects core components above `Number.MAX_SAFE_INTEGER`, while Cargo's `u64` range is wider — so it follows the narrower consumer. Accepted core values are carried and compared as exact decimal strings by digit length then lexical order; no comparison path uses floating-point conversion or platform-dependent integer coercion, and numeric prerelease identifiers remain exact at any length within the overall string bound.

The product TypeScript parser and the Python drift gate share **one acceptance set**, pinned by `apps/desktop/src/contracts/semverParityVectors.json`, which both suites read. The gate matches with a full-string match and ASCII-only digit classes, so a trailing line terminator or a Unicode decimal digit cannot be accepted by one implementation and rejected by the other.

## Canonical channel law

Channels are exactly `stable`, `beta` and `dev` (product label `dev/internal`), with `stable` as the production default and unknown values failing closed. Channel membership is a *shape* of version — `stable` admits no prerelease, `beta` and `dev` admit only their own prerelease prefix — derived exclusively from the canonical parser rather than from a second, looser pattern. A version and a channel are a single identity, so a pair that is individually valid but mutually incompatible fails closed at service construction, in status validation and in the read model. Only a strictly newer same-channel version is eligible; downgrade, identical version and prerelease mismatch are refused with distinct reasons; and cross-channel movement is never implicit.

## Canonical update-state and authenticity law

The lifecycle has ten declared states with an explicit transition table; unknown states and undeclared transitions fail closed. `ready`, `installing` and `success` are **authenticity-dependent states**: a legal transition that would actually enter one requires an accepted authenticity proof, and this slice admits **no** cryptographic scheme, so none can be entered. Such a state cannot be asserted as a current status, cannot be a persisted event source, and cannot be claimed as successfully entered by a persisted event. A bounded *refused* attempt toward `ready` from a reachable source — `verifying -> ready` — remains recordable with the bounded refusal outcomes and asserts only that an attempt was refused.

Persisted history is semantically closed: declared states, a reachable source, a declared legal edge and an outcome that edge could actually have produced, with a persisted-outcome vocabulary narrower than the live transition vocabulary. Status snapshots are closed plain-own-data objects with exact key sets at the top level, in the error object and in every event; validation reconstructs a canonical object from validated fields, never trusts an inherited field or an accessor, and never executes a getter. Diagnostic metadata is a closed code vocabulary plus bounded, charset-restricted and credential-screened detail.

## Explicitly unapproved authority

No updater plugin, updater endpoint, HTTP client or network request; no artifact download; no installer execution; no restart; no release or tag creation; no artifact publication; no signing, notarization or key/secret access; no CI release workflow; no rollback/downgrade execution; no `bundle.active=true`; no expansion of filesystem, Git, shell/process, Cua or credential authority; no production-distributable claim; and no Settings/About side effect, background check or notification centre.

## Evidence chain (immutable stage facts)

- Independently reviewed product head `81bdd283dfd299d5ad5035301d06501f6b953a56`, tree `99151781a7cd4a886bf0ea43bb9e29ca44b16cb1`; independent HEDS `5239135676` APPROVED FOR GOVERNED MERGE with unresolved CRITICAL `0` / HIGH `0` / MEDIUM `0`.
- Product PR #80 squash-merged with expected-head protection as `c7f2a5f21369fd92b3493bea0be0192bbd7298b4`; the merge tree equals the reviewed-head tree exactly.
- Post-merge exact-main validation: Governance `35252975365` SUCCESS and Desktop Shell `35252975322` SUCCESS on that merge SHA, covering source-pack with the full Python suite and JSON contracts, native Linux governed runtime/version-drift/Git-staging, native Windows HIGH_ASSURANCE contract and staging proof, native macOS governed replacement and version-drift proofs, and desktop web/Windows/Linux/macOS.
- Post-merge review: PR comment `5718801331` APPROVED for canonical closeout preparation.

Full correction chronology and the reviewed-head record are preserved in the Work Order, the Context Lock, the Evidence Bundle and the `DEC-028` ADR; they are not restated here. The closeout stage's own review, gates and merge evidence are the mutable inputs to `HCODER_CP_0024_EFFECTIVE`; they are not recorded in this committed package and live externally in the active closeout PR and Issues #30 and #77, so this document remains true whether or not the predicate has been satisfied.

## Canonical decision

`DEC-028 — Distribution Version And Release-Channel Contract` is declared **CANONICAL / SEALED** under `HCODER-CP-0024`, effective under `HCODER_CP_0024_EFFECTIVE` and non-canonical while that predicate is unsatisfied. This checkpoint canonicalizes the bounded version, channel, update-state, persisted-event and boundary law described above and nothing beyond it.

## Closeout promotion gates

This declaration becomes effective only through the predicate above. Concretely, the promotion requires:

1. exact-head Governance on the closeout revision to be SUCCESS;
2. exact-head Desktop Shell on that revision to be SUCCESS;
3. an independent review of that exact revision reporting unresolved HIGH/CRITICAL `0/0`;
4. a governed merge of that exact revision with expected-head protection;
5. the resulting exact `main` SHA to pass fresh Governance and Desktop Shell;
6. every closeout change to remain documentation/governance only, without broadening runtime authority or altering the reviewed contract law.

While the predicate holds, `HCODER-WO-0024` is complete, `DEC-028` is CANONICAL with this checkpoint as its promotion evidence, and Issue #77 may be closed. Whether each of those has happened is external state recorded in the active closeout PR and Issues #30 and #77, not in this document.

## STOP CONDITION

Do not assert that `HCODER-CP-0024` or `DEC-028` carry canonical force except while `HCODER_CP_0024_EFFECTIVE` is satisfied. Do not begin `HCODER-DIST-001B` from this declaration. This document never claims a phase: it states the predicate and the conditional outcome, so it remains true both before and after the closeout merge.
