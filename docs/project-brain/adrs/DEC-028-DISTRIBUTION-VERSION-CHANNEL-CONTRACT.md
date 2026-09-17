# DEC-028 — Distribution Version And Release-Channel Contract

**Status:** PROPOSED / NOT CANONICAL  
**Work Order:** `HCODER-WO-0024`  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Reviews of this proposal:** `5236275753` — CORRECTION_REQUIRED (CRITICAL `0` / HIGH `4` / MEDIUM `2`) at prebuild head `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`; `5236688350` — CORRECTION_REQUIRED (CRITICAL `0` / HIGH `2` / MEDIUM `1`) at correction head `97c533de73c9d8f007b6dfc4eaf73804fb1de220`; `5237206705` — CORRECTION_REQUIRED (CRITICAL `0` / HIGH `1` / MEDIUM `1`) at correction head `92b6b80fb599b3e2f810b1591b63a68e6b11ddf0`  
**Materialised under:** `HCODER-WO-0024` Context Lock Delta 001 (proposal), Delta 002 (second correction) and Delta 003 (third correction)

> **State record.** This ADR is a **proposal**. It records a durable law that `HCODER-WO-0024` is establishing and has no canonical standing. It grants no authority, admits no updater, and is not evidence that Hive Coder is installable, signed, auto-updatable or production-distributable. It becomes canonical only through the promotion gate below, and only with an independent review that reports unresolved HIGH/CRITICAL `0/0`.

## Context

Hive Coder's product version lives in three manifests (`apps/desktop/src-tauri/tauri.conf.json`, `apps/desktop/src-tauri/Cargo.toml`, `apps/desktop/package.json`) with no stated precedence and no machine-checked agreement. There is no release-channel concept, no update-lifecycle model and no Hive-owned boundary behind which a future updater could be implemented.

A distribution/update capability cannot be reasoned about safely on top of that: a version identity that three files may independently disagree about, and a "newer" test that is not exact, are exactly the preconditions that make an unsafe upgrade possible. The law therefore has to be fixed before any distribution behaviour exists, and it must be fixed in a form that a later governed slice cannot quietly weaken.

## Decision candidate

**1. One canonical version source.** The shipped product version has exactly one source of truth: `apps/desktop/src-tauri/tauri.conf.json` → `version`. The Tauri application version identifies the shipped artifact and is the value a future updater compares against. The Rust package version and the npm package version are *mirrors*: they must equal the canonical value exactly and must never be edited independently. A tool-enforced drift gate fails the build when a mirror is missing, malformed or divergent.

**2. One bounded SemVer 2.0.0 acceptance set, shared by every implementation.** Versions are parsed by one strict parser that fails closed on anything it cannot accept; nothing is trimmed, coerced or partially accepted. Because there is no single SemVer library that both the product TypeScript and the Python build gates can share, the law is stated as a **bounded SemVer 2.0.0 profile**: exactly the SemVer 2.0.0 grammar, restricted to version strings of at most 128 characters. The bound is part of the law rather than an implementation detail, and both implementations enforce it identically.

Precedence follows SemVer 2.0.0 exactly, including the rule that numeric identifiers compare by value. A SemVer numeric identifier — whether a core `major`/`minor`/`patch` value or a numeric prerelease identifier — is an arbitrary-precision integer, not a machine integer. Numeric comparison is therefore performed exactly, by digit-length and lexicographic comparison, and never through floating-point conversion: `Number()` / `parseFloat` would collapse distinct identifiers above `2^53` into one value and produce a wrong "newer" answer, and a safe-integer rejection would silently split the acceptance set in two.

One acceptance set means the product parser and the Python drift gate must agree on every input, so acceptance is pinned by a deterministic vector file consumed by both test suites. The drift gate may never report `LOCKED` for a version the product parser rejects, and the product parser may never accept a version the gate rejects — including trailing line terminators, which a naive end-anchored match on the Python side would accept, and Unicode decimal digits, which Python's `\d` matches and JavaScript's does not.

