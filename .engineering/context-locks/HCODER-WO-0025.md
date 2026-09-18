# HCODER-WO-0025 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** `#82`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001B` — native package matrix  
**Canonical base:** `HCODER-CP-0024` / `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Authority delta:** internal, unsigned native package **evidence generation only** — no signing, release, updater, install or distribution authority

> **Historical scope of the delta record.** This file is the canonical **append-only** authority and delta history for this Work Order. Every delta records what was authorised, required or true **at its own stage**; any phase, PR, review, gate or merge wording inside a delta describes that stage and is not a current-state field. Current mutable state — latest review and gate receipts, the active PR's state, and whether a promotion predicate is satisfied — lives externally in the active PR and Issues #30 and #82. Only the deltas' *law* (allowed files, prohibitions, predicates) carries forward.

## Source check

- Canonical predecessor `HCODER-CP-0024` / `DEC-028` is **CANONICAL / SEALED** on `3e1e1af7596c56716825206587bf2a88e1b179d0`; no successor slice has modified that law.
- `apps/desktop/src-tauri/tauri.conf.json` declares `version="0.1.0"`, `bundle = {"active": false}` and **no** `icon` key.
- `tools/desktop/generate_icon.py` deterministically writes `apps/desktop/src-tauri/icons/icon.ico` (single 64×64, 32-bit entry) and `icon.png` (64×64, 8-bit RGBA).
- `apps/desktop/package.json` pins `@tauri-apps/cli` to `2.11.4`; the installed CLI matches.
- Pinned CLI supports the split-build model: `tauri build --no-bundle` compiles, `tauri bundle --bundles <targets>` bundles an already-built app. `--bundles` possible values are host-platform dependent.
- Explicit bundling does **not** require `bundle.active=true`: `tauri bundle` with `bundle.active=false` produced a Windows NSIS package with no config change.
- Every existing desktop lane builds with `tauri build --no-bundle`, which never invokes the bundler — which is why the absent `bundle.icon` has never been observable in CI.
- The repository currently has **no** `actions/upload-artifact` usage and no release/tag automation.

## Selected first slice

A deterministic native package matrix for Windows, Linux and macOS that produces **bounded internal package artifacts**, validates their structure with runner-native tools, emits a deterministic inventory/hash manifest, and uploads only bounded CI evidence with short retention.

Package targets: Windows `msi` + `nsis`; macOS `app` + `dmg`; Linux `appimage` + `deb`.

Explicitly outside this slice: signing, codesign, notarization, stapling, publisher-authenticity claims, release/tag creation, GitHub Release upload, updater artifacts, update endpoints, product network fetch, download/install/restart or rollback behaviour, channel promotion, and any production-distributable claim.

## Canonical config preservation law

1. `apps/desktop/src-tauri/tauri.conf.json` is **not** edited by this Work Order. No tracked `bundle.icon`, no `bundle.active` change, no version bump, no updater or package-endpoint settings.
2. The only new bundle configuration authorised is an **ephemeral, runner-local, non-tracked overlay** supplied to the pinned CLI's explicit bundle command.
3. The overlay may contain only bundle fields strictly required to declare the **already-generated deterministic icon inputs** — and, if the pinned CLI proves it necessary, package-target-local metadata already derivable from canonical source. No signing, private-key, release or updater fields.
4. The overlay must live outside tracked source or in a guaranteed ignored/temporary runner path. It must never be committed, never uploaded as an artifact, and each job must prove tracked source is unchanged after overlay creation and use.
5. An ephemeral overlay is not canonical product config and must never be represented as a new product authority surface.

## Security law

1. Default deny; this slice adds no product runtime authority, capability, permission or IPC surface.
2. No signing certificate, notarization credential, signing key, updater key, release token or protected secret may be read, requested, printed, persisted or uploaded.
3. No package signing, codesign, notarization, stapling, publisher-authenticity claim or production-distributable claim.
4. No tag or release creation and no GitHub Release asset upload. Workflow artifacts are CI evidence only, with short explicit retention.
5. No updater plugin, update endpoint, product network fetch, artifact download/install/restart path, channel-promotion execution or rollback behaviour.
6. No new product/runtime dependency, plugin or capability. If one appears necessary, STOP for review instead of adding it.
7. Package SHA-256 proves **byte identity/integrity for evidence transport**. It is not signing and does not establish publisher authenticity; documentation and tests must say so explicitly.
8. Unsigned/unnotarized package state is expected in this slice and must never be presented as a security success.
9. Installers are never executed to satisfy acceptance. A target that can only pass by executing an installer is a STOP condition.
10. Artifact discovery is always bounded to an explicit package root and made deterministic; stale outputs cannot satisfy acceptance.

## Allowed-file set

This Work Order may change only:
- `.engineering/work-orders/HCODER-WO-0025.md`
- `.engineering/context-locks/HCODER-WO-0025.md`
- `.engineering/evidence/HCODER-WO-0025.md`
- `.engineering/prebuilt/HCODER-WO-0025-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0025-EXECUTOR-BRIEF.md`
- `.engineering/prebuilt/HCODER-WO-0025-ACCEPTANCE-SECURITY-MAP.md`
- `.github/workflows/native-package-matrix.yml`
- `tools/desktop/package_inventory.py`
- `tests/desktop/test_package_inventory.py`
- `docs/project-brain/adrs/DEC-029-NATIVE-PACKAGE-MATRIX-EVIDENCE-CONTRACT.md` and the matching `docs/project-brain/10-DECISIONS-LEDGER.md` entry, if the proposal is retained

## Forbidden files

`apps/desktop/src-tauri/tauri.conf.json`; `apps/desktop/package.json` and `apps/desktop/package-lock.json`; `apps/desktop/src-tauri/Cargo.toml` and `Cargo.lock`; every TypeScript/Python/Rust product source or test file outside the list above; `.github/workflows/governance.yml` and `.github/workflows/desktop-shell.yml`; runtime, control-plane, permission and capability code; release and packaging configuration; any dependency or lockfile change.

## STOP CONDITION

STOP and return to architecture/review if the slice would require a tracked `tauri.conf.json` change, a new tracked icon format, a product-artifact config mutation, a product dependency or plugin, a reduced approved matrix, installer execution, signing/notarization/release credentials, production release authority, a weakened or skipped existing Governance/Desktop/HIGH_ASSURANCE gate, or any filesystem/Git/shell/Cua/credential authority expansion.

---

# Context Lock Delta 001

**Status:** PREBUILT IMPLEMENTATION AUTHORISED — same Work Order  
**Authority granted:** exactly the allowed-file set above, and nothing else  
**Trigger:** Prompt 34 bounded continuation decision on Issue #82 (`5721331226`), authorising Option C — runner-local, non-tracked ephemeral bundle icon overlay through the pinned Tauri CLI config mechanism

## Recorded preflight history (immutable)

Prompt 33 stopped before implementation on Issue #82 (`5721095900`) because the Windows `msi` target could not be produced from the canonical configuration: `bundle` declared only `active: false` with no `icon` array, so WiX failed with `Couldn't find a .ico icon`. No branch, commit or PR existed — this was a preflight STOP, not a failed implementation. The independent review `5721331226` confirmed the STOP as valid and authorised a bounded ephemeral-overlay continuation rather than a canonical-config change. `DEC-028` / `HCODER-CP-0024` law and the canonical config are preserved unchanged by this delta.

