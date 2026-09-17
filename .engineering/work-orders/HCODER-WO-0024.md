# HCODER-WO-0024 — Distribution Contracts, Version Model and UpdateService Boundary

**Status:** IMPLEMENTED IN SOURCE — EXTERNAL PROMOTION EVIDENCE REQUIRED  
**Promotion evidence:** hosted exact-head gates, an independent HEDS review with unresolved HIGH/CRITICAL `0/0` and a governed expected-head merge are each required against the exact promotion head and are tracked in PR #80 and Issue #30, not in this document  
**Risk:** HIGH_ASSURANCE (supply-chain-adjacent)  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Decision:** `DEC-028` PROPOSED / NOT CANONICAL (version/channel source-of-truth law; an ADR exists at `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md` with a matching ledger entry, materialised under Context Lock Delta 001)  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**PR:** `#80` (Draft, unmerged)  
**Review history (immutable):** `5236275753` (CRITICAL `0` / HIGH `4` / MEDIUM `2`) at `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`; `5236688350` (CRITICAL `0` / HIGH `2` / MEDIUM `1`) at `97c533de73c9d8f007b6dfc4eaf73804fb1de220`; `5237206705` (CRITICAL `0` / HIGH `1` / MEDIUM `1`) at `92b6b80fb599b3e2f810b1591b63a68e6b11ddf0`; `5237592683` + addendum `5716617080` (CRITICAL `0` / HIGH `1` / MEDIUM `1`) at `a3e585823695f889dae92acc7cc5b57a17ba617d`; `5238290797` (CRITICAL `0` / HIGH `0` / MEDIUM `2`, documentation-only) at `0ec09d7e0d67018d51ee791a2bbca9f39f41c131`  
**Context Lock Deltas:** `001`–`005` (bounded corrections; `005` is documentation-only)

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
7. Every authenticity-dependent state (`ready`, `installing`, `success`) structurally requires an accepted authenticity/integrity proof: entering one as a transition destination and asserting one as a status snapshot both require it, and in recorded history such a state can neither be a **source** nor be claimed as **successfully entered**. This slice admits **no** cryptographic scheme, so the whole install path is unreachable by construction, cannot be asserted as a current state, and cannot be recorded as having existed or been entered. A refused attempt *toward* `ready` from a reachable source — `verifying -> ready` — remains recordable with the bounded refusal outcomes, and naming an attempted destination is not a claim that the state was entered.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.
9. One current version and one current channel form a single identity. A pair that is individually valid but mutually incompatible fails closed at service configuration, at status validation and at the read-model boundary.
10. A status snapshot is a closed object: exact key sets at the top level, inside the error object and inside every event; unknown keys, unknown vocabularies and incoherent candidates are refused, and a validated snapshot is reconstructed from validated fields rather than returned as the caller's object. Validation reads plain own-data records only and never executes an accessor.
11. One toolchain-compatible bounded SemVer 2.0.0 acceptance set: the product TypeScript parser and the Python drift gate accept exactly the same version strings, pinned by a shared cross-language vector file. Each core identifier is bounded to `0..9007199254740991` — the intersection of the declared mirror consumers, since npm's `node-semver` rejects core components above `Number.MAX_SAFE_INTEGER` while Cargo's `u64` range is wider — and the whole string is bounded to 128 characters. Numeric identifiers are compared exactly as decimal strings at every position, with no floating-point conversion and no platform-dependent integer coercion; numeric prerelease identifiers are not core-bounded.
12. A persisted history entry must be an assertion this contract could actually have produced: declared states, a source state that current v1 can reach, a declared legal edge, and an outcome that edge could actually yield. A recorded entry may never assert an authenticity-dependent source state or an outcome that is impossible for its edge.

## Documentation reconciliation (Context Lock Delta 005)

Independent review `5238290797` accepted `H-23-01` as closed and returned two documentary findings only. Under Delta 005 — documentation-only, with no product, test, workflow, manifest or dependency change:

- the Decisions Ledger `DEC-028` entry was reconciled with the corrected proposal (Deltas 002–004 represented, the toolchain-compatible bounded profile described accurately, and the promotion gate restated as durable requirements rather than a named round) (`M-24-01`);
- count-based prose in the Evidence Bundle was replaced with durable wording, and the Work Order security-law wording was tightened so a *refused attempt* toward an authenticity-dependent state is not confused with asserting that the state was entered (`M-24-02`).

`evaluatePersistedEvent` behaviour, the version/profile law and every other contract are unchanged by this round.

## Correction record 4 (Context Lock Delta 004)

Independent review `5237592683` (with remediation-bound addendum `5716617080`) accepted the event-history closures of H-22-01 and M-22-02 and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `1` / MEDIUM `1`:

