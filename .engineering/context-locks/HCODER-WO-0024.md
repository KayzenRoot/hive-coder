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

---

# Context Lock Delta 002

**Status:** SAME WORK ORDER — SECOND CORRECTION AUTHORISED  
**Authority granted:** none beyond the pre-existing allowed-file set, plus one test-fixture path named below  
**Trigger:** independent HEDS A4 review `5236688350`, verdict `CORRECTION_REQUIRED` on exact head `97c533de73c9d8f007b6dfc4eaf73804fb1de220`

## Recorded findings (as returned by the independent review)

Unresolved severity at review time: **CRITICAL 0 / HIGH 2 / MEDIUM 1**. The review accepted H-20-02, H-20-03 ordinary own-key closure, H-20-04, M-20-05 and M-20-06 as materially corrected and found no authority or dependency expansion.

- **H-21-01 (residual H-20-01) — the authenticity lifecycle can still be bypassed by status injection.** `ready` and `installing` are proof-gated, but `evaluateStatus()` accepts a direct `state:"success"` snapshot with a strictly newer candidate and `authenticityProof:null`. `success` is reachable only from `installing` in the declared state graph, so the status boundary can assert a completed install while no proof can be accepted. Recorded events also validate only structural edges, so current-v1 history can represent proof-gated transitions as successful without carrying gate evidence.
- **H-21-02 — canonical SemVer semantics diverge between product TypeScript and the Python drift gate.** `version.ts` converts core `major/minor/patch` through `Number()` and rejects values above `Number.MAX_SAFE_INTEGER`, while `version_drift.py` accepts arbitrary-length core numeric identifiers. Python can therefore report `LOCKED` for a canonical version such as `9007199254740993.0.0` that product TypeScript rejects as malformed. Python also uses `SEMVER_PATTERN.match(...$)`, which accepts a final newline that TypeScript rejects.
- **M-21-03 — exact-object validation is not limited to plain own-data records.** `asRecord()` accepts any non-array object and `hasOnlyKeys()` inspects only `Object.keys()`. Required fields may be inherited or getter-backed, so reads can execute accessors even though the contract is described as pure and closed.
- **Parity note discovered while correcting H-21-02.** Python's `\d` matches Unicode decimal digits where JavaScript's `\d` is ASCII-only, so `1.0.0-1٠` was accepted by the drift gate and rejected by the product parser. This is the same divergence class as H-21-02 and is closed with it rather than recorded as a separate finding.

## Authorisation

1. This delta authorises correction of exactly `H-21-01`, `H-21-02` and `M-21-03`, plus directly related tests, evidence and documentation, inside the existing allowed-file set. **No new authority, no new dependency, no checkpoint mutation and no DEC promotion** are authorised.
2. It additionally authorises one new file, solely as a shared cross-language test fixture so that the TypeScript and Python acceptance sets cannot drift apart:
   - `apps/desktop/src/contracts/semverParityVectors.json` — a deterministic vector file consumed by both test suites.
3. Delta 001 and the Prompt-20/Prompt-21 review history are preserved verbatim as historical evidence. No earlier finding, review record or defective-head record may be erased, softened or rewritten.
4. The correction must strengthen the contracts. No test may be weakened, skipped, deleted or rewritten to accept the reviewed defective behaviour; no HIGH_ASSURANCE gate or security rule may be relaxed.
5. The PR remains **Draft and unmerged**. No promotion claim, no `DEC-028` canonicalisation and no `HCODER-DIST-001B` work is authorised by this delta.

## STOP CONDITION (Delta 002)
STOP if closing any of the three findings would require updater, network, download, install, restart, signing or release authority, a new distribution dependency, a weakened HIGH_ASSURANCE gate, a change to the declared version law beyond the bounded profile (STOP for architecture review instead of silently diverging), historical migration semantics beyond v1 (STOP for an explicit versioned design), or any step that would mark PR #80 Ready, merge it, canonicalise `DEC-028` or begin `HCODER-DIST-001B`.

