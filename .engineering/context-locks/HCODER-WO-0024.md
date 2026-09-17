# HCODER-WO-0024 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Authority delta:** none — contracts and inert seams only

## Source check
- Current desktop Git observation is read-only and does not execute Git.
- `tauri.conf.json` declares `productName="Hive Coder"`, `version="0.1.0"`, `bundle.active=false`.
- `Cargo.toml` declares package version `0.1.0` with Tauri `=2.11.5`; `package.json` declares version `0.1.0` with `@tauri-apps/api` `2.11.1` and `@tauri-apps/cli` `2.11.4`.
- No `UpdateService` contract, release-channel contract or version source-of-truth law existed before this Work Order.
- `tools/desktop/security_gate.py` is the established precedent for a Python, offline, read-only desktop gate that parses the same manifests.

## Selected first slice
Distribution contracts only: canonical version law with drift verifier, release-channel contract, update-state model with an authenticity gate, a Hive-owned `UpdateService` boundary whose production implementation is inert, and a bounded read-only Settings/About read model.

An updater plugin, HTTP client, download, installer, restart, signing, notarization or release publication is **not** pre-approved and is not part of this slice.

## Security law
1. Default deny; this slice adds no authority at all.
2. Update metadata and artifacts are untrusted until a later governed slice proves verification; HTTPS is never authenticity proof.
3. No model, tool or backend may mint release or update authority.
4. Signing material never enters repository, logs, prompts or runtime state.
5. Version, channel and update-state parsing fail closed on malformed or unknown input.
6. No silent downgrade; no implicit cross-channel promotion or demotion.
7. `ready`-to-install requires authenticity proof inputs; no cryptographic scheme is admitted in this slice, so install-ready is unreachable.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.
9. The inert boundary must expose no mutating, transport or installation member, and must be provably unreachable from a production side-effect path.

## Allowed-file set
This Work Order may change only:
- `.engineering/work-orders/HCODER-WO-0024.md`
- `.engineering/context-locks/HCODER-WO-0024.md`
- `.engineering/evidence/HCODER-WO-0024.md`
- `.engineering/prebuilt/HCODER-WO-0024-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0024-EXECUTOR-BRIEF.md`
- `.engineering/prebuilt/HCODER-WO-0024-ACCEPTANCE-SECURITY-MAP.md`
- `apps/desktop/src/contracts/version.ts` and `version.test.ts`
- `apps/desktop/src/contracts/releaseChannel.ts` and `releaseChannel.test.ts`
- `apps/desktop/src/contracts/updateState.ts` and `updateState.test.ts`
- `apps/desktop/src/contracts/aboutReadModel.ts` and `aboutReadModel.test.ts`
- `apps/desktop/src/lib/updateService.ts` and `updateService.test.ts`
- `tools/desktop/version_drift.py`
- `tests/desktop/__init__.py`, `tests/desktop/test_version_drift.py`
- `.github/workflows/desktop-shell.yml` and `.github/workflows/governance.yml` only for the exact version-drift gate and its native proof step

Any expansion requires an explicit Context Lock delta before code changes.

## Forbidden files
Runtime Git/filesystem/shell/Cua authority code, control-plane files, dependency manifests and lockfiles, existing security or contract tests, release/distribution implementation, updater integration, Tauri capability files, `tauri.conf.json`, `Cargo.toml`, `package.json` and release workflows.

## STOP CONDITION
STOP and return to architecture/review if the slice would require activating an updater, a network or download path, installation or restart, signing/notarization, release publication, a dependency carrying update/distribution side effects, `bundle.active=true`, a weakened HIGH_ASSURANCE gate, or any filesystem/Git/shell/Cua/credential authority expansion.
