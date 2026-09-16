# HCODER-PLATFORM-001 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** `#63`  
**Base:** `f192d20065d915636397c33f8f82adf4f313625e`  
**Risk:** T2 platform/CI, no authority expansion

## Problem statement
Hive Coder currently has objective Windows desktop-native evidence, Ubuntu shared/runtime evidence and a dedicated macOS governed-filesystem lane, but the three target operating systems are not represented by one explicit first-class platform support contract. Linux and macOS native desktop/Tauri evidence are missing from the desktop workflow. Linux governed-filesystem evidence is embedded in the broad Ubuntu source-pack rather than represented as an explicit native platform claim.

## Source-of-truth lock
Read in this order before execution:
1. `docs/project-brain/11-CHECKPOINT.md`
2. `docs/project-brain/10-DECISIONS-LEDGER.md` and canonical ADRs
3. `docs/project-brain/03-SCOPE.md`
4. `docs/project-brain/09-DEFINITION-OF-DONE.md`
5. `docs/project-brain/04-ARCHITECTURE.md`
6. `docs/project-brain/02-REQUIREMENTS.md`
7. Issue `#63`
8. `.engineering/prebuilt/HCODER-PLATFORM-001-IMPLEMENTATION-PACK.md`

## Observed current CI
### Governance
- `source-pack`: Ubuntu, exact-head, canonical pack, foundation checks, Python compile, full unit discovery.
- `control-plane-windows`: Windows, exact-head, governed runtime compile and HIGH_ASSURANCE focused suite.
- `workspace-replace-macos`: macOS, exact-head, governed filesystem compile and native replacement contract/security suite.

### Desktop Shell
- `desktop-web`: Ubuntu shared web/typecheck/test/build/audit gate.
- `desktop-windows`: Windows exact-head, pinned Node/Rust, RustSec audit, Rust tests/check, Tauri build without bundle and launch smoke.
- No Linux native Tauri job is present at this lock.
- No macOS native Tauri job is present at this lock.

## Allowed-file set for this increment
Executor may modify only:
- `.github/workflows/governance.yml`
- `.github/workflows/desktop-shell.yml`
- `.engineering/context-locks/HCODER-PLATFORM-001.md`
- `.engineering/prebuilt/HCODER-PLATFORM-001-IMPLEMENTATION-PACK.md`
- `.engineering/evidence/HCODER-PLATFORM-001.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/06-TEST-BENCHMARK-PLAN.md`
- `docs/project-brain/07-DEPLOYMENT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- one new ADR for the first-class platform validation law if needed
- focused platform-support test/contract files only if a code-level support-state contract is introduced.

Any additional file requires a same-issue Context Lock delta explaining why.

## Fixed implementation direction
1. Preserve `desktop-web` and `desktop-windows` semantics.
2. Add explicit Linux and macOS native desktop/Tauri jobs, preferably by a matrix only if readability and platform-specific dependencies remain auditable.
3. Native jobs must exact-head checkout and print platform/toolchain identity.
4. Use the repository's pinned Node `24.21.0` and Rust `1.98.1` unless objective incompatibility proves a correction is necessary.
5. Use `cargo test --locked`, `cargo check --locked` and a credential-free Tauri build/check surface appropriate to the runner.
6. Linux runner must install only the minimal native system packages required by Tauri/WebKitGTK using auditable package-manager commands.
7. macOS runner must not be treated as Linux/POSIX-equivalent; it receives its own native desktop proof.
8. Packaging/signing/notarization is not part of this increment.
9. No runtime capability, desktop plugin or permission expansion is permitted.

## Evidence law
A platform/surface may move from `UNPROVEN` to `PROVEN_CI` only when an exact-head native job is green and its logs identify runner OS and relevant toolchain. `RELEASE_VALIDATED` is reserved for later package/install/smoke evidence.

## STOP CONDITION
Stop and open a correction delta if native Tauri proof requires new privileged desktop plugins, secrets/signing credentials, weakening a canonical security gate, unpinned remote executable installation, or scope outside the allowed-file set. Do not call the platform matrix complete while Linux or macOS native desktop evidence is absent.