---

# Context Lock Delta 003

**Status:** SAME WORK ORDER — THIRD CORRECTION AUTHORISED  
**Authority granted:** none beyond the pre-existing allowed-file set; no new file path is required  
**Trigger:** independent HEDS review `5237206705`, verdict `CORRECTION_REQUIRED` on exact head `92b6b80fb599b3e2f810b1591b63a68e6b11ddf0`

## Recorded findings (as returned by the independent review)

Unresolved severity at review time: **CRITICAL 0 / HIGH 1 / MEDIUM 1**. The review accepted H-21-02 (cross-language bounded SemVer parity) and M-21-03 (plain own-data record hardening) as materially closed, confirmed that direct `ready`/`installing`/`success` status injection is blocked, and found no authority or dependency expansion.

- **H-22-01 (residual H-21-01) — current-v1 event history can still assert an impossible authenticity-dependent source state.** The event validator rejects `legal_transition` only when the **destination** is authenticity-dependent. It still accepts events whose **source** is authenticity-dependent — `ready -> idle` and `installing -> failure` were explicitly asserted as valid history in the test suite. Such an event asserts that the source state previously existed, which in current v1 implies a successful traversal of the proof-gated path, contradicting the same contract law that the whole install path is unreachable.
- **M-22-02 — event reason is not semantically coupled to the edge.** The validator requires a legal structural edge and a reason from the global `TransitionReason` vocabulary, but does not prove that the outcome is possible for that edge, so an ordinary legal edge can be recorded with `illegal_transition`, `unknown_state` or `authenticity_proof_required` even when `evaluateTransition()` could never produce that outcome for the same edge.

## Required corrections recorded by the review

1. Under the current v1 / no-scheme policy, **no recorded event may have an authenticity-dependent source state**; a persisted event whose `from` is `ready`, `installing` or `success` fails closed regardless of destination or reason.
2. A refusal attempt **into** an authenticity-dependent destination remains recordable only from a reachable source and only with the matching refusal reason. With the present graph and an empty allowlist the only such attempt is `verifying -> ready`.
3. Persisted event outcomes become a **closed semantic contract**: ordinary reachable legal edges record `legal_transition`; the reachable proof-gated attempt records the bounded refusal outcomes. A distinct versioned event type is required if raw attempted input ever needs to be persisted — `UpdateEvent` must not be overloaded for that.
4. No migration semantics may be invented. If records from another contract version must be supported, STOP and request a separately versioned migration contract.

## Authorisation

1. This delta authorises correction of exactly `H-22-01` and `M-22-02`, plus directly related tests, evidence and documentation, inside the existing allowed-file set. **No new authority, no new dependency, no checkpoint mutation and no DEC promotion** are authorised, and no new file path is needed.
2. Deltas `001` and `002` and all earlier review history are preserved verbatim as historical evidence. No earlier finding, review record or defective-head record may be erased, softened or rewritten.
3. The correction must strengthen the contract. No test may be weakened, skipped, deleted or rewritten to accept the reviewed defective behaviour, and no HIGH_ASSURANCE gate or security rule may be relaxed. Removing the two Prompt-22 positive expectations that the review identified as wrong (`ready -> idle`, `installing -> failure`) is required by the review and is a correction of an over-permissive expectation, not a weakening.
4. The PR remains **Draft and unmerged**. No promotion claim, no `DEC-028` canonicalisation and no `HCODER-DIST-001B` work is authorised by this delta.

## STOP CONDITION (Delta 003)
In addition to the two STOP conditions above: STOP if closing either finding would require supporting historical records from another contract version (STOP for a separately versioned migration design), if any accepted Prompt-22 correction regresses, or if any step would mark PR #80 Ready, merge it, canonicalise `DEC-028` or begin `HCODER-DIST-001B`.

---

# Context Lock Delta 004

