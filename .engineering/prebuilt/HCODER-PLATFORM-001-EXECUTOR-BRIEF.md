# HCODER-PLATFORM-001 — Executor Brief

## Mission
Complete the first-class Windows/Linux/macOS CI validation matrix without redesigning Hive Coder and without expanding authority.

## Read first
1. `.engineering/context-locks/HCODER-PLATFORM-001.md`
2. `.engineering/prebuilt/HCODER-PLATFORM-001-IMPLEMENTATION-PACK.md`
3. `.engineering/evidence/HCODER-PLATFORM-001.md`
4. Issue `#63`
5. current `.github/workflows/governance.yml`
6. current `.github/workflows/desktop-shell.yml`

## Current delta already identified
Windows desktop-native is proven. Linux and macOS desktop-native Tauri lanes are missing. macOS governed filesystem already has a dedicated native lane. Linux runtime/POSIX proof exists inside Ubuntu source-pack but should become an explicit platform claim/lane without duplicating the full suite unnecessarily.

## Execute in this order
1. Preserve all existing gates exactly unless a documented contradiction requires a correction.
2. Add an explicit Linux native governed-runtime/filesystem job or split the relevant native proof from source-pack while retaining full source-pack.
3. Add Linux native desktop/Tauri compile/build evidence using minimal runner dependencies.
4. Add macOS native desktop/Tauri compile/build evidence independently.
5. Print OS/toolchain identity in each native job.
6. Run exact-head CI.
7. Fix only same-issue failures. Do not broaden scope.
8. Update Evidence Ledger with exact run/job evidence.
9. HEDS review before promotion.

## Required commands/surfaces
Desktop native jobs should use the existing locked graphs and, where supported by the runner:
- `npm ci --ignore-scripts --no-audit`
- `cargo test --locked --manifest-path apps/desktop/src-tauri/Cargo.toml`
- `cargo check --locked --manifest-path apps/desktop/src-tauri/Cargo.toml`
- `npm run tauri -- build --no-bundle` or a narrower credential-free native build command if the runner cannot launch a GUI deterministically.

Do not invent package/signing steps.

## Success contract
- Windows native desktop remains green.
- Linux native desktop becomes `PROVEN_CI`.
- macOS native desktop becomes `PROVEN_CI`.
- Linux native governed runtime/filesystem claim becomes explicit and green.
- macOS governed filesystem remains green.
- shared web/source-pack remain green.
- HEDS unresolved HIGH/CRITICAL = `0/0`.

## STOP
If a platform requires a security weakening, privileged Tauri plugin, secret/signing credential, or ungoverned authority to pass, stop that surface as `UNPROVEN` and report the blocker. Never fake platform parity.