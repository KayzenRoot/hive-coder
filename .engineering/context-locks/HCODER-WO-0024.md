# HCODER-WO-0024 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Authority delta:** none — contracts and inert seams only

## Source check
- Current desktop Git observation is read-only and does not execute Git.
- `tauri.conf.json` declares `productName="Hive Coder"`, `version="0.1.0"`, `bundle.active=false`.
- `Cargo.toml` declares package version `0.1.0` with Tauri `=2.11.5`; `package.json` declares version `0.1.0` with `@tauri-apps/api` `2.11.1` and `@tauri-apps/cli` `2.11.4`.
- No `UpdateService` contract, release-channel contract or version source-of-truth law existed before this Work Order.
- `tools/desktop/security_gate.py` is the established precedent for a Python, offline, read-only desktop gate that parses the same manifests.

## Selected first slice
Distribution contracts only: canonical version law with drift verifier, release-channel contract, update-state model with an authenticity gate, a Hive-owned `UpdateService` boundary whose production implementation is inert, and a bounded read-only Settings/About read model.

An updater plugin, HTTP client, download, installer, restart, signing, notarization or release publication is **not** pre-approved and is not part of this slice.

## Security law
1. Default deny; this slice adds no authority at all.
2. Update metadata and artifacts are untrusted until a later governed slice proves verification; HTTPS is never authenticity proof.
3. No model, tool or backend may mint release or update authority.
4. Signing material never enters repository, logs, prompts or runtime state.
5. Version, channel and update-state parsing fail closed on malformed or unknown input.
6. No silent downgrade; no implicit cross-channel promotion or demotion.
7. `ready`-to-install requires authenticity proof inputs; no cryptographic scheme is admitted in this slice, so install-ready is unreachable.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.
9. The inert boundary must expose no mutating, transport or installation member, and must be provably unreachable from a production side-effect path.

## Allowed-file set
This Work Order may change only:
- `.engineering/work-orders/HCODER-WO-0024.md`
- `.engineering/context-locks/HCODER-WO-0024.md`
- `.engineering/evidence/HCODER-WO-0024.md`
- `.engineering/prebuilt/HCODER-WO-0024-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0024-EXECUTOR-BRIEF.md`
- `.engineering/prebuilt/HCODER-WO-0024-ACCEPTANCE-SECURITY-MAP.md`
- `apps/desktop/src/contracts/version.ts` and `version.test.ts`
- `apps/desktop/src/contracts/releaseChannel.ts` and `releaseChannel.test.ts`
- `apps/desktop/src/contracts/updateState.ts` and `updateState.test.ts`
- `apps/desktop/src/contracts/aboutReadModel.ts` and `aboutReadModel.test.ts`
- `apps/desktop/src/lib/updateService.ts` and `updateService.test.ts`
- `tools/desktop/version_drift.py`
- `tests/desktop/__init__.py`, `tests/desktop/test_version_drift.py`
- `.github/workflows/desktop-shell.yml` and `.github/workflows/governance.yml` only for the exact version-drift gate and its native proof step

Any expansion requires an explicit Context Lock delta before code changes.

## Forbidden files
Runtime Git/filesystem/shell/Cua authority code, control-plane files, dependency manifests and lockfiles, existing security or contract tests, release/distribution implementation, updater integration, Tauri capability files, `tauri.conf.json`, `Cargo.toml`, `package.json` and release workflows.

## STOP CONDITION
STOP and return to architecture/review if the slice would require activating an updater, a network or download path, installation or restart, signing/notarization, release publication, a dependency carrying update/distribution side effects, `bundle.active=true`, a weakened HIGH_ASSURANCE gate, or any filesystem/Git/shell/Cua/credential authority expansion.

---

# Context Lock Delta 001

**Status:** SAME WORK ORDER — CORRECTION AUTHORISED  
**Authority granted:** none beyond the pre-existing allowed-file set, plus the two governance-document paths named below  
**Trigger:** independent review `5236275753`, verdict `CORRECTION_REQUIRED` on exact head `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`

## Recorded findings (as returned by the independent review)

Unresolved severity at review time: **CRITICAL 0 / HIGH 4 / MEDIUM 2**.

- **H-20-01** — the authenticity gate is on the wrong edge. `LEGAL_TRANSITIONS` admits `verifying -> ready` unconditionally and `evaluateTransition()` requires a proof only for `ready -> installing`, while `evaluateStatus()` accepts a direct `state:"ready"` snapshot. Install-ready is therefore reachable with no accepted proof, contradicting the claimed "install-ready unreachable by construction" property.
- **H-20-02** — version and channel do not form one bound identity. `InertUpdateService` validates them independently, `evaluateStatus()` accepts a mismatched pair, and `buildAboutReadModel()` does not require its own version/channel to match the validated status snapshot. `{currentVersion:"0.1.0", currentChannel:"beta"}` was accepted as a positive test case.
- **H-20-03** — status snapshots are not closed or bounded despite acceptance row C11 claiming they are. `evaluateStatus()` bounds only the event count, does not validate event objects or reject unknown top-level/status/error/event keys, and returns the original untrusted input object cast as `UpdateStatus`.
- **H-20-04** — `compareIdentifier()` in `version.ts` compares numeric prerelease identifiers through JavaScript `Number()`, so adjacent identifiers above `2^53` can collapse to the same double and compare equal, corrupting same-channel upgrade/downgrade eligibility.
- **M-20-05** — `versionMatchesChannel()` in `releaseChannel.ts` uses a second, permissive version-shape regex instead of the canonical strict parser, so malformed forms such as an empty prerelease identifier can satisfy the channel-prefix test.
- **M-20-06** — `DEC-028` is referenced as `PROPOSED` but no ADR exists and the Decisions Ledger has no `DEC-028` entry on this exact head.
- **Evidence/source-truth** — acceptance-map rows claiming `MATERIALISED` for the defective properties must return to `PENDING` until corrected exact-head tests prove them, and the Work Order/evidence stage vocabulary must say implemented / correction-review pending rather than implementation pending.

## Authorisation

1. This delta authorises the bounded correction of exactly the findings above, inside the existing allowed-file set. It authorises **no new product capability, no new dependency, no new runtime authority** and no change to the slice boundary declared above.
2. It additionally authorises two governance-document paths not previously in the allowed-file set, solely to materialise the proposal required by M-20-06:
   - `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md` — to be created with status `PROPOSED / NOT CANONICAL`;
   - `docs/project-brain/10-DECISIONS-LEDGER.md` — to receive the matching `DEC-028` proposed entry.
   Authoring a proposal records no approval and promotes nothing: `DEC-028` remains non-canonical until an independent HEDS approves a later promotion.
3. Corrections must be made by strengthening the contracts and their tests. No test may be weakened, skipped, deleted or rewritten to accept the reviewed defective behaviour, and no HIGH_ASSURANCE gate or security rule may be relaxed.
4. The PR remains **Draft and unmerged**. No promotion claim, no DEC promotion and no `HCODER-DIST-001B` work is authorised by this delta.

## STOP CONDITION (unchanged, plus)
In addition to the pre-existing STOP condition: STOP if any finding can only be closed by widening authority, admitting an authenticity scheme, weakening a gate, or expanding outside the file set above.
