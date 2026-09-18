# HCODER-WO-0025 — Native Package Matrix In CI For Windows, Linux And macOS

**Status:** IMPLEMENTATION AND EVIDENCE CONTRACT MATERIALIZED IN SOURCE — PROMOTION SATISFACTION EXTERNAL  
**Promotion law:** the contract, workflow, tool and tests this Work Order defines exist in source. Whether a particular exact head satisfies promotion evidence — hosted exact-head Governance, Desktop Shell and Native Package Matrix green, an independent HEDS review with unresolved HIGH/CRITICAL `0/0`, and a governed expected-head merge — is mutable external state tracked in PR #83 and Issues #30 and #82, and is deliberately not encoded here.
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0024` / `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Decision:** `DEC-029` PROPOSED / NOT CANONICAL (native package matrix evidence contract), if retained  
**Issue:** `#82`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001B`  
**Preflight history (historical):** Prompt 33 preflight STOP on Issue #82 (`5721095900`); independent review `5721331226` confirmed the STOP and authorised the bounded ephemeral-overlay continuation.

**Promotion evidence:** hosted exact-head gates, an independent HEDS review with unresolved HIGH/CRITICAL `0/0` and a governed expected-head merge are each required against the exact head the promotion decision names; that mutable state is tracked in the active PR and Issues #30 and #82, not in this document.

## Objective

Establish the first governed native packaging layer for Hive Coder: a deterministic CI package matrix for Windows, Linux and macOS that produces bounded **internal** package artifacts, validates their structure with runner-native tools, emits a deterministic inventory/hash manifest, and uploads only bounded CI evidence — while preserving every existing exact-head, HIGH_ASSURANCE and distribution-contract guard.

## Bounded first slice

- One additional workflow, `.github/workflows/native-package-matrix.yml`, parallel to `Governance` and `Desktop Shell` and weakening neither.
- Package targets: Windows `msi` + `nsis`; macOS `app` + `dmg`; Linux `appimage` + `deb`.
- A stdlib-only deterministic package inventory/validator (`tools/desktop/package_inventory.py`) with focused unit tests.
- Runner-native, non-install structural checks per package type.
- Bounded workflow-artifact evidence upload with short retention.

## Requested authority

Internal unsigned package **evidence generation** on GitHub-hosted runners only. No runtime authority, no capability, no permission, no IPC command, no plugin, no product dependency and no user-facing update behaviour.

## Canonical config preservation

`apps/desktop/src-tauri/tauri.conf.json` is not edited: version stays `0.1.0`, `bundle.active` stays `false`, and no tracked `bundle.icon` is added. Bundling uses the pinned CLI's split-build model — `tauri build --no-bundle`, then `tauri bundle --bundles <targets>` with an **ephemeral, runner-local, non-tracked** config overlay that declares only the already-generated deterministic icon inputs.

## Explicitly not approved

No signing, codesign, notarization, stapling or publisher-authenticity claim; no release or tag creation and no GitHub Release asset upload; no updater plugin, artifact or update endpoint; no product network fetch; no download, install, restart or rollback execution; no installer execution as acceptance; no channel promotion; no `bundle.active=true`; no new dependency, plugin, permission or capability; no expansion of filesystem, Git, shell/process, Cua or credential authority; no production-distributable claim; no `HCODER-DIST-001C` work.

## Security / supply-chain law

1. This slice adds no product authority; package artifacts are **internal unsigned evidence**, never a trusted or production artifact.
2. Package SHA-256 proves byte identity/integrity for evidence transport only; it is not signing and establishes no publisher authenticity.
3. Unsigned/unnotarized state is expected here and is never reported as a security success.
4. No signing material, notarization credential, key, release token or protected secret may be read, requested, printed, persisted or uploaded.
5. Workflow artifacts carry only generated package outputs and their inventory manifest — never repository source, caches, user data, logs with tokens, signing material or arbitrary workspace content.
6. Artifact discovery is bounded to an explicit package root, created deterministically per job, and never uses repository-wide recursive wildcards.
7. The ephemeral overlay never becomes canonical config, is never committed or uploaded, and each job proves tracked source is unchanged after bundling.
8. Installers are never executed to satisfy acceptance.

## Acceptance law

Promotion requires: a green Windows, macOS and Linux package lane on the exact head; a deterministic, closed, root-bounded inventory whose adversarial negatives all fail closed (missing, duplicate, unexpected and zero-size package types, wrong version, wrong source SHA, absolute path, traversal, symlink escape, artifact outside root, hash mutation, tree mutation, discovery-order shuffle); the ephemeral-overlay tracked-source guard passing; existing Governance and Desktop Shell lanes still green and unweakened; and an independent HEDS review with unresolved HIGH/CRITICAL `0/0`.

## Preserved exclusions

The `HCODER-CP-0024` / `DEC-028` law is unchanged: canonical version source and exact mirrors, the toolchain-compatible bounded SemVer profile with shared TS/Python acceptance vectors, channel identity, the authenticity law, the persisted-event law, plain-own-data validation with the zero-getter rule, the bounded About read model and the inert Hive-owned `UpdateService` boundary.

## STOP CONDITION

If completing this slice requires a tracked `tauri.conf.json` or icon-format mutation, a new dependency or plugin, signing/notarization credentials, release publication, installer execution, a reduced approved matrix, a weakened HIGH_ASSURANCE gate, or any filesystem/Git/shell/Cua/credential expansion, stop and create the smallest explicit governed delta. Do not smuggle distribution authority into this Work Order.
