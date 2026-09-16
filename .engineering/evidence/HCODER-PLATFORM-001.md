# HCODER-PLATFORM-001 — Evidence Ledger

**Status:** CANONICAL / PROVEN_CI MATRIX COMPLETE  
**Issue:** `#63` — CLOSED  
**Product merge:** `22b56b0f3111158cbf50789b1647c5a578a171c1`

## Claim matrix
| Surface | Windows | Linux | macOS |
|---|---|---|---|
| Shared Python/runtime regression | PROVEN_CI | PROVEN_CI | PROVEN_CI |
| Governed filesystem native proof | PROVEN_CI | PROVEN_CI | PROVEN_CI |
| Desktop web contract | shared PROVEN_CI | shared PROVEN_CI | shared PROVEN_CI |
| Desktop native Rust/Tauri compile/build | PROVEN_CI | PROVEN_CI | PROVEN_CI |
| Desktop launch smoke | PROVEN_CI | UNPROVEN | UNPROVEN |
| Release package/install | UNPROVEN | UNPROVEN | UNPROVEN |

## Exact-head promotion evidence
Promotion head: `0410f98e04a49acf3fb555a41198614daa0ab728`.

- Governance run `#334`, run ID `35096584877`: SUCCESS at exact promotion head.
- Desktop Shell run `#170`, run ID `35096584828`: SUCCESS at exact promotion head.
- `desktop-web`: shared security gate, exact npm graph, typecheck, component/contract tests, production web build and npm audit passed.
- `desktop-windows`: native Rust tests/check, Tauri Windows build without bundle and Windows launch smoke passed.
- `desktop-linux`: native runner/toolchain identity, minimal Tauri system dependencies, locked Rust tests/check with `rfd/gtk3`, and Tauri Linux build without bundle passed.
- `desktop-macos`: native runner/toolchain identity, locked Rust tests/check and Tauri macOS build without bundle passed independently from Linux.
- Formal HEDS FINAL review ID `5222762601`: APPROVED FOR PROMOTION, unresolved HIGH/CRITICAL `0/0`.

## Canonical merge and post-merge proof
PR `#67` was squash merged as `22b56b0f3111158cbf50789b1647c5a578a171c1`.

Post-merge exact-main validation:
- Governance `#335`, run ID `35097458521`: SUCCESS at `22b56b0f3111158cbf50789b1647c5a578a171c1`.
- Desktop Shell `#171`, run ID `35097458312`: SUCCESS at `22b56b0f3111158cbf50789b1647c5a578a171c1`.

Issue `#63` was closed after those post-merge gates completed successfully.

## Security assertions
- no new Tauri privileged plugin or runtime capability was introduced;
- desktop cannot mint privileged permits;
- Permission & Control Plane and HIGH_ASSURANCE filesystem boundaries were not weakened;
- no signing, notarization, store credential or release secret was introduced;
- macOS proof is independent and is not inferred from Linux;
- compile/build proof is not represented as launch-smoke or package/install proof.

## Support-state law
`PROVEN_CI` means the named surface has objective native CI evidence. It does not imply release packaging, installation validation, signing/notarization, or production-readiness.

`RELEASE_VALIDATED=false` remains canonical for Windows, Linux and macOS until later packaging/install/signing work orders produce their own exact-head evidence.

Linux and macOS desktop launch smoke remain `UNPROVEN`; only Windows has an objective launch-smoke claim in this checkpoint.

## Closeout
HCODER-PLATFORM-001 is complete for its intended scope: all three target operating systems are first-class native CI targets for the runtime/filesystem and desktop native compile/build surfaces. Remaining launch-smoke and release-packaging gaps are explicit future work, not hidden assumptions.