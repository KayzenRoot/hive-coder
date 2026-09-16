# HCODER-PLATFORM-001 — Evidence Ledger

**Status:** PREBUILT / NATIVE MATRIX INCOMPLETE  
**Issue:** `#63`

## Claim matrix
| Surface | Windows | Linux | macOS |
|---|---|---|---|
| Shared Python/runtime regression | PROVEN_CI | PROVEN_CI via Ubuntu source-pack | partial native evidence |
| Governed filesystem native proof | PROVEN_CI | PROVEN_CI via Ubuntu/POSIX tests, explicit lane pending normalization | PROVEN_CI dedicated lane |
| Desktop web contract | shared PROVEN_CI | shared PROVEN_CI | shared PROVEN_CI |
| Desktop native Rust/Tauri compile/build | PROVEN_CI | UNPROVEN | UNPROVEN |
| Desktop launch smoke | PROVEN_CI | UNPROVEN | UNPROVEN |
| Release package/install | UNPROVEN | UNPROVEN | UNPROVEN |

## Existing objective evidence inherited from canonical main
- WO-0022/CP-0022 established native Windows governed-filesystem and dedicated macOS replacement proof.
- Desktop Shell canonical workflow contains a Windows native Tauri build-without-bundle plus launch smoke.
- Ubuntu `source-pack` executes full Python test discovery and is evidence for shared/POSIX runtime behavior, but HCODER-PLATFORM-001 should make the Linux-native claim explicit rather than hiding it inside a generic source-pack label.

## Required new evidence
- exact-head Linux native desktop/Tauri job;
- exact-head macOS native desktop/Tauri job;
- explicit Linux native runtime/filesystem job or clearly separated evidence step whose claim is auditable;
- unchanged/green Windows native desktop and runtime gates;
- unchanged/green shared desktop-web and source-pack gates;
- HEDS review with unresolved HIGH/CRITICAL `0/0` before promotion.

## Evidence recording template
For each new native job record:
- exact head SHA;
- workflow/run number and run ID;
- job ID;
- runner OS/image details;
- Node/Rust/Python versions as applicable;
- exact test/check/build commands;
- pass/fail counts when available;
- any skipped native behavior and why;
- support-state transition justified by the evidence.

## Security assertions to verify during review
- no new Tauri privileged plugin or capability;
- no permit minting from desktop;
- no weakening/removal of security gate, audit or HIGH_ASSURANCE tests;
- no signing/notarization/store secret;
- no Linux/macOS success inferred from another OS;
- no release-ready claim from compile-only evidence.

## Promotion STOP
This ledger remains incomplete until Linux and macOS desktop-native exact-head evidence is green. `RELEASE_VALIDATED` remains false for all platforms in this increment.