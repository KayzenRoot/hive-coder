# HCODER-WO-0025 — Prebuilt Implementation Pack

**Status:** FROZEN EXECUTION CONTRACT — satisfaction of its obligations is external exact-head evidence
**Base:** `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Issue:** `#82`  
**Prior reviewed-head facts:** historical only; this document is not the review index. Mutable current review and gate state is external in the active PR and Issues #30 and #82.  
**Canonical authority history:** `.engineering/context-locks/HCODER-WO-0025.md` — the append-only delta sequence for this Work Order; no terminal delta number or range is mirrored here.

## Mission

Produce the first governed native package matrix so later distribution slices are completion-oriented: a deterministic CI lane per OS that generates bounded internal packages, validates them with runner-native tools, emits a deterministic inventory, and uploads only bounded evidence.

## Fixed contract identities

```text
PACKAGE_INVENTORY_SCHEMA = "hive-package-inventory-v1"
WORKFLOW_NAME            = "Native Package Matrix"
WORKFLOW_PATH            = ".github/workflows/native-package-matrix.yml"
INVENTORY_TOOL           = "tools/desktop/package_inventory.py"
CANONICAL_VERSION_SOURCE = "apps/desktop/src-tauri/tauri.conf.json"
PACKAGE_ROOT             = "apps/desktop/src-tauri/target/release/bundle"
```

## Pinned toolchain facts (verified from the repository, not assumed)

- `@tauri-apps/cli` is pinned to `2.11.4`.
- The CLI supports `build --no-bundle` (compile only) and a separate `bundle --bundles <targets>` subcommand that bundles an **already built** app.
- `--bundles` possible values are host-platform dependent; each lane must interrogate the CLI on its own runner and support the targets the CLI advertises there, or STOP.
- Explicit bundling does **not** require `bundle.active=true`: with the canonical config (`bundle.active=false`) `tauri bundle` proceeds on explicit request.
- `--config` accepts a JSON string or a path to a JSON/JSON5/TOML file merged over the default config; this is the ephemeral-overlay mechanism.
- `generate_icon.py` writes `icons/icon.ico` (single 64×64, 32-bit entry) and `icons/icon.png` (64×64, 8-bit RGBA). These are the only icon inputs the overlay may name.

## Canonical config preservation

Never edit `tauri.conf.json`. Never add a tracked `bundle.icon`. Never flip `bundle.active`. The overlay is runner-local, non-tracked, never committed, never uploaded, and each job proves tracked source is unchanged after bundling.

## Package matrix

| Lane | Runner | Targets | Notes |
|---|---|---|---|
| Windows | `windows-latest` | `msi`, `nsis` | MSI requires an icon declaration; NSIS may work without one. Neither installer is executed. |
| Linux | `ubuntu-latest` | `appimage`, `deb` | Preserve the existing GTK/rfd feature requirement (`rfd/gtk3`) used by the Linux desktop lane. |
| macOS | `macos-latest` | `app`, `dmg` | Icon format acceptance must be proven natively; a new tracked icon format is a STOP, not a fix. |

Build model per lane: `tauri build --no-bundle` (with the Linux feature set where applicable), then `tauri bundle --bundles <targets> --config <overlay>`.

## Ephemeral overlay contract

- Location: a runner-temporary path outside tracked source (for example `$RUNNER_TEMP`), created fresh per job.
- Content: only `{"bundle": {"icon": [...]}}` naming repository-existing generated icon inputs. No signing, key, release or updater fields.
- Every referenced icon path must be validated to exist **after** deterministic icon generation and before bundling.
- After bundling the job must prove `git status --porcelain` is clean and that `tauri.conf.json` is unchanged (content comparison, not just status).
- The overlay is never uploaded as a workflow artifact.

## Deterministic package inventory contract

`tools/desktop/package_inventory.py`, standard library only, schema `hive-package-inventory-v1`, closed key set per entry:

```text
schemaVersion, sourceSha, canonicalVersion, platform, architecture,
packageType, relativePath, byteSize, digestAlgorithm, digest, structuralValidation
```

Rules:
1. Discovery is bounded to an explicit package root passed by the caller; no repository-wide wildcards.
2. File packages hash exact bytes with SHA-256.
3. Directory bundles (macOS `.app`) use a documented deterministic **sorted-tree** digest over relative path, entry type, size and content digest — a directory is never represented as a plain file hash.
4. Reject: absolute paths, `..` traversal, symlink escape outside the root, duplicates, missing expected package type, unexpected extra package type, zero-size file package, wrong canonical version, wrong source SHA, artifact outside the bounded root.
5. Manifest ordering and JSON serialization are deterministic: shuffled discovery order must yield byte-identical output.
6. Exit codes: `0` valid, non-zero invalid; the CLI prints a machine-readable report and never mutates the package root.

## Native non-install structural checks

- **Windows MSI**: runner-native Windows Installer/PowerShell metadata access when available; verify product identity and version against the canonical version. Container magic alone is insufficient when metadata access exists. Never install.
- **Windows NSIS**: bounded path, non-zero size, PE/MZ structure. Never execute.
- **macOS `.app`**: `Contents/Info.plist` present; bundle identifier, product name and version verified; expected executable present. No codesign.
- **macOS `.dmg`**: `hdiutil verify`; no mount or install unless a structural check proves it necessary, in which case STOP first.
- **Linux `.deb`**: `dpkg-deb` metadata inspection for package and version identity. Never install.
- **Linux AppImage**: bounded path, non-zero size, executable bit, native magic/format proof. Never execute.

## Tests before promotion

Unit tests must cover: valid inventory generation per supported package type; missing, duplicate and unexpected package type; zero-size file package; wrong canonical version; wrong source SHA; absolute path, traversal and symlink escape; artifact-root isolation (a lookalike outside the root is never selected); one-byte hash mutation invalidating the expected digest; directory-tree mutation invalidating the `.app` tree digest; discovery-order shuffle producing identical manifest bytes; and an explicit assertion that digests are integrity evidence, not signing or publisher authenticity.

## Evidence required

Per lane: exact source SHA, runner OS and architecture, pinned CLI version, advertised bundle targets, whether the overlay was needed, generated package paths, inventory identity and artifact upload name — all posted externally to the PR and Issue #82, never committed into repository documents.

## STOP conditions

Tracked `tauri.conf.json`/icon-format/product-artifact mutation; a new dependency or plugin; signing/notarization/release credentials; installer execution; a reduced approved matrix; non-deterministic or unbounded artifact discovery; a weakened existing gate; or any step that would merge the PR, claim production distributability, or begin `HCODER-DIST-001C`.
