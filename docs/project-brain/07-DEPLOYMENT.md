# Deployment — Hive Coder

Initial deployment target is a user-installed desktop application, Windows-first during early validation while preserving cross-platform architecture where foundations support it.

Packaging, signing, updater, crash telemetry, rollback and release channels remain `PLANNED` until stack selection is finalized. No production release is complete without reproducible build/package evidence and a tested rollback/roll-forward path.

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
