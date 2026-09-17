# DEC-028 — Distribution Version And Release-Channel Contract

**Status:** CANONICAL / SEALED under `HCODER-CP-0024` — **effective under `HCODER_CP_0024_EFFECTIVE`; non-canonical while that predicate is unsatisfied**  
**Work Order:** `HCODER-WO-0024` — product implementation MERGED / POSTVALIDATED  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Product merge (immutable lifecycle-stage fact):** `c7f2a5f21369fd92b3493bea0be0192bbd7298b4` — PR #80, squash with expected-head protection; merge tree `99151781a7cd4a886bf0ea43bb9e29ca44b16cb1` identical to the reviewed-head tree  
**Promotion evidence:** `.engineering/evidence/HCODER-CP-0024-CANONICAL-CLOSEOUT.md`  
**Reviews of this proposal:** prior reviewed-head facts are historical and recorded in the review-history section below and in `.engineering/evidence/HCODER-WO-0024.md`; they are not mirrored here as a current index. Mutable current review and gate state is external in the active closeout PR and Issues #30 and #77.  
**Materialised under:** `HCODER-WO-0024` — the canonical append-only delta history for this Work Order lives in `.engineering/context-locks/HCODER-WO-0024.md`, and no terminal delta number or range is mirrored here.

> **Conditional effectiveness (must not be misread).** This ADR declares the CANONICAL / SEALED state of `DEC-028` under `HCODER-CP-0024`. That state is **effective if and only if** `HCODER_CP_0024_EFFECTIVE` holds: for one and the same closeout revision, (a) the exact revision was independently reviewed with unresolved HIGH/CRITICAL `0/0`; (b) it was governed-merged with expected-head protection; and (c) the resulting exact `main` SHA passed fresh Governance and Desktop Shell. **While the predicate is unsatisfied**, `DEC-028` is non-canonical and `HCODER-CP-0023` remains the authoritative checkpoint. The predicate depends on no merge SHA, run ID, review ID, Issue state, PR state or moving `current main` field; evidence of whether it holds lives externally in the active closeout PR and Issues #30 and #77. This ADR grants no authority, admits no updater, and is not evidence that Hive Coder is installable, signed, auto-updatable or production-distributable.

## Context

Hive Coder's product version lives in three manifests (`apps/desktop/src-tauri/tauri.conf.json`, `apps/desktop/src-tauri/Cargo.toml`, `apps/desktop/package.json`) with no stated precedence and no machine-checked agreement. There is no release-channel concept, no update-lifecycle model and no Hive-owned boundary behind which a future updater could be implemented.

A distribution/update capability cannot be reasoned about safely on top of that: a version identity that three files may independently disagree about, and a "newer" test that is not exact, are exactly the preconditions that make an unsafe upgrade possible. The law therefore has to be fixed before any distribution behaviour exists, and it must be fixed in a form that a later governed slice cannot quietly weaken.

## Decision candidate

**1. One canonical version source.** The shipped product version has exactly one source of truth: `apps/desktop/src-tauri/tauri.conf.json` → `version`. The Tauri application version identifies the shipped artifact and is the value a future updater compares against. The Rust package version and the npm package version are *mirrors*: they must equal the canonical value exactly and must never be edited independently. A tool-enforced drift gate fails the build when a mirror is missing, malformed or divergent.

**2. One toolchain-compatible bounded SemVer 2.0.0 acceptance set, shared by every implementation.** Versions are parsed by one strict parser that fails closed on anything it cannot accept; nothing is trimmed, coerced or partially accepted. Because there is no single SemVer library that both the product TypeScript and the Python build gates can share, the law is stated as a **bounded SemVer 2.0.0 profile** with two explicit project bounds:

- each core identifier (`major`, `minor`, `patch`) must lie in `0..9007199254740991`, and
- the whole version string must be at most 128 characters.

The core bound is a real toolchain constraint rather than a stylistic choice. The canonical version is mirrored into `Cargo.toml` and `package.json`, and the two consumers do not agree on range: Cargo's Rust SemVer accepts core values up to `u64::MAX`, while npm's `node-semver` rejects a core component above JavaScript's `Number.MAX_SAFE_INTEGER`. The profile is the **intersection** of every declared consumer, so it follows the narrower one — a version this product accepts must be a version every mirror can parse. Both bounds are part of the law, are enforced identically by both implementations, and are pinned by a shared vector file.

Precedence follows SemVer 2.0.0 exactly, including the rule that numeric identifiers compare by value. Numeric identifiers are carried as exact decimal strings and compared by digit-length and lexicographic comparison — never through floating-point conversion, which would collapse distinct identifiers above `2^53` into one value, and never through platform integer coercion, which would make the bound platform-dependent. The core bound is applied to the digit strings themselves, so accepted values keep full exactness. Numeric *prerelease* identifiers are deliberately not subject to the core bound: no declared consumer imposes a lower bound there, so they remain exact at any length within the overall string bound.