**Status:** SAME WORK ORDER — FOURTH CORRECTION AUTHORISED  
**Authority granted:** none beyond the pre-existing allowed-file set; no new tracked file path is required  
**Trigger:** independent HEDS review `5237592683` with remediation-bound addendum comment `5716617080`, verdict `CORRECTION_REQUIRED` on exact head `a3e585823695f889dae92acc7cc5b57a17ba617d`

## Recorded findings (as returned by the independent review)

Unresolved severity at review time: **CRITICAL 0 / HIGH 1 / MEDIUM 1**. The review accepted H-22-01 (event source reachability) and M-22-02 (outcome/edge coupling) as materially closed and confirmed that the Prompt-22 parity, snapshot rejection, plain-own-data hardening, identity binding and closed reconstruction all remain intact.

- **H-23-01 — the declared shared version acceptance profile is broader than the actual mirror/build surface.** The contract, the drift gate and the shared parity fixture accepted arbitrary-precision core `major`/`minor`/`patch` identifiers, but the Work Order declares `Cargo.toml` an exact mirror, and the real consumers bound core components: Cargo/Rust SemVer uses `u64`, and npm's `node-semver` rejects core components above `Number.MAX_SAFE_INTEGER`. The gate could therefore report `LOCKED` for a canonical/mirrored version that a declared build surface cannot parse.
- **M-23-02 — self-staling governance prose.** DEC-028's promotion table named a moving correction round as the current promotion state; the Evidence Bundle claimed the corrected head "has not yet been gated or independently reviewed" while exact-head gates were complete, and separately claimed `HEDS: NOT YET RUN on any head` while listing three HEDS reviews in the same file; the terminal STOP block is duplicated.
- **Addendum `5716617080` (supersedes only the remediation bound).** The correct bound is **not** `u64::MAX`. The profile must be the intersection of every real consumer of the mirrored version: Cargo's `u64` is wider than npm's `Number.MAX_SAFE_INTEGER`, so the npm bound is the binding one: core `major`/`minor`/`patch` are bounded to `9007199254740991`. Exact decimal-string ordering must be preserved (no floating-point comparison), and arbitrary-length *prerelease* numeric identifiers remain admissible because no consuming surface imposes a lower bound there.

## Toolchain constraint check performed before authorisation

Both declared consumers were checked against repository-pinned tooling rather than assumed:

- **npm / node-semver** — the `node-semver` bundled with the repository's npm toolchain (version 7.8.1, shipped by npm 11.16.0) accepts core `9007199254740991`, rejects `9007199254740992`, `9007199254740993`, a 30-digit core and `u64::MAX`, and keeps an oversized numeric prerelease identifier as a string.
- **Cargo / semver crate** — the crate pinned in `apps/desktop/src-tauri/Cargo.lock` (semver 1.0.28) accepts core values up to `u64::MAX` and rejects `u64::MAX + 1` ("exceeds u64::MAX"), and accepts arbitrary-length numeric prerelease identifiers.

The intersection is `Number.MAX_SAFE_INTEGER`, so the review's addendum bound is confirmed and no STOP for a narrower-than-expected consumer is triggered. A persistent CI change is not required for this proof and none is authorised.

## Authorisation

1. This delta authorises correction of exactly `H-23-01` and `M-23-02`, plus directly related tests, evidence and documentation, inside the existing allowed-file set. **No manifest or lockfile version change, no new dependency, no new authority, no checkpoint mutation and no DEC promotion** are authorised.
2. Deltas `001`, `002` and `003` and all earlier review history are preserved verbatim as historical evidence. No earlier finding, review record or defective-head record may be erased, softened or rewritten.
3. The correction must strengthen the contract. Bounding the core identifier range narrows acceptance deliberately and requires removing the now-invalid oversized-core vectors; that is a correction of an over-broad law, not a weakening. No HIGH_ASSURANCE gate or security rule may be relaxed and no previously accepted security correction may regress.
4. Exact decimal-string comparison must be preserved for accepted values, and numeric prerelease identifiers remain exact within the overall version-length bound.
5. Self-staling wording must be replaced with stage-bound requirements; mutable exact-head receipts belong in PR #80, Issue #30 and the Prompt return, never inside the pre-CI commit.
6. The PR remains **Draft and unmerged**. No promotion claim, no `DEC-028` canonicalisation and no `HCODER-DIST-001B` work is authorised by this delta.