## Additional law for the ephemeral overlay

1. The overlay is passed to the pinned CLI only through its `--config` mechanism, as a runner-temporary file where the CLI accepts a file path, otherwise as a correctly escaped inline JSON value; the mechanism actually used must be demonstrated per runner.
2. The overlay names only repository-existing generated icon inputs, and each referenced path must be validated to exist **after** deterministic icon generation.
3. After bundling, each job must prove `git status --porcelain` shows no unexpected tracked change, and must specifically prove `tauri.conf.json` content is unchanged.
4. Canary-first: no full-matrix claim may be made until the Windows, macOS and Linux lanes each prove their targets natively. If any lane requires a tracked config, icon-format or product-artifact change, STOP with the exact native evidence before making that change.

## STOP CONDITION (Delta 001)
In addition to the pre-existing STOP condition: STOP if any native lane requires a tracked `tauri.conf.json` or icon-format mutation, if any target can only work by reducing the approved matrix, if artifact discovery cannot be made root-bounded and deterministic, or if any step would merge the Draft PR, call Hive Coder production-distributable, or begin `HCODER-DIST-001C`.

---

# Context Lock Delta 002

**Status:** HIVE PROVIDER ONLINE — BOUNDED CORRECTION AUTHORISED (same Work Order)  
**Authority granted:** exactly the four corrections below, within the existing allowed-file set; no new product/runtime/update/package/network/install/signing/release/filesystem/Git/shell/Cua/credential authority and no successor-slice authority  
**Trigger:** independent HEDS review `5248101122`, verdict `CORRECTION_REQUIRED`, CRITICAL `0` / HIGH `2` / MEDIUM `2`, on exact head `c2bf8605f64c1584e00def7f06ba6d3d5176c7ed`

