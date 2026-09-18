# HCODER-WO-0025 — Acceptance & Security Map

**Status:** PROPERTY CONTRACT — every row is an executable obligation, not an execution status  
**Issue:** `#82`  
**Canonical authority history:** `.engineering/context-locks/HCODER-WO-0025.md`

Required negative proofs are the point of this slice. A row is satisfied only by a test or gate that fails when the guard is removed.

## How to read this map

The **Implementation** column is a durable statement about the repository, not about any CI run or review outcome:

- `REQUIRED` — the property is an obligation of this slice; it is satisfied in source by the named test or gate and is enforced whenever that lane runs.
- `EXTERNAL PROOF` — the property can only be demonstrated by hosted exact-head evidence: the lanes must actually run and produce, or refuse, their declared targets on a named head.

**External promotion evidence is required for every row and is deliberately not encoded per row.** Hosted exact-head Governance, Desktop Shell and Native Package Matrix green, plus an independent review with unresolved HIGH/CRITICAL `0/0`, must each be produced against whichever exact head a promotion decision names. That mutable state lives in the active PR and Issues #30 and #82; this map records the property and its evidence path, never a current PASS claim.

## Package matrix and canary law

| # | Property the law must enforce | Test location | Implementation |
|---|---|---|---|
| A1 | Windows lane produces `msi` and `nsis`, or STOPs with exact native evidence instead of reducing the matrix | `native-package-matrix.yml` (windows job) | EXTERNAL |
| A2 | Linux lane produces `appimage` and `deb` with the existing GTK/rfd feature set | `native-package-matrix.yml` (linux job) | EXTERNAL |
| A3 | macOS lane produces `app` and `dmg`, or STOPs if a new tracked icon format would be required | `native-package-matrix.yml` (macos job) | EXTERNAL |
| A4 | Every lane checks out and prints the exact head SHA with equality verification before package work | `native-package-matrix.yml` | EXTERNAL |
| A5 | No installer is ever executed to satisfy acceptance | `native-package-matrix.yml` (no execution step exists) | EXTERNAL |

## Canonical config preservation

| # | Property the law must enforce | Test location | Implementation |
|---|---|---|---|
| B1 | `tauri.conf.json` is unchanged after overlay creation and bundling (content comparison) | `native-package-matrix.yml` (guard step) | EXTERNAL |
| B2 | `bundle.active` remains `false` and no tracked `bundle.icon` is added | existing `tools/desktop/security_gate.py` + `version_drift.py`; `native-package-matrix.yml` | EXTERNAL |
| B3 | The overlay is runner-local, non-tracked, never committed and never uploaded as an artifact | `native-package-matrix.yml` (overlay path and upload list) | EXTERNAL |
| B4 | The overlay may name only repository-existing generated icon inputs, validated after icon generation | `native-package-matrix.yml` (existence checks) | EXTERNAL |

## Deterministic inventory contract

| # | Property the law must enforce | Test location | Implementation |
|---|---|---|---|
| C1 | Schema is closed and deterministic: `hive-package-inventory-v1` with exact key set | `tests/desktop/test_package_inventory.py` | REQUIRED |
| C2 | File packages hash exact bytes with SHA-256; directory bundles use a documented sorted-tree digest | `test_package_inventory.py` | REQUIRED |
| C3 | Absolute path, `..` traversal and symlink escape are rejected | `test_package_inventory.py` | REQUIRED |
| C4 | Missing, duplicate and unexpected package types are rejected | `test_package_inventory.py` | REQUIRED |
| C5 | Zero-size file package, wrong canonical version and wrong source SHA are rejected | `test_package_inventory.py` | REQUIRED |
| C6 | Artifact outside the bounded root is never discovered, including lookalikes | `test_package_inventory.py` | REQUIRED |
| C7 | One-byte hash mutation invalidates the expected digest | `test_package_inventory.py` | REQUIRED |
| C8 | Directory-tree mutation invalidates the `.app` tree digest | `test_package_inventory.py` | REQUIRED |
| C9 | Shuffled discovery order yields byte-identical manifest output | `test_package_inventory.py` | REQUIRED |
| C10 | Documentation and tests state that SHA-256 is integrity evidence, not signing or publisher authenticity | `test_package_inventory.py` | REQUIRED |

## Security invariants this slice must not weaken

The existing `tools/desktop/security_gate.py` assertions — zero frontend invokes beyond the three governed commands, zero capability permissions, `desktop-read-only` scope, zero filesystem mutation primitives, zero generic process execution, one fixed runtime sidecar process, zero Apple-specific font references, committed lockfiles — must remain unchanged and passing, as must `tools/desktop/version_drift.py` reporting `LOCKED`, the full Python and desktop suites, and the Rust lanes.

`bundle.active` remains `false`; no signing, notarization, release, tag or updater authority is added; no dependency, manifest or lockfile changes; no `HCODER-DIST-001C` work.

## STOP
Any row that cannot be satisfied without a tracked config or icon-format change, a new dependency, signing/release authority, installer execution or a reduced matrix is a STOP condition, not an implementation task. `IMPLEMENTED` is not a promotion claim.