## STOP CONDITION (Delta 004)
In addition to the three STOP conditions above: STOP if the pinned toolchain proves a bound narrower than `Number.MAX_SAFE_INTEGER` that cannot be reconciled without architecture review, if closing either finding requires a manifest version change, a new dependency or a weakened HIGH_ASSURANCE gate, if any Prompt-23 event-history or security correction regresses, or if any step would mark PR #80 Ready, merge it, canonicalise `DEC-028` or begin `HCODER-DIST-001B`.

---

# Context Lock Delta 005

**Status:** SAME WORK ORDER — DOCUMENTATION/SOURCE-TRUTH CORRECTION ONLY  
**Authority granted:** none beyond documentation reconciliation of the governance documents named below  
**Trigger:** independent HEDS review `5238290797`, verdict `CORRECTION_REQUIRED` on exact head `0ec09d7e0d67018d51ee791a2bbca9f39f41c131`

## Recorded findings (as returned by the independent review)

Unresolved severity at review time: **CRITICAL 0 / HIGH 0 / MEDIUM 2**. The review accepted `H-23-01` as CLOSED (one toolchain-compatible bounded profile with core identifiers bounded to `9007199254740991`, exact decimal-string comparison, shared parity vectors, u64-boundary rejection, legal 128-character boundary coverage and exact large-prerelease ordering), confirmed the Prompt-23 persisted-event law remains closed, and found no authority, dependency, manifest, lockfile or DEC promotion change.

- **M-24-01 — the Decisions Ledger still contradicts the corrected proposal.** The `DEC-028` entry says the proposal was corrected only under Deltas 002/003 (omitting Delta 004), still describes the profile as arbitrary-precision core identifiers, and ties promotion to a moving "third corrected exact head".
- **M-24-02 — residual durable-prose inconsistencies.** The Evidence Bundle still carries count-based claims (`all three rounds`, `all eleven recorded findings`) although a fourth bounded correction exists, and the Work Order / ADR security wording overstates recorded-history destination semantics by implying that an authenticity-dependent state requires proof merely because it is named as a *recorded event destination* — while the law deliberately permits a refused `verifying -> ready` attempt that names `ready` as the attempted destination without asserting that it was entered.

## Authorisation

1. This delta authorises **documentation/source-truth correction only**, limited to:
   - `.engineering/context-locks/HCODER-WO-0024.md` (this Delta 005 append);
   - `docs/project-brain/10-DECISIONS-LEDGER.md` (the `DEC-028` entry);
   - `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md`;
   - `.engineering/work-orders/HCODER-WO-0024.md`;
   - `.engineering/evidence/HCODER-WO-0024.md`;
   - the Implementation Pack, Executor Brief and Acceptance/Security Map **only** where a stale current-state phrase is actually present.
2. **Forbidden without a new delta:** every TypeScript, Python and Rust source or test file, `.github/workflows/*`, `tauri.conf.json`, Cargo/npm manifests and lockfiles, runtime/control-plane files, dependencies, release files, and any `HCODER-DIST-001B` work. The technical files at this correction head must be byte-identical to the start head `0ec09d7e0d67018d51ee791a2bbca9f39f41c131` except for the documentation paths listed above.
3. No product/runtime authority is granted, `evaluatePersistedEvent` behaviour is unchanged, and no version/profile/event law changes — only its documentation.
4. Deltas `001`–`004` and all prior review history are preserved verbatim as historical evidence. Historical finding and reviewed-head descriptions are not rewritten; only current-state summary prose is made durable.
5. `DEC-028` remains **PROPOSED / NOT CANONICAL**; the PR remains **Draft and unmerged**; no promotion claim may be made on the basis of this correction.

