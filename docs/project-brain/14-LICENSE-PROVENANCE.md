# License & Provenance — Hive Coder

Third-party foundations must be evaluated before source import or distribution.

## Approved foundation records

### Open Interpreter
- Repository: `openinterpreter/openinterpreter`.
- Release: `0.0.43`.
- Tag: `rust-v0.0.43`.
- Commit: `6e7c4bb78bb1c349b82f584f7e21a529ec39a74f`.
- License verified at exact commit: Apache-2.0.
- Windows x64 artifact SHA-256: `be317ff01c8730f9a3623cb2f807d80414923ddedf5e31a3012403a1f6ba67c5`.
- Integration classification: external dependency, not copied source.

### Cua Driver
- Repository: `trycua/cua`.
- Selected component: `libs/cua-driver/rust`.
- Release: `0.28.1`.
- Tag: `cua-driver-rs-v0.28.1`.
- Commit: `d8028a7943087ee258dc1b4d19dc12a7cd27669c`.
- License verified at exact commit: MIT in the component workspace manifest and repository `LICENSE.md`.
- Windows x64 artifact SHA-256: `ab90418aa2efb5a48d6eea1481fb99ae6a93e3fe93c829ee5340d5c50fb5cb1a`.
- Integration classification: external dependency, not copied source.

## Explicit exclusions
OmniParser and Ultralytics are not part of the approved first foundation set. Optional/transitive components require independent provenance/license review before inclusion.

## Rules
Preserve required copyright/NOTICE/attribution; record source URL/version/commit and license for imported code; distinguish dependency use from copied/modified source; do not copy proprietary visual assets; scan transitive/optional dependencies before release; unresolved or incompatible licensing blocks distribution. Foundation binaries are not vendored and automatic install/download remains disabled under HCODER-WO-0002.

No final Hive Coder project license is selected by this checkpoint. A later governed decision must choose it after product/distribution requirements are defined.