## Recorded pre-execution STOP history (immutable)

- **Prompt 35** stopped before execution: HIVE was healthy but registered zero projects, no repository mutation occurred, and no correction commit existed.
- **Prompt 36** stopped as `HIVE_PROJECT_BOOTSTRAP_BLOCKED`: the running `hive-api-1` container mounted only `D:/HIVE/data` and `D:/HIVE/projects` (read-only), so the active checkout at `D:/Projeto Codexx/hive-coder` was not visible and no legal registration could become context-capable.
- **Prompt 37 unblock** (`5730739379`) authorised one bounded host-side HIVE mount reconfiguration.

## Host bootstrap performed (recorded, verified)

The effective bind source was **not** the `.env` file: `HIVE_PROJECTS_ROOT` was set as a Windows user environment variable, which overrides `.env` in Compose, so the mount did not change until that variable was corrected. Both were brought into agreement on `D:/Projeto Codexx`; `.env` was backed up as `.env.<timestamp>.pre-hive-coder.bak` before the byte-precise edit (newline style preserved). HIVE was restarted only through the documented launchers (`hive-down.cmd` uses `docker compose stop`, never deleting volumes, then `hive-up.cmd`); all services returned healthy. The container now mounts `D:/Projeto Codexx → /workspace/projects` read-only, proven both by `docker inspect` (`rw=false`) and independently by `ro` in the container's `/proc/mounts`. Container checkout identity was proven by SHA-256 equality of `apps/desktop/src-tauri/tauri.conf.json` and `tools/desktop/version_drift.py` between host and container.

HIVE project `hive-coder` (`bec146b3-7ac9-404a-bb79-17ea8dbda7e5`, `relative_path=hive-coder`) registered through the documented `POST /api/v1/projects`, refreshed through the documented `POST /inspect` (state `READY`, `repository_accessible: true`, `git_head_sha` exactly `c2bf8605…`), indexed through the documented `POST /index` (400 files, 2021 symbols at that head), and made retrievable through the documented `POST /retrieval/corpus/sync` (2421 sources, 3018 chunks). Capsule fingerprints were cross-checked against the working tree and match exactly.

**Recorded environmental note.** HIVE's git inspection caps each git call at 5 seconds; the first cold inspection exceeded that and was reported as `git_timeout`, while a warm re-inspection succeeded. Separately, the container's git reports 360 files as modified because this Windows checkout materialises CRLF while the index holds LF and only the host's `core.autocrlf=true` hides the difference, so `working_tree_clean` is `false` in HIVE while the host tree is clean. Neither condition affects indexing (which reads the git index) and neither is repaired by this Work Order.

## Authorised correction scope (exactly these four)

| Finding | Defect | Required correction |
|---|---|---|
| `H-34-01` | `validate_manifest()` compared only environment fields and a dictionary of `(type, path) → digest`, so duplicates collapsed, ordering and several entry fields were unverified, and schema/closed-key compliance was not enforced. | Accept recorded evidence only if it exactly matches the recomputed canonical closed inventory: exact top-level closed keys and `schemaVersion`, `packages` a list of closed entry dictionaries with exact keys, duplicate `(packageType, relativePath)` rejected before comparison, and every evidence-significant field plus package count and order compared. Prefer canonical-serialization equality. |
| `H-34-02` | `tree_digest()` recorded symlink targets without validating containment, so a link inside a `.app` could point outside the bundle. | Validate every symlink's containment before writing its record: reject absolute external targets and relative targets that normalize outside the bundle root; preserve valid internal relative links and keep hashing the link-target string. |
| `M-34-03` | The workflow hardcoded `CANONICAL_VERSION: "0.1.0"` and the macOS lane hardcoded the identifier, creating duplicate version/config sources. | Remove the workflow constant and never replace it with another tracked mirror; run the existing `tools/desktop/version_drift.py` in every native lane and require `VERSION_DRIFT=LOCKED`; derive the canonical version and the bundle identifier at runtime from `apps/desktop/src-tauri/tauri.conf.json`; export them only as per-job observations and log the canonical source path. |
| `M-34-04` | The `pull_request` path filter did not include the WO-0025 governance/decision paths, so a docs-only correction head could not receive package evidence. | Make the trigger durable for every legal same-Work-Order correction: include the complete authorised WO-0025 path set, or remove the PR path filter when completeness cannot be guaranteed; keep `push`/`main` behaviour unchanged; no artificial technical touch may be required. |