## STOP CONDITION (Delta 005)
STOP if any technical/runtime/test/workflow/manifest/dependency change becomes necessary, if a correction would change the actual version, profile or event law rather than reconcile its documentation, if fresh exact-head Governance or Desktop Shell fails, if any HIGH or CRITICAL finding appears, or if any step would mark PR #80 Ready, merge it, canonicalise `DEC-028` or begin `HCODER-DIST-001B`.

---

# Context Lock Delta 006

**Status:** SAME WORK ORDER — RESIDUAL DOCUMENTATION/SOURCE-TRUTH CORRECTION ONLY  
**Authority granted:** none beyond documentation reconciliation of the paths named below  
**Trigger:** independent HEDS review `5238504760`, verdict `CORRECTION_REQUIRED` on exact head `b12baf1650be23a28dda0b04f1cca40687a205ca`

## Recorded finding (as returned by the independent review)

Unresolved severity at review time: **CRITICAL 0 / HIGH 0 / MEDIUM 1**. The review accepted `M-24-01` as CLOSED, confirmed the count-based Evidence wording and the Work Order event-history wording are corrected, confirmed Delta 005 changed governance/document paths only, and confirmed the fresh exact-head gates.

- **M-25-01 — one residual current-state source-truth contradiction.** `DEC-028` Security law item 7 still read "Every authenticity-dependent state requires an accepted authenticity proof, including in a status snapshot or a recorded history entry", which is broader than the ADR's own corrected persisted-event law: a `verifying -> ready` attempt may be recorded with a bounded refusal outcome, without accepted proof and without asserting that `ready` was entered. The Evidence Bundle also still described the implemented property as "whole-install-path unreachability across snapshots, sources and destinations", which can be read as prohibiting even an attempted destination.

## Required durable law (to be stated identically wherever it is summarised)

1. A legal **transition that would actually enter** `ready`, `installing` or `success` requires an accepted authenticity proof. Transition-time law is unchanged.
2. An authenticity-dependent state cannot be asserted as a **current status** while no scheme is admitted.
3. An authenticity-dependent state cannot be a **persisted event source**.
4. A persisted event cannot claim **successful entry** into an authenticity-dependent state.
5. A **refused attempt** toward `ready` from a reachable source (`verifying -> ready`) is recordable with the bounded refusal outcomes `authenticity_proof_required` or `malformed_authenticity_proof`. That records a refusal and does not assert that `ready` was entered, or that it ever existed as a current state.

## Authorisation

1. This delta authorises **documentation/source-truth correction only**, limited to:
   - `.engineering/context-locks/HCODER-WO-0024.md` (this Delta 006 append);
   - `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md` (Security law item 7);
   - `.engineering/evidence/HCODER-WO-0024.md`;
   - the Work Order, Implementation Pack, Executor Brief, Acceptance/Security Map and Decisions Ledger **only** if the scan finds the same current-state semantic overstatement.
2. **Forbidden:** every TypeScript, Python and Rust source or test file, `.github/workflows/*`, `tauri.conf.json`, Cargo/npm manifests and lockfiles, dependency files, runtime/control-plane code, release files, and any `HCODER-DIST-001B` work.
3. No behaviour changes: `evaluateTransition`, `evaluatePersistedEvent`, the state vocabularies, the outcome vocabularies and every test remain untouched. The transition-entry rule is not weakened, and no current-state document may imply that a persisted refusal attempt itself needs accepted proof, or that naming `ready` as an attempted destination means it was entered.
4. Deltas `001`–`005` and all prior review history are preserved verbatim. Historical defect descriptions scoped to a reviewed head keep their original wording.
5. `DEC-028` remains **PROPOSED / NOT CANONICAL**; the PR remains **Draft and unmerged**; mutable gate and review evidence stays external in PR #80 and Issue #30, and no future head SHA or run ID is embedded in the pre-CI commit.

