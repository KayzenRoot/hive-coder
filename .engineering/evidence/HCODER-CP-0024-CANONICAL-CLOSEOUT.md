# HCODER-CP-0024 — Canonical Closeout

**Status:** CLOSEOUT CANDIDATE — NOT CANONICAL UNTIL INDEPENDENTLY APPROVED, GOVERNED-MERGED AND EXACT-MAIN POSTVALIDATED  
**Work Order:** `HCODER-WO-0024`  
**Decision candidate:** `DEC-028`  
**Canonical predecessor:** `HCODER-CP-0023`  
**Product PR:** `#80` — SQUASH MERGED (expected-head protected)  
**Product merge SHA:** `c7f2a5f21369fd92b3493bea0be0192bbd7298b4`  
**Issue:** `#77` — OPEN (closeout not merged)

> **Pre-merge candidate note.** On this branch this package states the *intended* canonical outcome. It carries canonical force only after this exact closeout candidate head is independently approved, squash-merged with expected-head protection, and the resulting exact `main` SHA passes fresh Governance and Desktop Shell. No future closeout merge SHA is embedded, because it does not exist yet.

## Canonical candidate boundary

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

Full correction chronology and the reviewed-head record are preserved in the Work Order, the Context Lock, the Evidence Bundle and the `DEC-028` ADR; they are not restated here. The closeout stage's own review, gates and merge SHA are deliberately not recorded in this committed package — they do not exist yet, and per the Work Order's anti-self-staling law they belong in PR #80-adjacent and Issue #30 / #77 pointers.

## Canonical decision

`DEC-028 — Distribution Version And Release-Channel Contract` is proposed as **CANONICAL / SEALED** under `HCODER-CP-0024`, effective only after the governed closeout merge and exact-main postvalidation. This checkpoint canonicalizes the bounded version, channel, update-state, persisted-event and boundary law described above and nothing beyond it.

## Closeout promotion gates

Before this closeout may merge:
1. exact-head Governance on the closeout branch must be SUCCESS;
2. exact-head Desktop Shell must be SUCCESS;
3. an independent review of this exact closeout candidate head must report unresolved HIGH/CRITICAL `0/0`;
4. the closeout changes must remain documentation/governance only and must not broaden runtime authority or alter the reviewed contract law.

After closeout merge and exact-main postvalidation, `HCODER-WO-0024` may be marked COMPLETE, Issue #77 may close, and `DEC-028` becomes CANONICAL with this checkpoint as its promotion evidence.

## STOP CONDITION

Do not mark `HCODER-CP-0024` canonical before the closeout exact-head gates, independent closeout approval, governed closeout merge and post-merge exact-main validation succeed. Do not begin `HCODER-DIST-001B` from this candidate. Never represent this candidate state as sealed while it is unmerged.