A bounded retry (maximum two attempts, short deterministic delay, fail-closed) may wrap the explicit bundle command to absorb the previously observed transient WiX download failure.

## Preserved unchanged

Accepted Prompt-34 native matrix behaviour (Windows `msi`+`nsis`, macOS `app`+`dmg`, Linux `appimage`+`deb`); canonical `tauri.conf.json` byte-unchanged with `bundle.active=false` and no tracked `bundle.icon`; runner-local non-tracked ephemeral overlay, never uploaded; no manifest/lockfile/dependency/plugin/runtime/permission/capability change; no signing, notarization, release or tag publication, updater network/download/install/restart, installer execution or production-distributable claim; no `HCODER-DIST-001C`.

## HIVE-FIRST law (execution optimization only)

HIVE is the primary project-context, retrieval and delta-memory layer for this Work Order: its project checkpoint, bounded context capsule, hybrid/lexical retrieval, impact set and required proofs are consulted before broad repository reads, and progressive disclosure widens reads only when HIVE returns UNKNOWN or insufficient evidence. **HIVE grants no product or runtime authority, is not elevated above Git, and never outranks Git, code, tests, approved decisions or hosted exact-head evidence.** Where HIVE and verified source conflict, the source wins and HIVE context is refreshed. No secrets, credentials, workflow artifacts or mutable CI run state are stored in HIVE as canonical project memory. Deltas `001` and the Prompt 33/35/36 history are preserved.

## STOP CONDITION (Delta 002)
STOP if a correction requires a tracked `tauri.conf.json` or icon-format change, a new dependency/plugin/runtime authority, a reduced package matrix, installer execution, or signing/notarization/release/updater/install/restart/secret authority; if fresh exact-head Governance, Desktop Shell or Native Package Matrix is not fully green; if any HIGH/CRITICAL finding remains unresolved; or if any step would merge PR #83 or begin `HCODER-DIST-001C`.


---

# Context Lock Delta 003

**Status:** DOCUMENTATION/SOURCE-TRUTH RECONCILIATION ONLY — no technical authority  
**Authority granted:** correction of durable governance wording in the paths listed below, and nothing else  
**Trigger:** independent HEDS review `5249173061`, verdict `CORRECTION_REQUIRED`, CRITICAL `0` / HIGH `0` / MEDIUM `1`, on exact head `20a63350fb685953893ae03b57fc26d22e460f10`

## Recorded finding (as returned by the independent review)

The review **accepted and closed** the technical work: the HIVE bootstrap blocker is resolved and the project fingerprint matches the candidate head; `H-34-01` (closed-schema manifest verification with duplicate rejection before comparison and exact canonical-document equality), `H-34-02` (internal bundle symlinks failing closed on absolute or normalized escape targets), `M-34-03` (no stored version/identifier mirror; every lane gates on `VERSION_DRIFT=LOCKED` and derives both from the canonical Tauri config) and `M-34-04` (unfiltered `pull_request` trigger) are all closed. Exact-head `Governance`, `Desktop Shell` and `Native Package Matrix` evidence was green, all six package targets were produced, and `TRACKED_SOURCE_UNCHANGED` passed.

- **M-37-01 — durable governance artifacts still described the Work Order as pre-implementation.** The Work Order carried a live `PREBUILT / IMPLEMENTATION PENDING` status; the Evidence Bundle said packages were not produced or validated yet and that the inventory/validator and workflow were not yet implemented; the Acceptance/Security Map kept executable obligations as a live `PENDING` execution state; the Implementation Pack and Executor Brief carried pre-execution status wording; `DEC-029` stated as present tense that no gate had ever exercised the bundler, which is only true historically before this Work Order; and the Decisions Ledger expressed satisfaction as a phase claim rather than as delegated external state. These are not technical defects, and the review explicitly required that they must **not** be "fixed" by embedding current SHA, run or review identifiers.