## STOP CONDITION (Delta 006)
STOP if any technical/runtime/test/workflow/manifest/dependency change becomes necessary, if a correction would change behaviour rather than documentation, if fresh exact-head Governance or Desktop Shell fails, if any HIGH or CRITICAL finding appears, or if any step would mark PR #80 Ready, merge it, canonicalise `DEC-028` or begin `HCODER-DIST-001B`.

---

# Context Lock Delta 007

**Status:** SAME WORK ORDER — ANTI-SELF-STALING GOVERNANCE CORRECTION (documentation only)  
**Authority granted:** none beyond documentation restructuring of the paths named below  
**Trigger:** independent HEDS review `5238656172`, verdict `CORRECTION_REQUIRED` on exact head `45b201583878ddfcd774351fc74564eb24f9171e`

## Recorded finding (as returned by the independent review)

Unresolved severity at review time: **CRITICAL 0 / HIGH 0 / MEDIUM 1**. The review accepted `M-25-01` as materially CLOSED, confirmed Delta 006 was documentation-only with no technical, workflow, manifest, lockfile or dependency change, and confirmed `DEC-028` remains PROPOSED / NOT CANONICAL.

- **M-26-01 — self-staling mirrored governance indices.** The Work Order mirrored `Context Lock Deltas: 001–005`, the Implementation Pack mirrored `Bounded corrections: Deltas 001–005`, the Acceptance/Security Map still declared `Authority: ... Deltas 001–004`, and `DEC-028` said `Materialised under ... Deltas 001–005` even though Delta 006 changed that ADR. Several `Immutable review history` headers listed review sets that stopped before the most recent review. Copied terminal delta numbers and exhaustive review lists guarantee another stale pointer whenever the next bounded correction or review occurs. This is not a product defect: it is a source-truth architecture defect in governance prose.

## Anti-self-staling rule (binding for this Work Order from Delta 007 onward)

1. **The Context Lock file is the canonical append-only authority history for this Work Order.** `.engineering/context-locks/HCODER-WO-0024.md` is the single place where the delta sequence lives. No other durable document mirrors a terminal delta number, a terminal delta range, or a "current" delta pointer.
2. **Mutable current review and gate state is external.** PR #80 and Issue #30 are the canonical pointers for the latest review identifiers, verdicts and hosted gate receipts. Repository artifacts record *historical* reviewed-head facts in explicitly historical sections; they do not present a duplicated list as the complete current review index.
3. **A new Context Lock delta requires editing only the Context Lock**, unless that delta changes actual law or content in another artifact.
4. **A new independent review must not require editing any repository document merely to append its identifier.** Historical review identifiers already embedded in historical narratives remain valid and stay as they are.
5. **No live repository field may encode** `latest review`, `current terminal delta`, `all reviews` or equivalent moving-pointer semantics, outside the two canonical pointers above.
6. Deltas `001`–`006` and all prior review history are preserved verbatim. Historical findings are not deleted or rewritten because later reviews exist.

## Authorisation

1. This delta authorises **documentation/source-truth correction only**, limited to replacing terminal-delta mirrors and exhaustive live review-index headers with durable pointers, in:
   - `.engineering/context-locks/HCODER-WO-0024.md` (this Delta 007 append);
   - `.engineering/work-orders/HCODER-WO-0024.md`;
   - `.engineering/prebuilt/HCODER-WO-0024-IMPLEMENTATION-PACK.md`;
   - `.engineering/prebuilt/HCODER-WO-0024-EXECUTOR-BRIEF.md`;
   - `.engineering/prebuilt/HCODER-WO-0024-ACCEPTANCE-SECURITY-MAP.md`;
   - `.engineering/evidence/HCODER-WO-0024.md`;
   - `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md`;
   - `docs/project-brain/10-DECISIONS-LEDGER.md`.
2. **Forbidden:** every TypeScript, Python and Rust source or test file, `.github/workflows/*`, `tauri.conf.json`, Cargo/npm manifests and lockfiles, dependency files, runtime/control-plane code, release files, and any `HCODER-DIST-001B` work. No behaviour, law, gate or authority changes.
3. The corrected wording must be one that survives both a future delta and a future review without editing more than the Context Lock.

