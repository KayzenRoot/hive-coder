# HCODER-WO-0024 — Distribution Contracts, Version Model and UpdateService Boundary

**Status:** IMPLEMENTED / CORRECTION REVIEW PENDING  
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Decision:** `DEC-028` PROPOSED / NOT CANONICAL (version/channel source-of-truth law; an ADR exists at `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md` with a matching ledger entry, materialised under Context Lock Delta 001)  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**PR:** `#80` (Draft, unmerged)  
**Review history:** `5236275753` — CORRECTION_REQUIRED (CRITICAL `0` / HIGH `4` / MEDIUM `2`) at prebuild head `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`  
**Context Lock Deltas:** `001` (correction of the six findings below; no new authority)

## Objective
Establish the first governed slice of distribution: the canonical version/channel model and a Hive-owned `UpdateService` boundary, so that later distribution work is completion-oriented rather than architecture discovery.

This slice defines **contracts and inert seams only**. It grants no update, install, download, network, signing, release or packaging authority.

## Bounded first slice
- one canonical product-version source of truth with deterministic mirrors and a drift verifier;
- strict SemVer parsing that fails closed;
- release channels `stable`, `beta`, `dev/internal`, stable as production default, unknown values fail closed;
- a deterministic update-state model with explicit legal transitions and a mandatory authenticity gate;
- a Hive-owned `UpdateService` interface with an inert, fail-closed production implementation;
- a bounded, read-only Settings/About read model;
- adversarial contract tests and evidence scaffolding.

## Canonical version law
Exactly one canonical source exists: `apps/desktop/src-tauri/tauri.conf.json` → `version`.

Rationale, from build and release semantics rather than convenience: the Tauri application version is the version the bundler and a future updater treat as the shipped product version. The Rust package version (`Cargo.toml`) and the npm package version (`package.json`) are implementation-package versions and are therefore **mirrors** that must equal the canonical value exactly. `tools/desktop/version_drift.py` enforces this deterministically and offline.

## Requested authority
None. This slice adds no runtime authority, no capability, no permission and no control-plane path.

## Explicitly not approved
No `bundle.active=true`; no updater plugin; no updater endpoint; no HTTP client or network request; no artifact download; no installer execution; no restart; no release or tag creation; no artifact publication; no signing, notarization or key/secret access; no CI release workflow; no rollback/downgrade execution; no expansion of filesystem, Git, shell/process, Cua or credential authority; no production-distributable claim; no Settings/About side effect, background check, notification centre or broad UI redesign.

## Security / supply-chain law
1. Update metadata and artifacts are untrusted input until a later governed slice proves cryptographic verification.
2. HTTPS is never treated as authenticity proof.
3. Models, tools and backends cannot mint release or update authority.
4. Signing material must never appear in repository, logs, prompts or runtime state.
5. Version, channel and update-state parsing fails closed on malformed or unknown input.
6. No silent downgrade and no implicit cross-channel promotion or demotion.
7. Entering an install-ready state (`ready`, and `installing` again as defence in depth) structurally requires an accepted authenticity/integrity proof; this slice admits **no** cryptographic scheme, so install-ready is unreachable by construction, and a direct `ready`/`installing` status snapshot is invalid.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.
9. One current version and one current channel form a single identity. A pair that is individually valid but mutually incompatible fails closed at service configuration, at status validation and at the read-model boundary.
10. A status snapshot is a closed, bounded object: exact key sets at the top level, inside the error object and inside every event; unknown keys, unknown vocabularies and incoherent candidates are refused, and a validated snapshot is reconstructed from validated fields rather than returned as the caller's object.

## Correction record (Context Lock Delta 001)

The first implementation head passed both hosted gates yet did not hold the properties it claimed. Independent review `5236275753` returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `4` / MEDIUM `2`:

| Finding | Defect | Correction |
|---|---|---|
| `H-20-01` | The authenticity gate sat on `ready -> installing` while `verifying -> ready` was ungated, so install-ready was reachable with no proof; a direct `ready`/`installing` status was accepted. | Gate moved to the install-ready edge (`verifying -> ready`) and re-applied on `ready -> installing`. Install-ready status snapshots now require an accepted proof and are therefore invalid while the scheme allowlist is empty. |
| `H-20-02` | Version and channel were validated independently; `0.1.0` + `beta` was accepted, and the About model did not have to agree with the status it displayed. | Version+channel is one identity, enforced at service construction, in status validation (current and candidate) and in the About read model against the validated status. |
| `H-20-03` | `evaluateStatus` bounded only the event count, validated no event object, rejected no unknown key, and returned the untrusted input cast as `UpdateStatus`. | Exact key sets at every level, per-event validation against the closed vocabulary and the transition table, state-dependent candidate and error invariants, and reconstruction of a canonical object from validated fields only. |
| `H-20-04` | Numeric prerelease identifiers were compared through `Number()`, so distinct identifiers above `2^53` collapsed and compared equal. | Exact comparison by digit length then lexicographically; regression cases at `9007199254740991/2/3` and for much longer identifiers. |
| `M-20-05` | `versionMatchesChannel` used a second, looser version-shape regex, so malformed versions such as `1.0.0-beta.` satisfied the channel prefix test. | The channel-shape test is derived exclusively from the canonical strict parser; malformed input matches no channel. |
| `M-20-06` | `DEC-028` was referenced as PROPOSED but neither the ADR nor a ledger entry existed. | `DEC-028` ADR created as `PROPOSED / NOT CANONICAL` with a matching ledger entry, under Context Lock Delta 001. |

No correction weakens a gate, widens authority, admits an authenticity scheme or adds a dependency, and no test was weakened, skipped or rewritten to accept the defective behaviour.

## Acceptance law
Prebuilt contract tests come first. Promotion requires: canonical-and-mirrors drift lock, fail-closed unknown/malformed version and channel, illegal-transition rejection, downgrade and cross-channel refusal, install-ready refusal without accepted authenticity proof, bounded redaction-safe error metadata, proof that the inert boundary exposes no mutating/transport/install member, proof that no network/process/update side effect is reachable, and independent Windows/Linux/macOS evidence.

## Preserved exclusions
No commit/ref/branch/tag mutation; no checkout/reset/restore/clean/stash; no merge/rebase/cherry-pick; no remote/network/credentials; no hooks or executable filters; no generic shell/process/terminal; no arbitrary `.git` write authority; no desktop/Tauri mutation expansion.

## STOP CONDITION
If completing this slice requires activating an updater plugin, a network or download path, installation or restart, signing/notarization, release publication, a dependency that introduces update or distribution side effects, or weakening an existing HIGH_ASSURANCE gate, stop and create the smallest explicit governed delta. Do not smuggle distribution authority into this Work Order.