## Authorised correction

Convert current-state scaffolding into durable source law. Repository artifacts state what is materialized in source and which properties and evidence are required, while mutable review, gate, merge and promotion satisfaction stays external in PR #83 and Issues #30 and #82. Historical pre-Work-Order facts are labelled explicitly historical. `DEC-029` is not promoted by this delta.

Allowed paths, exactly: this Context Lock; `.engineering/work-orders/HCODER-WO-0025.md`; `.engineering/evidence/HCODER-WO-0025.md`; `.engineering/prebuilt/HCODER-WO-0025-ACCEPTANCE-SECURITY-MAP.md`; the Implementation Pack and Executor Brief only where stale live execution wording is present; `docs/project-brain/adrs/DEC-029-NATIVE-PACKAGE-MATRIX-EVIDENCE-CONTRACT.md`; and the `DEC-029` entry in `docs/project-brain/10-DECISIONS-LEDGER.md`.

**Forbidden:** `.github/workflows/native-package-matrix.yml`; `tools/desktop/package_inventory.py`; `tests/desktop/test_package_inventory.py`; every product or runtime source; `tauri.conf.json`; manifests and lockfiles; dependencies; the Governance and Desktop workflows; and any authority surface.

**Preserved:** the acceptance properties themselves are unchanged — closed-schema verification, root-bounded discovery, mutation proofs, the native target matrix, the tracked-source guard and every authority exclusion remain exactly as reviewed. Prompt 33/35/36/37 history, including the preflight and bootstrap STOPs, is preserved as historical record and is not rewritten.

## Anti-self-staling test applied

Both thought experiments must hold simultaneously: if this exact correction later merges without another byte changing, every durable statement remains true; and before merge, no source statement falsely claims that `DEC-029` is canonical or that the Work Order is complete. Mutable receipts — head SHAs, run IDs, review IDs and merge state — remain external and are never embedded here.

## STOP CONDITION (Delta 003)
STOP if any wording correction would require a technical, workflow, tool, test, Tauri-config, manifest, lockfile, dependency or authority change; if it would canonicalise `DEC-029` before governed promotion; if a durable source would still self-stale merely because review, gate or merge phase advances; if fresh exact-head gates are not fully green; or if any step would mark PR #83 Ready, merge it, or begin `HCODER-DIST-001C`.

## Delta 004 — closeout source-truth correction (M-39-01)

**Trigger:** independent closeout HEDS review `5250120095`, verdict `CORRECTION_REQUIRED`, CRITICAL `0` / HIGH `0` / MEDIUM `1`, on exact reviewed closeout head `8d7ad5e2dfc285116d86e992d830e4fa76864f06`. The closeout base is `676138df041c4147df7a5fe3a42b481c0f5e7f13`.

**Accepted by that review and preserved by this delta:** the product implementation and the six-target package matrix; the `HCODER_CP_0025_EFFECTIVE` predicate design itself — independent HIGH/CRITICAL `0/0` review of one closeout revision, expected-head governed merge of that same revision, and fresh exact-main Governance, Desktop Shell and Native Package Matrix; CP-0025/DEC-029 admitted authority and exclusions; and the documentation-only character of the closeout revision. `DEC-029` holds no canonical force while the predicate is unsatisfied, and `HCODER-CP-0024` remains authoritative while the CP-0025 predicate is unsatisfied and the CP-0024 predicate is satisfied.

## Recorded finding (as returned by the independent review)

- **M-39-01 — residual self-staling lifecycle pointers remain in the closeout source.** The conditional-effectiveness design was accepted, but several durable files still carried phase-relative wording. Three specific defects: `.engineering/evidence/HCODER-WO-0025.md` ended with a terminal `Do not merge` command, which the already-merged product stage and any future governed closeout merge contradict; multiple closeout files located mutable evidence in `the active closeout PR`, a pointer that ceases to exist once a closeout merges; and the no-byte-change thought experiment had to be applied consistently to all seven closeout files. The review recorded this as documentation/source-truth only, rejected no technical law, package-matrix fact, exact-head evidence or authority boundary, and required that the correction must **not** be made by embedding current SHA, run or review identifiers.