## STOP CONDITION (Delta 007)
STOP if any technical/runtime/test/workflow/manifest/dependency change becomes necessary, if a proposed wording would still require editing multiple documents whenever a new delta or review occurs, if fresh exact-head Governance or Desktop Shell fails, if any HIGH or CRITICAL finding appears, or if any step would mark PR #80 Ready, merge it, canonicalise `DEC-028` or begin `HCODER-DIST-001B`.

---

# Context Lock Delta 008

**Status:** SAME WORK ORDER — CANONICAL CLOSEOUT CANDIDATE (documentation/governance only)  
**Authority granted:** none beyond canonical closeout source changes on a fresh closeout branch; no runtime, updater, packaging, network, install, signing, release, filesystem, Git, shell, Cua or credential authority of any kind  
**Trigger:** product implementation merged and exact-main postvalidated, then approved for closeout preparation by PR comment `5718801331`

## Immutable product lifecycle facts (recorded, not live pointers)

| Stage | Fact |
|---|---|
| Independently reviewed product head | `81bdd283dfd299d5ad5035301d06501f6b953a56` |
| Reviewed-head tree | `99151781a7cd4a886bf0ea43bb9e29ca44b16cb1` |
| Independent product HEDS | `5239135676` — APPROVED FOR GOVERNED MERGE, CRITICAL `0` / HIGH `0` / MEDIUM `0` |
| Product PR | `#80` — squash merged with expected-head protection |
| Product merge SHA / canonical main at postvalidation | `c7f2a5f21369fd92b3493bea0be0192bbd7298b4` |
| Merge tree | `99151781a7cd4a886bf0ea43bb9e29ca44b16cb1` — identical to the reviewed-head tree |
| Post-merge Governance | `35252975365` SUCCESS on that exact main |
| Post-merge Desktop Shell | `35252975322` SUCCESS on that exact main |
| Post-merge review | PR comment `5718801331` — APPROVED for canonical closeout preparation |

Pre-merge base `main` was `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`. These are immutable lifecycle-stage facts, not live repository pointers.

## Authorised scope

1. Canonical closeout source only: the closeout checkpoint delta, the `HCODER-CP-0024` closeout evidence package, the canonical checkpoint source, the Work Order's final-state wording, the `DEC-028` / Decisions Ledger promotion wording in this closeout candidate, and directly related evidence wording.
2. **Forbidden:** every TypeScript, Python and Rust source or test file, `.github/workflows/*`, `tauri.conf.json`, Cargo/npm manifests and lockfiles, dependency files, runtime/control-plane/permission/capability code, release files, and any `HCODER-DIST-001B` implementation or issue activation.
3. The already-reviewed contract law does not change: the version source and exact mirrors, the toolchain-compatible bounded SemVer profile, the channel law, the authenticity law, the persisted-event law, plain-own-data validation with the zero-getter rule, and the inert Hive-owned `UpdateService` boundary all remain exactly as reviewed. This delta advances lifecycle/canonical status only.
4. Nothing in this delta admits installers, packages, signing/notarization, updater transport, download/install/restart, release or tag publication, or any production-distribution claim.

## Anti-self-staling law (Delta 007) remains in force

The closeout candidate records only facts already immutable before this branch existed. Future closeout review identifiers, future closeout CI receipts and the future closeout merge SHA stay **external** in PR and Issue pointers and must not be embedded into the pre-CI commit of this candidate. No moving `current main` field is created. Deltas `001`–`007` and all prior review history are preserved verbatim.

## STOP CONDITION (Delta 008)
STOP if any product, runtime, test, workflow, manifest, lockfile or dependency change becomes necessary; if any closeout edit would change the reviewed contract law rather than its lifecycle/canonical status; if any new updater, packaging, signing or release authority would be introduced; if fresh exact-head Governance or Desktop Shell is not fully green; or if any step would merge the closeout PR, close Issue #77, or begin `HCODER-DIST-001B`.