| Finding | Defect | Correction |
|---|---|---|
| `H-23-01` | The declared profile accepted core `major`/`minor`/`patch` identifiers of any length, but `Cargo.toml` is a declared exact mirror and the real consumers bound core components: npm's `node-semver` rejects a core component above `Number.MAX_SAFE_INTEGER`. The drift gate could report `LOCKED` for a canonical and mirrored version that a declared build surface cannot parse. | The profile is now the **intersection** of the declared consumers: each core identifier is bounded to `0..9007199254740991` (npm's `Number.MAX_SAFE_INTEGER`, which is narrower than Cargo's `u64`), while the whole string stays bounded to 128 characters. The bound is applied to the digit strings with exact string logic in both implementations — no float conversion, no platform-dependent integer coercion — so accepted values keep full exactness in ordering. Numeric *prerelease* identifiers remain exact at any length, because no declared consumer imposes a bound there. Oversized-core vectors moved to the rejection set and the 128-character boundary case was rebuilt from legal non-core content. |
| `M-23-02` | Governance prose carried moving current-state claims: DEC-028's promotion table named a specific correction round as the current promotion state, and the Evidence Bundle claimed the head "has not yet been gated or independently reviewed" and `HEDS: NOT YET RUN on any head` while listing completed reviews in the same file; the terminal STOP block was duplicated. | Promotion is stated as a durable requirement (implementation materialised, adversarial coverage, hosted exact-head gates, independent HEDS `0/0`, governed expected-head merge) rather than a round-named status; mutable exact-head evidence is delegated to PR #80 and Issue #30; reviewed heads are recorded as an append-only table of immutable facts; the duplicate STOP block is removed; acceptance rows use durable implementation/evidence semantics. |

The profile narrowing is a deliberate strengthening of an over-broad law, not a weakening: acceptance shrinks and no guard is relaxed. Both declared consumers were re-verified against repository-pinned tooling before the bound was chosen.

## Correction record 3 (Context Lock Delta 003)

Independent review `5237206705` accepted H-21-02 and M-21-03 as materially closed, confirmed that direct `ready`/`installing`/`success` status injection is blocked, and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `1` / MEDIUM `1`:

| Finding | Defect | Correction |
|---|---|---|
| `H-22-01` | The event validator rejected `legal_transition` only when the **destination** was authenticity-dependent, so events whose **source** was authenticity-dependent (`ready -> idle`, `installing -> failure`) were accepted and explicitly asserted as valid history. Such an event asserts the source state previously existed, which in current v1 implies successful traversal of the proof-gated path. | A persisted event whose `from` is `ready`, `installing` or `success` now fails closed for any destination and any reason. The two over-permissive positive expectations were removed and `success -> idle` added as an explicit negative. A refusal attempt *into* an authenticity-dependent state stays recordable only from a reachable source — with the present graph, `verifying -> ready`. |
| `M-22-02` | The validator required a legal structural edge and a reason from the global `TransitionReason` vocabulary but did not prove the outcome was possible for that edge, so an ordinary legal edge could be recorded with `illegal_transition`, `unknown_state` or a proof-refusal reason. | Persisted outcomes are a closed semantic contract: `PERSISTED_EVENT_OUTCOMES` replaces `TransitionReason` on `UpdateEvent`, and `evaluatePersistedEvent(from, to, reason)` is the single reusable law used by `evaluateStatus()` and by tests. Ordinary reachable legal edges record only `legal_transition`; the reachable proof-gated attempt records only the bounded refusal outcomes. Persisting attempted raw input would require a distinct, separately reviewed event type. |

No migration semantics were invented and no separate event contract was introduced; the review's STOP branch was not triggered. No correction weakens a gate, widens authority, admits an authenticity scheme or adds a dependency.

## Correction record 2 (Context Lock Delta 002)

Independent review `5236688350` accepted the first correction round (H-20-02, H-20-03 ordinary own-key closure, H-20-04, M-20-05, M-20-06) and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `2` / MEDIUM `1`:

| Finding | Defect | Correction |
|---|---|---|
| `H-21-01` | `evaluateStatus()` accepted a direct `state:"success"` snapshot with a strictly newer candidate and no proof, although `success` is reachable only from `installing`; recorded events validated only structural edges, so v1 history could report proof-gated transitions as successful without gate evidence. | `ready`, `installing` and `success` are declared **authenticity-dependent states**. Every legal edge entering one is proof-gated, a status snapshot claiming one must carry a proof accepted under current policy (and is therefore invalid while no scheme is admitted), and a history entry may not report a `legal_transition` into one. Refusal events on those edges and all ordinary pre-gate history remain valid, so verification is not globally banned. |
| `H-21-02` | Product TypeScript rejected core identifiers above `Number.MAX_SAFE_INTEGER` that the Python gate accepted, and Python's end-anchored `re.match` accepted a trailing newline that TypeScript rejects: two acceptance sets for one canonical version law. | Core identifiers are exact decimal strings compared by length and lexicographically, with no numeric conversion. The Python gate uses `fullmatch` with explicit ASCII `[0-9]` classes and no anchors. The law is stated as a **bounded SemVer 2.0.0 profile** (128-character maximum) and pinned by `apps/desktop/src/contracts/semverParityVectors.json`, consumed by both suites. A third divergence found while correcting this — Python's `\d` matching Unicode decimal digits — is closed with it. |
| `M-21-03` | `asRecord()` accepted any non-array object and `hasOnlyKeys()` inspected only `Object.keys()`, so required fields could be inherited or getter-backed and reads could execute accessors. | Validation operates only on plain own-data records: no custom prototype or class instance, no accessor-backed property, no non-enumerable or symbol-keyed field, and no sparse or accessor-backed event array. Property values come from own property descriptors, so validation never invokes a getter. Applied to status, error, event and proof objects. |

No correction weakens a gate, widens authority, admits an authenticity scheme or adds a dependency, and no test was weakened, skipped or rewritten to accept the defective behaviour.

## Correction record 1 (Context Lock Delta 001)

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