## Authorised correction

Replace phase-relative commands and moving pointers with durable predicate, evidence and authority law, so that one and the same repository text is true before the closeout merge, after it, and after exact-main postvalidation. Specifically: the terminal command in the Evidence Bundle becomes a durable rule that `UNKNOWN` never becomes `PASS`, that canonical standing is determined only by `HCODER_CP_0025_EFFECTIVE`, and that no production-distributable claim and no `HCODER-DIST-001C` transition is admitted unless separately governed; and every `the active closeout PR` pointer is replaced with external lifecycle evidence referenced by Issues #30 and #82, naming a PR only by immutable identity or by role without depending on its open, active, draft, unmerged or current state. No phase command of any other form is introduced in its place.

Allowed paths, exactly: this Context Lock; `.engineering/evidence/HCODER-WO-0025.md`; `.engineering/work-orders/HCODER-WO-0025.md`; `.engineering/checkpoint-deltas/HCODER-WO-0025.md`; `.engineering/evidence/HCODER-CP-0025-CANONICAL-CLOSEOUT.md`; `docs/project-brain/11-CHECKPOINT.md`; the `DEC-029` ADR; and the `DEC-029` entry in `docs/project-brain/10-DECISIONS-LEDGER.md`, together with the `DEC-028` ledger entry only for the same moving-pointer wording — the whole ledger file is already in the closeout revision. Files outside this set are changed only where they actually contain M-39-01 wording.

**Forbidden:** `.github/workflows/native-package-matrix.yml`; `tools/desktop/package_inventory.py`; `tests/desktop/test_package_inventory.py`; every product or runtime source; `tauri.conf.json`; manifests and lockfiles; dependencies; the Governance and Desktop workflows; the product version; and any authority surface.

**Preserved:** the three-condition `HCODER_CP_0025_EFFECTIVE` predicate; the package matrix (Windows `msi`+`nsis`, macOS `app`+`dmg`, Linux `appimage`+`deb`); the split-build, ephemeral-overlay, closed-inventory, tree-digest, structural-validation and evidence-is-not-trust law; every product-stage immutable fact and every product merge/postvalidation receipt; `bundle.active` as `false` with no tracked `bundle.icon`; and every authority exclusion. Prompt 33/35/36/37 preflight and bootstrap STOPs and the Prompt 39 closeout findings remain historical record and are not rewritten.

## Anti-self-staling test applied

Both thought experiments must hold simultaneously. First: if these exact corrected bytes are governed-merged unchanged and the exact-main gates satisfy the predicate, every durable statement remains true with no follow-up status-flip commit. Second: before merge, no durable statement falsely claims that `HCODER_CP_0025_EFFECTIVE` already holds or that `DEC-029` already carries canonical force. Mutable receipts — head SHAs, run IDs, review IDs and merge state — remain external and are never embedded here.

## STOP CONDITION (Delta 004)
STOP if any correction would require a technical, workflow, tool, test, Tauri-config, manifest, lockfile, dependency, runtime or authority change; if it would alter the accepted predicate or the package contract rather than only source-truth wording; if any durable closeout file would still become false solely because review, merge or postvalidation state advances; if any HIGH/CRITICAL finding arises or fresh exact-head gates are not fully green; or if any step would mark the closeout PR Ready, merge it, close Issue #82 as complete, or begin `HCODER-DIST-001C`.

## Delta 005 — Context Lock pointer supersession (M-40-01)

**Trigger:** independent closeout HEDS review `5250270929`, verdict `CORRECTION_REQUIRED`, CRITICAL `0` / HIGH `0` / MEDIUM `1`, on exact reviewed head `7c48100067d31c6ea34f07c8365ea26c99d1604a`. The closeout base is `676138df041c4147df7a5fe3a42b481c0f5e7f13`.

**Accepted by that review and preserved by this delta:** M-39-01 is closed across the seven closeout files; `HCODER_CP_0025_EFFECTIVE` is unchanged and remains accepted; the Prompt 40 delta was documentation/governance-only with no technical, workflow, tool, test, Tauri-config, manifest, lockfile or dependency byte changed; fresh exact-head Governance, Desktop Shell and Native Package Matrix evidence was green with every Governance, Desktop and package job passing; product and package authority boundaries are unchanged; and `HCODER-DIST-001C` is not started. `DEC-029` carries no canonical force while the predicate is unsatisfied, and `HCODER-CP-0024` remains authoritative while the CP-0025 predicate is unsatisfied and the CP-0024 predicate is satisfied.

