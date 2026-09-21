# Deployment — Hive Coder

Initial deployment target is a user-installed desktop application, Windows-first during early validation while preserving cross-platform architecture where foundations support it.

Packaging is no longer merely planned: it is proven as **evidence** under `HCODER-CP-0025` (see below). Signing, notarization, updater, crash telemetry, rollback and release-channel execution remain outside the approved state, and no production release is complete without reproducible build/package evidence plus a tested rollback/roll-forward path.

## Current release-trust status

This section states what the source hierarchy actually proves, so that packaging progress is not misread as either nothing-happened or a shippable release. `docs/project-brain/11-CHECKPOINT.md` and the Decision ledger remain authoritative over this summary.

- **Proven (CANONICAL / `HCODER-CP-0025`, `DEC-029`):** the declared six native package targets build deterministically under CI — Windows `msi`+`nsis`, macOS `app`+`dmg`, Linux `appimage`+`deb` — each lane failing closed rather than shipping a smaller set, with every artifact bound to a closed `hive-package-inventory-v1` manifest. A recorded digest proves byte identity and integrity for evidence transport only.
- **Proven (CANONICAL / `HCODER-CP-0024`, `DEC-028`):** the canonical version and release-channel contract that a release identity must satisfy.
- **Reviewed promotion candidate, not canonical on `main` (`HCODER-WO-0026`, `DEC-030`):** the `hive-release-provenance-v1` contract, its offline fail-closed validator, and a protected-release workflow whose credential-bearing stages exist as provable structure rather than as YAML intent. The implementation was independently reviewed at `0a1b8375e5c950d321f898b6d455eb874583c9a4` and its checkpoint delta is PROPOSED / REVIEW PENDING, so the substrate exists only in an unmerged Draft PR; canonical force needs `HCODER_CP_0026_EFFECTIVE`, which nothing here asserts.
- **Not admitted at any status:** publisher signing, notarization, stapling, release/tag creation, GitHub Release publication, updater transport, artifact download, install, restart or rollback execution. Packages built today are deliberately unsigned; that is not a security success and those packages are not distributable.

No deployment target is reachable from this repository's current state without external provisioning: a publisher-signing identity per platform, Apple Developer notarization credentials, and release environments whose protection rules are enforced and cannot be bypassed by administrators. Until each exists and is proved by the environment-protection probe rather than asserted, the release path stays closed.

## WO-0015 desktop build state — promotion candidate
The first Windows-native desktop substrate is now technically buildable under CI:
- Tauri 2 + React/TypeScript/Vite under `apps/desktop/`;
- committed npm/Cargo lockfiles;
- deterministic Hive desktop icon generation before Tauri build;
- pinned Node/Rust toolchains in desktop CI;
- Windows release build produces `hive-coder-desktop.exe`;
- bounded native launch smoke passes on Windows Server 2025.

This is **not** a production distribution claim. `bundle.active=false` in WO-0015, so installer creation, code signing, update channels, package integrity/attestation, production secrets, crash telemetry, uninstall behavior and tested rollback/roll-forward remain outside the checkpoint. A later deployment/release Work Order must prove those items before Hive Coder is declared releasable.

Dependency release readiness also remains gated by license/provenance review and by explicit treatment of the recorded RustSec warning-class transitive advisories.
