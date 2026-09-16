# HCODER-PLATFORM-001 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION — CI CORRECTION DELTA 001  
**Issue:** `#63`  
**Base:** `f192d20065d915636397c33f8f82adf4f313625e`  
**Risk:** T2 platform/CI, no authority expansion

## Problem statement
Hive Coder needs one explicit first-class validation contract for Windows, Linux and macOS. Windows desktop-native evidence already exists; this increment makes Linux runtime evidence explicit and adds Linux/macOS native desktop evidence without expanding authority.

## Source-of-truth lock
Read in this order before execution: `11-CHECKPOINT.md` → Decisions/ADRs → Scope → DoD → Architecture → Requirements → Issue `#63` → Implementation Pack.

## CI Correction Delta 001
First exact-head execution at `62a81ebad4fd96b2dddb0090f6221d4eaad3b55b` produced objective platform-specific build failures while Governance #329 was fully green, including the new `governed-runtime-linux` job. Windows native desktop and shared desktop-web also remained green.

- macOS reached Rust compilation but `tauri::generate_context!()` failed because Tauri expects `apps/desktop/src-tauri/icons/icon.png`; the deterministic generator creates only Windows `icon.ico`.
- Linux reached Rust compilation but `rfd 0.17.2` failed because default features are disabled and no Linux backend (`gtk3` or `xdg-portal`) is selected.

These are cross-platform build-contract gaps, not permission/runtime-authority requirements. Same-issue correction is authorized with the smallest additional surfaces.

## Allowed-file set
- `.github/workflows/governance.yml`
- `.github/workflows/desktop-shell.yml`
- `.engineering/context-locks/HCODER-PLATFORM-001.md`
- `.engineering/prebuilt/HCODER-PLATFORM-001-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-PLATFORM-001-EXECUTOR-BRIEF.md`
- `.engineering/evidence/HCODER-PLATFORM-001.md`
- `apps/desktop/src-tauri/Cargo.toml` only for target-specific native dependency feature selection
- `apps/desktop/src-tauri/Cargo.lock` only if Cargo legitimately changes the locked graph
- `tools/desktop/generate_icon.py` only to add deterministic PNG generation while preserving ICO behavior
- project-brain Architecture/Test/Deployment/Decisions docs and one platform ADR if needed
- focused platform-support tests only if a code-level support-state contract is introduced.

Any additional file requires another same-issue Context Lock delta.

## Fixed correction direction
1. Preserve existing Windows and shared web semantics.
2. Keep Linux and macOS native jobs independent and exact-head.
3. Keep Node `24.21.0` and Rust `1.98.1` pinned.
4. Select the Linux `rfd` backend only under Linux target configuration. Prefer `gtk3`, matching the already-installed GTK3/Tauri runner surface, rather than introducing a second portal stack.
5. Extend deterministic icon generation to produce the PNG Tauri expects while preserving the existing Windows ICO output.
6. No privileged Tauri plugin, signing/notarization, runtime capability, permit authority or security-gate weakening is permitted.

## Evidence law
A platform/surface moves from `UNPROVEN` to `PROVEN_CI` only after a green exact-head native job with runner/toolchain identity. `RELEASE_VALIDATED` remains a later packaging/install/smoke gate.

## STOP CONDITION
Stop and open another correction delta if native proof requires privileged desktop plugins, secrets/signing credentials, weakening canonical security, unpinned remote executable installation or scope outside this corrected allowed-file set. Do not call the platform matrix complete while Linux or macOS native desktop evidence is absent.