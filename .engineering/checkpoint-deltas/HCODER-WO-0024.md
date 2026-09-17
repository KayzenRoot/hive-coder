# Checkpoint Delta / Closeout — HCODER-WO-0024

**Status:** CANONICAL CLOSEOUT CANDIDATE — NOT YET MERGED, NOT YET SEALED  
**Work Order:** `HCODER-WO-0024 — Distribution Contracts, Version Model and UpdateService Boundary`  
**Intended decision state:** `DEC-028` — CANONICAL / SEALED under `HCODER-CP-0024`  
**Issue:** `#77` — OPEN  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Product PR:** `#80` — **MERGED** by squash with expected-head protection  
**Canonical product merge:** `c7f2a5f21369fd92b3493bea0be0192bbd7298b4`  
**Disclosed conflicts:** none

> **Pre-merge candidate semantics.** On this branch this document states a *proposed* final source state. It gains canonical force only after this exact closeout candidate is independently approved, governed-merged with expected-head protection, and exact-main postvalidated. No future closeout merge SHA is invented or embedded here, and no moving `current main` field is created.

## Purpose

Record the intended canonical outcome of the first governed distribution/version-contract slice. The **product** implementation is already merged and exact-main postvalidated; the **closeout** is what remains.

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

These are immutable lifecycle-stage facts and are not live repository pointers. The closeout stage's own review, gates and merge SHA are deliberately **not** recorded here: they do not exist yet, and per the anti-self-staling law in Context Lock Delta 007 they belong in PR and Issue pointers rather than in a pre-CI commit.

## Not changed by this delta

No product behaviour, runtime authority, contract law, workflow behaviour, dependency state or test semantics changes. The version law, channel law, authenticity law, persisted-event law, validation law and `UpdateService` boundary are exactly as independently reviewed at `81bdd283`. What this closeout candidate advances is lifecycle/canonical status only.

## STOP CONDITION (candidate state)

This document is a **candidate**. It grants no additional authority, capability, scope or behaviour change, and it must not be represented as sealed until the governed closeout merge and exact-main postvalidation have occurred. No further repository mutation under `HCODER-WO-0024` is authorised by it. Any new product behaviour requires a newly governed Work Order with its own Context Lock, allowed files and exact-head gates.
