# HCODER-WO-0024 — Distribution Contracts, Version Model and UpdateService Boundary

**Status:** PREBUILT / IMPLEMENTATION PENDING  
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Decision:** `DEC-028` PROPOSED (version/channel source-of-truth law, not yet canonical)  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`

## Objective
Establish the first governed slice of distribution: the canonical version/channel model and a Hive-owned `UpdateService` boundary, so that later distribution work is completion-oriented rather than architecture discovery.

This slice defines **contracts and inert seams only**. It grants no update, install, download, network, signing, release or packaging authority.

## Bounded first slice
- one canonical product-version source of truth with deterministic mirrors and a drift verifier;
- strict SemVer parsing that fails closed;
- release channels `stable`, `beta`, `dev/internal`, stable as production default, unknown values fail closed;
- a deterministic update-state model with explicit legal transitions and a mandatory authenticity gate;
- a Hive-owned `UpdateService` interface with an inert, fail-closed production implementation;
- a bounded, read-only Settings/About read model;
- adversarial contract tests and evidence scaffolding.

## Canonical version law
Exactly one canonical source exists: `apps/desktop/src-tauri/tauri.conf.json` → `version`.

Rationale, from build and release semantics rather than convenience: the Tauri application version is the version the bundler and a future updater treat as the shipped product version. The Rust package version (`Cargo.toml`) and the npm package version (`package.json`) are implementation-package versions and are therefore **mirrors** that must equal the canonical value exactly. `tools/desktop/version_drift.py` enforces this deterministically and offline.

## Requested authority
None. This slice adds no runtime authority, no capability, no permission and no control-plane path.

## Explicitly not approved
No `bundle.active=true`; no updater plugin; no updater endpoint; no HTTP client or network request; no artifact download; no installer execution; no restart; no release or tag creation; no artifact publication; no signing, notarization or key/secret access; no CI release workflow; no rollback/downgrade execution; no expansion of filesystem, Git, shell/process, Cua or credential authority; no production-distributable claim; no Settings/About side effect, background check, notification centre or broad UI redesign.

## Security / supply-chain law
1. Update metadata and artifacts are untrusted input until a later governed slice proves cryptographic verification.
2. HTTPS is never treated as authenticity proof.
3. Models, tools and backends cannot mint release or update authority.
4. Signing material must never appear in repository, logs, prompts or runtime state.
5. Version, channel and update-state parsing fails closed on malformed or unknown input.
6. No silent downgrade and no implicit cross-channel promotion or demotion.
7. `ready`-to-install state structurally requires authenticity/integrity proof inputs; this slice admits **no** cryptographic scheme, so install-ready is unreachable by construction.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.

## Acceptance law
Prebuilt contract tests come first. Promotion requires: canonical-and-mirrors drift lock, fail-closed unknown/malformed version and channel, illegal-transition rejection, downgrade and cross-channel refusal, install-ready refusal without accepted authenticity proof, bounded redaction-safe error metadata, proof that the inert boundary exposes no mutating/transport/install member, proof that no network/process/update side effect is reachable, and independent Windows/Linux/macOS evidence.

## Preserved exclusions
No commit/ref/branch/tag mutation; no checkout/reset/restore/clean/stash; no merge/rebase/cherry-pick; no remote/network/credentials; no hooks or executable filters; no generic shell/process/terminal; no arbitrary `.git` write authority; no desktop/Tauri mutation expansion.

## STOP CONDITION
If completing this slice requires activating an updater plugin, a network or download path, installation or restart, signing/notarization, release publication, a dependency that introduces update or distribution side effects, or weakening an existing HIGH_ASSURANCE gate, stop and create the smallest explicit governed delta. Do not smuggle distribution authority into this Work Order.
