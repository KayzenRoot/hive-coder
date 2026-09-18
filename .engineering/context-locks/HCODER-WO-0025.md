# HCODER-WO-0025 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** `#82`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001B` — native package matrix  
**Canonical base:** `HCODER-CP-0024` / `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Authority delta:** internal, unsigned native package **evidence generation only** — no signing, release, updater, install or distribution authority

> **Historical scope of the delta record.** This file is the canonical **append-only** authority and delta history for this Work Order. Every delta records what was authorised, required or true **at its own stage**; any phase, PR, review, gate or merge wording inside a delta describes that stage and is not a current-state field. Current mutable state — latest review and gate receipts, the active PR's state, and whether a promotion predicate is satisfied — lives externally in the active PR and Issues #30 and #82. Only the deltas' *law* (allowed files, prohibitions, predicates) carries forward.

## Source check

- Canonical predecessor `HCODER-CP-0024` / `DEC-028` is **CANONICAL / SEALED** on `3e1e1af7596c56716825206587bf2a88e1b179d0`; no successor slice has modified that law.
- `apps/desktop/src-tauri/tauri.conf.json` declares `version="0.1.0"`, `bundle = {"active": false}` and **no** `icon` key.
- `tools/desktop/generate_icon.py` deterministically writes `apps/desktop/src-tauri/icons/icon.ico` (single 64×64, 32-bit entry) and `icon.png` (64×64, 8-bit RGBA).
- `apps/desktop/package.json` pins `@tauri-apps/cli` to `2.11.4`; the installed CLI matches.
- Pinned CLI supports the split-build model: `tauri build --no-bundle` compiles, `tauri bundle --bundles <targets>` bundles an already-built app. `--bundles` possible values are host-platform dependent.
- Explicit bundling does **not** require `bundle.active=true`: `tauri bundle` with `bundle.active=false` produced a Windows NSIS package with no config change.
- Every existing desktop lane builds with `tauri build --no-bundle`, which never invokes the bundler — which is why the absent `bundle.icon` has never been observable in CI.
- The repository currently has **no** `actions/upload-artifact` usage and no release/tag automation.

## Selected first slice

A deterministic native package matrix for Windows, Linux and macOS that produces **bounded internal package artifacts**, validates their structure with runner-native tools, emits a deterministic inventory/hash manifest, and uploads only bounded CI evidence with short retention.

Package targets: Windows `msi` + `nsis`; macOS `app` + `dmg`; Linux `appimage` + `deb`.

Explicitly outside this slice: signing, codesign, notarization, stapling, publisher-authenticity claims, release/tag creation, GitHub Release upload, updater artifacts, update endpoints, product network fetch, download/install/restart or rollback behaviour, channel promotion, and any production-distributable claim.

## Canonical config preservation law

1. `apps/desktop/src-tauri/tauri.conf.json` is **not** edited by this Work Order. No tracked `bundle.icon`, no `bundle.active` change, no version bump, no updater or package-endpoint settings.
2. The only new bundle configuration authorised is an **ephemeral, runner-local, non-tracked overlay** supplied to the pinned CLI's explicit bundle command.
3. The overlay may contain only bundle fields strictly required to declare the **already-generated deterministic icon inputs** — and, if the pinned CLI proves it necessary, package-target-local metadata already derivable from canonical source. No signing, private-key, release or updater fields.
4. The overlay must live outside tracked source or in a guaranteed ignored/temporary runner path. It must never be committed, never uploaded as an artifact, and each job must prove tracked source is unchanged after overlay creation and use.
5. An ephemeral overlay is not canonical product config and must never be represented as a new product authority surface.

## Security law

1. Default deny; this slice adds no product runtime authority, capability, permission or IPC surface.
2. No signing certificate, notarization credential, signing key, updater key, release token or protected secret may be read, requested, printed, persisted or uploaded.
3. No package signing, codesign, notarization, stapling, publisher-authenticity claim or production-distributable claim.
4. No tag or release creation and no GitHub Release asset upload. Workflow artifacts are CI evidence only, with short explicit retention.
5. No updater plugin, update endpoint, product network fetch, artifact download/install/restart path, channel-promotion execution or rollback behaviour.
6. No new product/runtime dependency, plugin or capability. If one appears necessary, STOP for review instead of adding it.
7. Package SHA-256 proves **byte identity/integrity for evidence transport**. It is not signing and does not establish publisher authenticity; documentation and tests must say so explicitly.
8. Unsigned/unnotarized package state is expected in this slice and must never be presented as a security success.
9. Installers are never executed to satisfy acceptance. A target that can only pass by executing an installer is a STOP condition.
10. Artifact discovery is always bounded to an explicit package root and made deterministic; stale outputs cannot satisfy acceptance.

## Allowed-file set

This Work Order may change only:
- `.engineering/work-orders/HCODER-WO-0025.md`
- `.engineering/context-locks/HCODER-WO-0025.md`
- `.engineering/evidence/HCODER-WO-0025.md`
- `.engineering/prebuilt/HCODER-WO-0025-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0025-EXECUTOR-BRIEF.md`
- `.engineering/prebuilt/HCODER-WO-0025-ACCEPTANCE-SECURITY-MAP.md`
- `.github/workflows/native-package-matrix.yml`
- `tools/desktop/package_inventory.py`
- `tests/desktop/test_package_inventory.py`
- `docs/project-brain/adrs/DEC-029-NATIVE-PACKAGE-MATRIX-EVIDENCE-CONTRACT.md` and the matching `docs/project-brain/10-DECISIONS-LEDGER.md` entry, if the proposal is retained

## Forbidden files

`apps/desktop/src-tauri/tauri.conf.json`; `apps/desktop/package.json` and `apps/desktop/package-lock.json`; `apps/desktop/src-tauri/Cargo.toml` and `Cargo.lock`; every TypeScript/Python/Rust product source or test file outside the list above; `.github/workflows/governance.yml` and `.github/workflows/desktop-shell.yml`; runtime, control-plane, permission and capability code; release and packaging configuration; any dependency or lockfile change.

## STOP CONDITION

STOP and return to architecture/review if the slice would require a tracked `tauri.conf.json` change, a new tracked icon format, a product-artifact config mutation, a product dependency or plugin, a reduced approved matrix, installer execution, signing/notarization/release credentials, production release authority, a weakened or skipped existing Governance/Desktop/HIGH_ASSURANCE gate, or any filesystem/Git/shell/Cua/credential authority expansion.

---

# Context Lock Delta 001

**Status:** PREBUILT IMPLEMENTATION AUTHORISED — same Work Order  
**Authority granted:** exactly the allowed-file set above, and nothing else  
**Trigger:** Prompt 34 bounded continuation decision on Issue #82 (`5721331226`), authorising Option C — runner-local, non-tracked ephemeral bundle icon overlay through the pinned Tauri CLI config mechanism

## Recorded preflight history (immutable)

Prompt 33 stopped before implementation on Issue #82 (`5721095900`) because the Windows `msi` target could not be produced from the canonical configuration: `bundle` declared only `active: false` with no `icon` array, so WiX failed with `Couldn't find a .ico icon`. No branch, commit or PR existed — this was a preflight STOP, not a failed implementation. The independent review `5721331226` confirmed the STOP as valid and authorised a bounded ephemeral-overlay continuation rather than a canonical-config change. `DEC-028` / `HCODER-CP-0024` law and the canonical config are preserved unchanged by this delta.

## Additional law for the ephemeral overlay

1. The overlay is passed to the pinned CLI only through its `--config` mechanism, as a runner-temporary file where the CLI accepts a file path, otherwise as a correctly escaped inline JSON value; the mechanism actually used must be demonstrated per runner.
2. The overlay names only repository-existing generated icon inputs, and each referenced path must be validated to exist **after** deterministic icon generation.
3. After bundling, each job must prove `git status --porcelain` shows no unexpected tracked change, and must specifically prove `tauri.conf.json` content is unchanged.
4. Canary-first: no full-matrix claim may be made until the Windows, macOS and Linux lanes each prove their targets natively. If any lane requires a tracked config, icon-format or product-artifact change, STOP with the exact native evidence before making that change.

## STOP CONDITION (Delta 001)
In addition to the pre-existing STOP condition: STOP if any native lane requires a tracked `tauri.conf.json` or icon-format mutation, if any target can only work by reducing the approved matrix, if artifact discovery cannot be made root-bounded and deterministic, or if any step would merge the Draft PR, call Hive Coder production-distributable, or begin `HCODER-DIST-001C`.