One acceptance set means the product parser and the Python drift gate must agree on every input, so acceptance is pinned by a deterministic vector file consumed by both test suites. The drift gate may never report `LOCKED` for a version the product parser rejects, and the product parser may never accept a version the gate rejects — including trailing line terminators, which a naive end-anchored match on the Python side would accept, and Unicode decimal digits, which Python's `\d` matches and JavaScript's does not.

**3. Channel is a shape of version, and version+channel is one identity.** A release channel is one of `stable`, `beta`, `dev` (product label `dev/internal`). `stable` versions carry no prerelease component; `beta` and `dev` versions carry the channel's name as their first prerelease identifier. A version and a channel are a single identity: a pair that is individually valid but mutually incompatible (`0.1.0` on `beta`, `0.1.0-beta.1` on `stable`) is rejected wherever the identity is asserted — service construction, status snapshots and the read model — rather than being half-validated field by field. Channel membership is a *shape* test derived from the same strict parser; it is not a promotion authorisation, and this contract admits no implicit cross-channel promotion or demotion and no silent downgrade.

**4. The update lifecycle is a closed state machine whose whole install path is authenticity-gated.** The lifecycle states and the legal transitions are declared exactly; anything else fails closed. `ready` is install-ready, `installing` is downstream of it, and `success` is reachable only from `installing`: all three are **authenticity-dependent states**, and asserting any of them asserts that an authenticity proof was verified and acted on. A transition entering one of them requires an accepted proof, and a status snapshot claiming one must carry a proof accepted under the same policy.

Recorded history carries the same rule in the precise form the event shape allows: while no scheme is admitted, an authenticity-dependent state cannot be an event's **source**, and no event may claim **successful entry** into one. A *refused attempt* toward `ready` from a reachable source — `verifying -> ready` — remains recordable with the bounded proof-refusal outcomes, because it asserts only that an attempt was made and refused: naming an attempted destination is not a claim that the state was entered, or that it ever existed as a current state.

Cryptographic schemes are admitted by an explicit allowlist that is **empty** in this slice, so no proof can be accepted and no authenticity-dependent state can actually be entered, rather than merely being discouraged by convention. Ordinary history that does not touch the gated path remains valid, and a refused attempt on it is recordable, so the rule restricts the claim without banning the record.

**5. Status snapshots are closed, plain-data objects.** A status snapshot has an exact key set at the top level, inside its error object and inside every recorded event; unknown keys are refused rather than ignored, unknown states, channels, error codes and event outcomes are refused, events are validated individually by the persisted-event law below and by a maximum count, and the candidate version is constrained by state (`required`, `forbidden`, or either) and must be a strictly newer version belonging to the same channel.

Validation operates only on plain own-data records. A required field that is inherited through a custom prototype or a class instance, or that is backed by an accessor, is refused before any application field is read, and property values are taken from own property descriptors so that no getter is ever invoked by validation. The same rule applies to nested error, event and authenticity-proof objects. A validated snapshot is *reconstructed* from validated fields; the untrusted input object is never cast and returned, so an unvalidated property cannot ride into product state.

**6. Persisted history is semantically closed.** A recorded history entry is evidence, so it must be an assertion this contract could actually have produced. The persisted-event law requires declared states, a source state that current v1 can reach, a declared legal edge, and an outcome that edge could actually have yielded. Persisted outcomes are their own bounded vocabulary, deliberately narrower than the live transition vocabulary: `illegal_transition` and `unknown_state` describe a live evaluation of raw input that a validated `from`/`to` pair cannot represent, so an ordinary reachable legal edge records only `legal_transition` and the one reachable proof-gated attempt records only the bounded refusal outcomes. Persisting attempted raw input would require a distinct, separately reviewed event type rather than an overload of this one.

**7. The updater is behind a Hive-owned boundary and is inert.** Product code depends on an `UpdateService` interface, never on an updater plugin, endpoint, HTTP client or installer. The production implementation in this slice reports configuration, evaluates contract law and does nothing else: it exposes no check, download, install, restart, signing, publication or mutation member, and its availability is always reported as unavailable.

## Non-decision

This ADR does not approve, and does not create authority for: a Tauri updater plugin or any update transport; an updater endpoint, HTTP client, download, artifact fetch or metadata fetch; installation, restart or process execution; signing, key access, notarization or store submission; release/tag creation or artifact publication; `bundle.active=true`; any new dependency; any filesystem, Git, shell, Cua, credential or provider authority; and any change to the Permission & Control Plane. It establishes no claim about platforms on which the product is installable, and no release-readiness claim of any kind.

## Security law carried by this proposal

