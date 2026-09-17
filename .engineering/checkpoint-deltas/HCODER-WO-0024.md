# Checkpoint Delta / Closeout — HCODER-WO-0024

**Status:** DURABLE CLOSEOUT DECLARATION — CONDITIONAL EFFECTIVENESS (`HCODER_CP_0024_EFFECTIVE`)  
**Work Order:** `HCODER-WO-0024 — Distribution Contracts, Version Model and UpdateService Boundary`  
**Declared decision state:** `DEC-028` — CANONICAL / SEALED under `HCODER-CP-0024`, effective under the predicate below  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Product PR:** `#80` — squash merged with expected-head protection  
**Canonical product merge:** `c7f2a5f21369fd92b3493bea0be0192bbd7298b4`  
**Disclosed conflicts:** none

## Effectiveness predicate

`HCODER_CP_0024_EFFECTIVE` is satisfied if and only if all three hold for one and the same closeout revision:

- (a) that exact closeout candidate revision was independently reviewed with unresolved HIGH/CRITICAL `0/0`;
- (b) that exact revision was governed-merged with expected-head protection;
- (c) the resulting exact `main` SHA passed fresh Governance and Desktop Shell.

**Before** the predicate is satisfied, `HCODER-CP-0023` and the non-canonical `DEC-028` state remain authoritative. **Once** it is satisfied, `HCODER-CP-0024` and `DEC-028` are CANONICAL / SEALED under the declaration in this document, with no repository-document rewrite required merely to flip phase or status wording.

The predicate deliberately depends on no merge SHA, run ID, review ID, Issue state, PR state or moving `current main` field. Evidence of whether it is satisfied lives externally in the active closeout PR and Issues #30 and #77.

## Purpose

Declare the canonical outcome of the first governed distribution/version-contract slice. The **product** implementation is merged and exact-main postvalidated as recorded below; this document supplies the durable closeout declaration whose effect is governed by the predicate above.

This delta creates no new authority and changes no behaviour. It records lifecycle and canonical status only.

## What is admitted (already merged and postvalidated)

The first governed slice of `HCODER-DIST-001A`, as contracts and inert seams only:

- **One canonical product-version source**: `apps/desktop/src-tauri/tauri.conf.json` → `version`, with `apps/desktop/src-tauri/Cargo.toml` and `apps/desktop/package.json` as exact mirrors enforced by a deterministic, offline drift verifier.
- **A toolchain-compatible bounded SemVer 2.0.0 profile**: each core `major`/`minor`/`patch` within `0..9007199254740991`, the whole version string at most 128 characters, accepted core values compared as exact decimal strings with no floating-point conversion and no platform-dependent integer coercion. The core bound follows the narrowest declared mirror consumer (npm's `node-semver`), not the widest.
- **One acceptance set across languages**: the product TypeScript parser and the Python drift gate accept and reject exactly the same versions, pinned by a shared cross-language parity vector file.
- **Release channels** `stable`, `beta` and `dev` (product label `dev/internal`), with channel membership a shape of version, version+channel as a single identity, no implicit cross-channel movement and no silent downgrade.
- **A closed update-state model** in which `ready`, `installing` and `success` are authenticity-dependent: while no authenticity scheme is admitted they cannot be entered by a legal transition, asserted as a current status, used as a persisted event source, or claimed as successfully entered. A bounded *refused* attempt toward `ready` remains recordable and asserts only a refusal.
- **A semantically closed persisted-event law** reusing one validator, with a persisted-outcome vocabulary narrower than the live transition vocabulary.
- **Closed, plain-own-data status validation** with exact key sets at every level and a zero-getter rule.
- **A bounded, read-only Settings/About read model.**
- **A Hive-owned inert `UpdateService` boundary** exposing no mutating, transport or installation member.

## What remains explicitly unapproved

No updater plugin, endpoint, HTTP client or network request; no download, installer, restart or rollback execution; no signing, notarization, key or secret access; no release/tag creation or artifact publication; no CI release workflow; no dependency addition; no `bundle.active=true`; no expansion of filesystem, Git, shell/process, Cua or credential authority; no production-distributable claim. `bundle.active` remains `false`.

This checkpoint also does not approve packaging, installer generation, transport, channel promotion execution, rollback policy or any later `HCODER-DIST-001` slice.

## Lifecycle evidence (immutable stage facts)

| Stage | Fact |
|---|---|
| Independently reviewed product head | `81bdd283dfd299d5ad5035301d06501f6b953a56` |
| Reviewed-head tree | `99151781a7cd4a886bf0ea43bb9e29ca44b16cb1` |
| Independent product HEDS | `5239135676` — APPROVED FOR GOVERNED MERGE, CRITICAL `0` / HIGH `0` / MEDIUM `0` |
| Pre-merge base `main` | `b6aff55ac12c1d31a883878f1d8478d642fbe8e6` |
| Product merge (squash, expected-head protected) | `c7f2a5f21369fd92b3493bea0be0192bbd7298b4` |
| Merge tree | `99151781a7cd4a886bf0ea43bb9e29ca44b16cb1` — identical to the reviewed-head tree |
| Post-merge Governance | `35252975365` SUCCESS on that exact merge SHA |
| Post-merge Desktop Shell | `35252975322` SUCCESS on that exact merge SHA |
| Post-merge review | PR comment `5718801331` — APPROVED for canonical closeout preparation |

Post-merge exact-main validation covered: source-pack with the full Python suite and JSON contract validation; native Linux governed runtime, version-drift and governed Git staging proofs; native Windows HIGH_ASSURANCE contract tests and governed Git staging proof; native macOS governed replacement and version-drift proofs; and desktop web (security gate, version drift gate, typecheck, contracts, production build, dependency audit) plus the Windows, Linux and macOS Rust/Tauri lanes. Every required lane belonged to the merge SHA; none was inferred from an adjacent commit.

These are immutable lifecycle-stage facts and are not live repository pointers. The *closeout* stage's own review, gates and merge evidence are deliberately **not** recorded here: they are the mutable inputs to `HCODER_CP_0024_EFFECTIVE` and live externally in the active closeout PR and Issues #30 and #77. This document therefore stays true whether or not the predicate has been satisfied.

## Not changed by this delta

No product behaviour, runtime authority, contract law, workflow behaviour, dependency state or test semantics changes. The version law, channel law, authenticity law, persisted-event law, validation law and `UpdateService` boundary are exactly as independently reviewed at `81bdd283`. What this closeout declaration governs is lifecycle/canonical status only, and only through the predicate above.

## STOP CONDITION

This declaration grants no additional authority, capability, scope or behaviour change. `HCODER-CP-0024` and `DEC-028` carry canonical force only while `HCODER_CP_0024_EFFECTIVE` is satisfied, and no repository text asserts that it is. No further repository mutation under `HCODER-WO-0024` is authorised by it. Any new product behaviour requires a newly governed Work Order with its own Context Lock, allowed files and exact-head gates.
