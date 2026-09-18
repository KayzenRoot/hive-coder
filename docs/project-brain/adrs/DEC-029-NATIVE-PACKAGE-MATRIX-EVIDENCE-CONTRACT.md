# DEC-029 — Native Package Matrix Evidence Contract

**Status:** PROPOSED / NOT CANONICAL  
**Work Order:** `HCODER-WO-0025`  
**Issue:** `#82`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001B`  
**Canonical base:** `HCODER-CP-0024` / `3e1e1af7596c56716825206587bf2a88e1b179d0`  
**Reviews of this proposal:** prior reviewed-head facts are historical and recorded externally in the active PR and Issues #30 and #82; they are not mirrored here as a current index.  
**Materialised under:** `HCODER-WO-0025`; the canonical append-only delta history for this Work Order lives in `.engineering/context-locks/HCODER-WO-0025.md`, and no terminal delta number or range is mirrored here.

> **State record.** This ADR is a **proposal**. It records a durable evidence contract that `HCODER-WO-0025` is establishing and has no canonical standing. It grants no authority, admits no signing, notarization, release or updater, and is not evidence that Hive Coder is installable or production-distributable. It becomes canonical only through a governed promotion with an independent review reporting unresolved HIGH/CRITICAL `0/0`.

## Context

`HCODER-CP-0024` sealed the distribution and version contract law but admitted no packaging. Before `HCODER-WO-0025`, every existing desktop lane built with `tauri build --no-bundle` and no governed gate in this repository exercised the bundler at all — which is why the canonical config's missing icon declaration went unnoticed until a package slice was attempted.

Producing native packages raises a question the previous slice deliberately deferred: what may a generated package artifact be *used as*? A build that emits installers can very easily drift into implying trust, and a digest can very easily be read as authenticity. This proposal fixes that boundary before any package exists, rather than retrofitting it afterwards.

## Decision candidate

**1. One bounded native package matrix per platform.** Windows produces `msi` and `nsis`; macOS produces `app` and `dmg`; Linux produces `appimage` and `deb`. The matrix is declared, not discovered at runtime: a lane that cannot produce its declared targets fails closed instead of quietly shipping a smaller set.

**2. Split-build model, canonical activation preserved.** Packaging uses the pinned CLI's explicit bundling path — a native compile with `--no-bundle`, then an explicit `bundle` invocation naming its targets. `bundle.active` stays `false` in the canonical config, because explicit bundling does not require activating global bundling and a convenience flip would change how every existing lane behaves.

**3. The canonical config is not packaging config.** `apps/desktop/src-tauri/tauri.conf.json` remains the canonical version source and is not modified for packaging. Where the bundler needs an icon declaration the canonical config does not carry, that declaration is supplied as an **ephemeral, runner-local, non-tracked overlay** naming only already-generated deterministic icon inputs. The overlay is never committed, never uploaded as an artifact, and each lane proves canonical tracked source — and the canonical config's bytes — are unchanged after bundling.

**4. Package evidence is closed and deterministic.** A generated package set is described by a closed inventory schema (`hive-package-inventory-v1`) carrying the source SHA, canonical version, platform, architecture and one entry per package with type, relative path, byte size, digest algorithm, digest and the portable structural checks that passed. Discovery is bounded to one explicit package root created fresh per lane; manifest ordering and serialization are deterministic, so the same artifact set always yields byte-identical output. Absolute paths, traversal, symlink escape, artifacts outside the root, missing, duplicate, unexpected or zero-size packages, wrong versions and wrong source SHAs are all refused.

**5. Directory bundles are not files.** A macOS `.app` is hashed with a documented deterministic sorted-tree digest, never represented as a plain file hash, so a changed, added or removed file inside the bundle changes the recorded digest.

**6. Evidence is not trust.** A digest proves **byte identity and integrity for evidence transport**. It is not signing, not notarization and not a publisher-authenticity proof. Packages produced by this pipeline are deliberately unsigned, and unsigned state must never be reported as a security success.

**7. Internal evidence only.** Workflow artifacts carry generated packages and their inventory manifest, with short explicit retention. There is no GitHub Release, no tag creation, no release asset upload and no production publication. Installers are never executed to satisfy acceptance.

**8. Structural validation is non-installing and runner-native.** Each lane validates what its platform can validate without installing: install metadata and version on Windows, `hdiutil verify` for disks on macOS, package metadata for Debian archives on Linux, and format/magic/executable-bit checks for the file formats that carry them.

## Non-decision

This ADR does not approve signing, codesign, notarization, stapling or any publisher-authenticity claim; release or tag creation and GitHub Release publication; updater plugins, update endpoints, updater artifacts or channel-promotion execution; product network fetch; artifact download, install, restart or rollback behaviour; installer execution as acceptance; a tracked `bundle.icon` or any other canonical-config mutation for packaging; any new product dependency, plugin, permission or capability; or any production-distributable claim.

## Security law carried by this proposal

1. Default deny; this contract adds no product runtime authority.
2. No signing material, notarization credential, key, release token or protected secret is read, requested, printed, persisted or uploaded.
3. Digests are integrity evidence only and are never described as authenticity.
4. Unsigned and unnotarized state is expected here and is never presented as a security success.
5. Artifact discovery is always root-bounded and deterministic; stale outputs cannot satisfy acceptance.
6. The ephemeral overlay is never canonical config and never a new authority surface.
7. Existing exact-head, HIGH_ASSURANCE and distribution-contract gates are neither weakened nor skipped.

## Promotion gate

`DEC-029` is **PROPOSED / NOT CANONICAL**. Promotion is a durable gate rather than a statement about any particular head, and requires all of the following, each produced against whatever exact head the promotion decision names:

| Condition | Requirement |
|---|---|
| Evidence contract materialised | The inventory/validator law exists in source as executable code, with tests that fail when a guard is removed |
| Adversarial coverage | The negative, mutation, determinism and root-isolation proofs are implemented and green |
| Native matrix proven | Windows, macOS and Linux lanes each produce their declared targets on native runners, or the slice STOPs with exact native evidence instead of reducing the matrix |
| Canonical config preserved | No tracked config or icon-format mutation was required, proven per lane |
| Hosted exact-head gates | Governance, Desktop Shell and Native Package Matrix are green on that exact head |
| Independent review | An independent HEDS review of that exact head reports unresolved HIGH/CRITICAL `0/0` |
| Governed merge | The Work Order merges with expected-head protection |

Mutable evidence for these conditions lives in the active PR and Issues #30 and #82, where it can advance without falsifying this document. Until every condition is met, no promotion claim may be made for this decision or for Hive Coder's packaging capability.
