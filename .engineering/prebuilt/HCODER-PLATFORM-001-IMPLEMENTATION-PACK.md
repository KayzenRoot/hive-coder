# HCODER-PLATFORM-001 — Prebuilt Implementation Pack

**Status:** PREBUILT / EXECUTION NOT YET PROMOTED  
**Issue:** `#63`  
**Canonical base:** `f192d20065d915636397c33f8f82adf4f313625e`  
**Purpose:** remove platform-discovery work from the later Codex-heavy phase.

## Objective
Make Windows, Linux and macOS explicit first-class Hive Coder targets through one platform-neutral product contract and evidence-backed native adapters/gates. This increment does not grant new privileged authority.

## Target matrix
| Surface | Windows | Linux | macOS |
|---|---|---|---|
| Python/runtime contracts | required | required | required |
| Filesystem HIGH_ASSURANCE native tests | required | required | required |
| Desktop web contract | shared required gate | shared required gate | shared required gate |
| Tauri native check/build | required | required | required |
| Native smoke | required before production-ready claim | required before production-ready claim | required before production-ready claim |
| Packaging | MSI/EXE candidate | AppImage/DEB candidate | APP/DMG candidate |
| Architecture adapter | Win32/NT | POSIX/Linux | POSIX/Darwin |

## Prebuilt executor map
Implementation-heavy executor MUST work from these fixed concerns instead of rediscovering scope:

1. **Platform-neutral contract**
   - define stable platform identifiers: `windows`, `linux`, `macos`;
   - expose support state independently for runtime, desktop-native and packaging surfaces;
   - never infer Darwin support from Linux/POSIX success;
   - never call a platform production-ready from shared/unit tests alone.

2. **Runtime/native evidence**
   - retain existing exact-head Governance source-pack;
   - retain native Windows HIGH_ASSURANCE lane;
   - retain dedicated native macOS replacement lane;
   - add/normalize a dedicated Linux native lane when its proof is currently embedded only in Ubuntu source-pack;
   - platform-specific filesystem/link/reparse/race tests remain mandatory where relevant.

3. **Desktop/Tauri evidence**
   - preserve current desktop web contract gate;
   - add OS-matrix native Tauri check/build lanes without adding privileged plugins;
   - verify the Tauri shell remains read-only with respect to governed runtime mutation authority;
   - use exact-head checkout and toolchain versions visible in logs.

4. **Packaging boundary**
   - define package targets now, but do not silently claim release readiness;
   - packaging implementation/release signing/notarization belongs to a later governed release increment unless already safely testable without secrets;
   - no signing secrets, developer certificates or store credentials may be introduced by this issue.

## Expected implementation files
Executor should prefer the existing architecture and touch the smallest set needed. Likely surfaces:
- `.github/workflows/governance.yml`
- `.github/workflows/desktop-shell.yml` or a dedicated platform-native workflow if separation is clearer
- `apps/desktop/**` Tauri configuration/build metadata already owned by desktop shell
- platform support documentation under `docs/project-brain/`
- focused platform tests under `tests/runtime/`

Before editing, executor MUST inspect actual current paths and record an exact allowed-file list in a Context Lock. Do not invent duplicate configuration trees.

## CI contract
Each platform-native job MUST:
- run on a GitHub-hosted runner matching the declared OS;
- checkout the exact PR/head SHA;
- expose OS image/toolchain identity in logs;
- compile/check the governed runtime or desktop surface it claims;
- execute platform-specific tests relevant to that claim;
- fail closed if a required native dependency/toolchain is unavailable;
- avoid network-fetched executable bootstrap scripts unless already governed/pinned by repository policy.

## Platform support state
Use three states per surface:
- `UNPROVEN`: no objective native evidence;
- `PROVEN_CI`: exact-head native CI evidence exists;
- `RELEASE_VALIDATED`: packaging/install/smoke evidence exists under a later release gate.

`PROVEN_CI` is not synonymous with production-ready. `RELEASE_VALIDATED` requires its own evidence.

## Security invariants
- no new filesystem/process/shell/Git/Cua authority;
- no desktop permit minting;
- no weakening of Permission & Control Plane;
- no weakening of `write_file_v1` or canonical `replace_file_v1`;
- no platform-specific bypass for approval/permit/cancellation/session laws;
- no hidden fallback from native safety primitive to weaker generic behavior;
- unsupported platform/filesystem combinations fail closed.

## Acceptance tests to prebuild/normalize
- platform identifier/support-state contract tests;
- Windows native governed filesystem regression suite;
- Linux native symlink/path/race regression suite;
- macOS native symlink/path/race regression suite;
- desktop native `cargo check` or equivalent Tauri compile gate on all three OS runners;
- build/smoke proof where deterministic and credential-free;
- negative test/documented assertion that desktop shell has no privileged write/process plugin authority.

## Codex handoff shape
The future executor receives:
`Checkpoint → Issue #63 → Context Lock → this Implementation Pack → exact allowed-file list → executable acceptance tests → platform matrix → evidence template`.

Its job is to complete missing implementation and make the prewritten tests/gates pass. It must not redesign platform architecture during execution unless a contradiction is proven and captured as a correction delta.

## STOP CONDITION
Do not call Windows/Linux/macOS first-class complete until each declared `PROVEN_CI` surface has objective native exact-head evidence. Do not expand runtime authority. Do not introduce release signing secrets. Do not call packaging production-ready before a later release-validation increment proves installation/smoke behavior.