**3. Channel is a shape of version, and version+channel is one identity.** A release channel is one of `stable`, `beta`, `dev` (product label `dev/internal`). `stable` versions carry no prerelease component; `beta` and `dev` versions carry the channel's name as their first prerelease identifier. A version and a channel are a single identity: a pair that is individually valid but mutually incompatible (`0.1.0` on `beta`, `0.1.0-beta.1` on `stable`) is rejected wherever the identity is asserted — service construction, status snapshots and the read model — rather than being half-validated field by field. Channel membership is a *shape* test derived from the same strict parser; it is not a promotion authorisation, and this contract admits no implicit cross-channel promotion or demotion and no silent downgrade.

**4. The update lifecycle is a closed state machine whose whole install path is authenticity-gated.** The lifecycle states and the legal transitions are declared exactly; anything else fails closed. `ready` is install-ready, `installing` is downstream of it, and `success` is reachable only from `installing`: all three are **authenticity-dependent states**, and asserting any of them asserts that an authenticity proof was verified and acted on. A transition entering one of them requires an accepted proof, a status snapshot claiming one must carry a proof accepted under the same policy, and a recorded history entry may neither report a successful traversal of that path nor name one of those states as its source.

Cryptographic schemes are admitted by an explicit allowlist that is **empty** in this slice, so no proof can be accepted and the entire install path is unreachable by construction rather than by convention. Refusal attempts into those states remain recordable from a reachable source, and history that does not touch the gated path remains valid, so the rule restricts the claim without banning the record.

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
7. Every authenticity-dependent state requires an accepted authenticity proof, including in a status snapshot or a recorded history entry, and no scheme is admitted in this slice.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.
9. The inert boundary exposes no mutating, transport or installation member.
10. Validation reads only plain own-data records; no inherited field and no accessor is ever trusted, and no getter is ever executed by validation.

## Promotion gate

`DEC-028` remains **PROPOSED / NOT CANONICAL**. It may be promoted only when all of the following hold and are recorded against an exact head:

| Condition | Status |
|---|---|
| Contract law implemented and materialised | PENDING independent review of the second corrected head |
| Executable contract/security tests prove every property above, including the adversarial cases and the cross-language parity vectors | PENDING independent review of the second corrected head |
| Exact-head Governance and Desktop Shell green on the promotion head | PENDING |
| Independent HEDS with unresolved HIGH/CRITICAL `0/0` | PENDING |
| Governed merge with expected-head protection | PENDING |

Until every condition is met, no promotion claim may be made for this decision, for `HCODER-WO-0024`, or for Hive Coder's distribution or update capability.

## Recorded review history

The first implementation head of `HCODER-WO-0024` (`4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`, gates green) was independently reviewed as `5236275753` and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `4` / MEDIUM `2`: the authenticity gate sat on the install call instead of the install-ready boundary; version and channel were validated independently rather than as one identity; status snapshots were neither closed nor reconstructed; numeric prerelease precedence used floating-point conversion; the channel contract carried a second, looser version parser; and this ADR was referenced without existing. The corrections were carried in the same Work Order under Context Lock Delta 001.

The correction head `97c533de73c9d8f007b6dfc4eaf73804fb1de220` (Governance `35229265839` SUCCESS, Desktop Shell `35229265814` SUCCESS) was independently reviewed as `5236688350` and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `2` / MEDIUM `1`: `status:"success"` was still accepted as a direct snapshot although it is reachable only through the proof-gated install path, recorded history could still report a proof-gated transition as successful without carrying gate evidence, the product TypeScript parser and the Python drift gate had different acceptance sets for core identifier magnitude and for trailing line terminators, and exact-object validation accepted inherited and accessor-backed fields. The corrections are carried in the same Work Order under Context Lock Delta 002, which also records a parity defect found while correcting the second finding (Python's `\d` matching Unicode decimal digits).

The second correction head `92b6b80fb599b3e2f810b1591b63a68e6b11ddf0` (Governance `35232341418` SUCCESS, Desktop Shell `35232341386` SUCCESS) was independently reviewed as `5237206705` and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `1` / MEDIUM `1`: history could still assert an authenticity-dependent *source* state — `ready -> idle` and `installing -> failure` were accepted and asserted as valid — and an event's reason was not proven possible for its edge, so an ordinary legal edge could carry a refusal or live-evaluation reason. The corrections are carried in the same Work Order under Context Lock Delta 003.

All three review histories are preserved here rather than rewritten: those heads were real, their gates were green, and green gates did not mean the properties held.