1. Default deny; the contract adds no authority.
2. Update metadata and artifacts are untrusted until a later governed slice proves verification; HTTPS is never authenticity proof.
3. No model, tool or backend may mint release or update authority.
4. Signing material never enters repository, logs, prompts or runtime state.
5. Version, channel and state parsing fail closed on malformed or unknown input.
6. No silent downgrade; no implicit cross-channel promotion or demotion.
7. An authenticity-dependent state requires an accepted authenticity proof to be **entered**, and no scheme is admitted in this slice. Concretely: a legal transition that would actually enter `ready`, `installing` or `success` requires accepted proof; such a state cannot be asserted as a current status; it cannot be a persisted event source; and a persisted event cannot claim successful entry into it. A *refused attempt* toward `ready` from a reachable source is recordable with the bounded refusal outcomes, and records a refusal rather than asserting that the state was entered.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.
9. The inert boundary exposes no mutating, transport or installation member.
10. Validation reads only plain own-data records; no inherited field and no accessor is ever trusted, and no getter is ever executed by validation.

## Promotion gate

`DEC-028` is declared **CANONICAL / SEALED** under `HCODER-CP-0024`, effective under `HCODER_CP_0024_EFFECTIVE` and non-canonical while that predicate is unsatisfied. Promotion is a durable gate rather than a statement about any particular head: it requires all of the following, and evidence for each must be produced against whatever exact head the promotion decision names.

| Condition | Requirement | Product-stage status |
|---|---|---|
| Contract law materialised | The law above exists in source as executable contract code, with tests that fail when a guard is removed | MET at the reviewed product head |
| Adversarial coverage | The negative and adversarial proofs listed in the Work Order's acceptance map are implemented and green | MET at the reviewed product head |
| Hosted exact-head gates | Governance and Desktop Shell are green on the exact promotion head | MET at the reviewed product head and again on the exact product merge `main` |
| Independent review | An independent HEDS review of that exact head reports unresolved HIGH/CRITICAL `0/0` | MET at the product stage — `5239135676`, APPROVED FOR GOVERNED MERGE, CRITICAL `0` / HIGH `0` / MEDIUM `0`; the closeout stage requires its own review of its own exact revision |
| Governed merge | The Work Order merges with expected-head protection | Product merge MET (`c7f2a5f21369fd92b3493bea0be0192bbd7298b4`, PR #80); the closeout stage requires its own governed merge of its own exact revision |

Whether the closeout stage's conditions are currently met is external state, recorded in the active closeout PR and Issues #30 and #77 rather than in this document; this ADR states only the requirement and the conditional outcome, so it remains true as that state advances. The historical reviewed-head record is below.

## Recorded review history

The first implementation head of `HCODER-WO-0024` (`4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`, gates green) was independently reviewed as `5236275753` and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `4` / MEDIUM `2`: the authenticity gate sat on the install call instead of the install-ready boundary; version and channel were validated independently rather than as one identity; status snapshots were neither closed nor reconstructed; numeric prerelease precedence used floating-point conversion; the channel contract carried a second, looser version parser; and this ADR was referenced without existing. The corrections were carried in the same Work Order under Context Lock Delta 001.

The correction head `97c533de73c9d8f007b6dfc4eaf73804fb1de220` (Governance `35229265839` SUCCESS, Desktop Shell `35229265814` SUCCESS) was independently reviewed as `5236688350` and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `2` / MEDIUM `1`: `status:"success"` was still accepted as a direct snapshot although it is reachable only through the proof-gated install path, recorded history could still report a proof-gated transition as successful without carrying gate evidence, the product TypeScript parser and the Python drift gate had different acceptance sets for core identifier magnitude and for trailing line terminators, and exact-object validation accepted inherited and accessor-backed fields. The corrections are carried in the same Work Order under Context Lock Delta 002, which also records a parity defect found while correcting the second finding (Python's `\d` matching Unicode decimal digits).

The second correction head `92b6b80fb599b3e2f810b1591b63a68e6b11ddf0` (Governance `35232341418` SUCCESS, Desktop Shell `35232341386` SUCCESS) was independently reviewed as `5237206705` and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `1` / MEDIUM `1`: history could still assert an authenticity-dependent *source* state — `ready -> idle` and `installing -> failure` were accepted and asserted as valid — and an event's reason was not proven possible for its edge, so an ordinary legal edge could carry a refusal or live-evaluation reason. The corrections are carried in the same Work Order under Context Lock Delta 003.

The third correction head `a3e585823695f889dae92acc7cc5b57a17ba617d` (Governance `35236042240` SUCCESS, Desktop Shell `35236042371` SUCCESS) was independently reviewed as `5237592683`, returning `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `1` / MEDIUM `1`: the declared profile accepted core identifiers that npm's `node-semver` refuses, so the gate could report `LOCKED` for a canonical/mirrored version a declared build surface cannot parse, and governance prose still contained moving current-state claims. The review's remediation-bound addendum `5716617080` refined the required bound from `u64::MAX` to `Number.MAX_SAFE_INTEGER`, the narrower of the two declared consumers. The correction is carried in the same Work Order under Context Lock Delta 004.

All four review histories are preserved here rather than rewritten: those heads were real, their gates were green, and green gates did not mean the properties held.