## Recorded finding (as returned by the independent review)

- **M-40-01 — one residual moving-pointer sentence remained in the append-only Context Lock preamble.** The preamble's standing interpretation clause still located current mutable state, including the state of the PR then carrying the work, in that PR and Issues #30/#82. That is the same lifecycle-pointer pattern Delta 004 removed from the closeout files: once a closeout merges there is no such active PR, so the sentence ceases to be literally durable. The review required the smallest lawful **append-only** supersession rather than a rewrite, and rejected no technical law, package-matrix fact, exact-head evidence or authority boundary.

## Authorised correction

Supersede the preamble's pointer semantics **prospectively**, without rewriting the historical record. The preamble's clause locating current mutable state in the PR then carrying the work is hereby **historical and superseded for interpretation**: from Delta 005 onward it must not be read as a live pointer, and it is preserved only as a description of the stage at which it was written. More generally, every PR, review, gate, approval or merge reference inside Deltas 001–004 — including Delta 001's STOP-condition wording that names a Draft PR, and including the passages in Deltas 003 and 004 that quote lifecycle-pointer wording while recording or correcting it — is a historical stage record by the standing rule at the head of this file, is superseded for pointer interpretation by this delta, and is not a current-state field.

**Durable replacement law.** Mutable lifecycle evidence is **external evidence referenced by Issues #30 and #82 and by the PR carrying the evaluated revision**, independent of whether that PR is open, draft, merged, closed or otherwise inactive. A PR is named only by immutable identity or by role.

**No moving pointer is canonical repository state.** No PR state, no latest-review pointer, no current-head pointer and no moving-main pointer is canonical repository state. Every delta in this file records what was authorised, required or true at its own stage; only each delta's *law* — allowed files, prohibitions, predicates — carries forward, and this delta's law is the paragraph above.

Change set, exactly: this Context Lock. No other repository file is changed by Delta 005, because the source check found no independent contradiction caused by M-40-01 outside it — the seven closeout files were already corrected under Delta 004 and retain that correction and the three-condition predicate unchanged.

**Forbidden:** `.github/workflows/native-package-matrix.yml`; `tools/desktop/package_inventory.py`; `tests/desktop/test_package_inventory.py`; every product or runtime source; `tauri.conf.json`; manifests and lockfiles; dependencies; the Governance and Desktop workflows; and any permission, capability or authority surface.

**Preserved:** the `HCODER_CP_0025_EFFECTIVE` predicate; the package matrix (Windows `msi`+`nsis`, macOS `app`+`dmg`, Linux `appimage`+`deb`); the split-build, ephemeral-overlay, closed-inventory, tree-digest, structural-validation and evidence-is-not-trust law; every product-stage immutable fact and postvalidation receipt; and every authority exclusion. Deltas 001–004 are preserved byte-for-byte, are not renumbered or collapsed, and no terminal delta range is created in another file. No signing, notarization, release, updater, install, restart, rollback or production-distributable authority is admitted by this delta.

## Anti-self-staling test applied

Three thought experiments must hold simultaneously. First: if this exact Context Lock byte sequence merges unchanged, every current law statement remains true — the historical deltas remain true as stage records, and the preamble's pointer clause is superseded by this delta rather than relied upon. Second: after exact-main postvalidation satisfies `HCODER_CP_0025_EFFECTIVE`, no current law statement becomes false merely because the closeout PR is merged or closed, because none of them depends on its state. Third: before merge, nothing in this delta claims the predicate already holds or that `DEC-029` already carries canonical force. Mutable receipts — head SHAs, run IDs, review IDs and merge state — remain external and are never embedded here.

## STOP CONDITION (Delta 005)
STOP if any correction beyond this Context Lock is required; if any accepted closeout predicate or the package contract would need to change; if fresh exact-head Governance, Desktop Shell or Native Package Matrix is not fully green; if any HIGH/CRITICAL finding appears; or if any step would mark the closeout PR Ready, merge it, close Issue #82, assert CP-0025 effectiveness prematurely, or begin `HCODER-DIST-001C`.
