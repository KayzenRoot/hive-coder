# HCODER-WO-0024 — Prebuilt Implementation Pack

**Status:** IMPLEMENTED / THIRD CORRECTION REVIEW PENDING — three independent reviews returned CORRECTION_REQUIRED on the prebuild head `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d` (`5236275753`, CRITICAL `0` / HIGH `4` / MEDIUM `2`), the first correction head `97c533de73c9d8f007b6dfc4eaf73804fb1de220` (`5236688350`, CRITICAL `0` / HIGH `2` / MEDIUM `1`) and the second correction head `92b6b80fb599b3e2f810b1591b63a68e6b11ddf0` (`5237206705`, CRITICAL `0` / HIGH `1` / MEDIUM `1`). All three correction rounds are carried in source under Context Lock Deltas `001`–`003`; their exact-head proof is pending.  
**Base:** `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Issue:** `#77`

## Mission
Complete the distribution contracts of HCODER-DIST-001A so later distribution slices are completion-oriented: one canonical version law with deterministic mirrors, a fail-closed release-channel contract, a bounded update-state model with a mandatory authenticity gate, and a Hive-owned `UpdateService` boundary whose production implementation remains inert.

## Fixed contract identities
```text
VERSION_CONTRACT            = "hive-version-v1"
CHANNEL_CONTRACT            = "hive-release-channel-v1"
UPDATE_STATE_CONTRACT       = "hive-update-state-v1"
ABOUT_READ_MODEL_SCHEMA     = "hive-about-v1"
UPDATE_SERVICE_BOUNDARY     = "hive-update-service-v1"
CANONICAL_VERSION_SOURCE    = "apps/desktop/src-tauri/tauri.conf.json"
```

## Canonical version law
- Canonical source: `tauri.conf.json` → `version`.
- Mirrors: `Cargo.toml` `[package].version`, `package.json` `version`.
- A mirror is correct only when it parses as SemVer under the bounded profile **and** equals the canonical value exactly.
- The declared profile is **bounded SemVer 2.0.0**: the SemVer 2.0.0 grammar restricted to version strings of at most 128 characters. The bound is part of the law and is enforced identically by the product TypeScript parser and the Python drift gate.
- Core identifiers (`major`/`minor`/`patch`) and numeric prerelease identifiers are arbitrary-precision integers: they are carried as exact decimal strings and compared by digit length then lexicographically. No `Number()`/float conversion and no safe-integer rejection, which would otherwise split the acceptance set across languages.
- The product parser and the Python gate share one acceptance set, pinned by `apps/desktop/src/contracts/semverParityVectors.json`, which both suites read. The Python gate matches with `fullmatch`, uses explicit ASCII `[0-9]` classes and carries no end anchor, so a trailing newline or a Unicode decimal digit cannot be accepted there while the product parser rejects it.
- Malformed canonical or mirror versions fail closed and are reported by path.
- The verifier is offline, read-only, deterministic and reports `sideEffects: NONE`.

## Release-channel law
- Channels: `stable`, `beta`, `dev`. `dev` carries the product label `dev/internal`.
- Stable is the default production channel.
- Version shape must match the channel: stable admits no prerelease; `beta`/`dev` admit only a first prerelease identifier equal to their prefix.
- The shape test derives exclusively from the canonical strict SemVer parser. A second, looser pattern here would admit versions the strict contract refuses, such as `1.0.0-beta.`.
- Only a strictly newer same-channel version is eligible.
- Downgrade, identical version and malformed versions are refused with distinct reasons.
- Cross-channel movement is never implicit: even explicit intent reports `requiresGovernedDecision`.

## Update-state law
```text
idle -> checking
checking -> available | unavailable | failure | idle
available -> downloading | idle | failure
downloading -> verifying | failure
verifying -> ready | failure
ready -> installing | idle | failure
installing -> success | failure
success -> idle
failure -> idle
unavailable -> idle
```
- Unknown states and undeclared transitions fail closed.
- `ready`, `installing` and `success` are **authenticity-dependent states**: `success` is reachable only from `installing`, so asserting any of them asserts that a verified proof was acted on. Every legal edge entering one — `verifying -> ready`, `ready -> installing`, `installing -> success` — is authenticity-gated in `evaluateTransition`, and a test asserts that the gated set is exactly the set of legal edges whose destination is authenticity-dependent.
- A status snapshot claiming an authenticity-dependent state must carry a proof accepted under the same policy. Because no scheme is admitted, the whole install path is unreachable and unassertable in this slice.
- **Persisted history is semantically closed.** `evaluatePersistedEvent(from, to, reason)` is the single law for recorded entries: `from`/`to` must be declared states, `from` must not be authenticity-dependent (such a state cannot have been entered, so it can be neither source nor destination of a success), the edge must be declared legal, and the outcome must be one that edge could have produced.
- `UpdateEvent.reason` uses the bounded persisted vocabulary `PERSISTED_EVENT_OUTCOMES`, not the live `TransitionReason` vocabulary. `illegal_transition` and `unknown_state` cannot ride on a validated legal edge: they describe a live evaluation of raw input, and persisting attempted raw input would need a distinct, separately reviewed event type.
- An ordinary reachable legal edge records only `legal_transition`. The one reachable proof-gated attempt, `verifying -> ready`, records only `authenticity_proof_required` or `malformed_authenticity_proof`; `legal_transition` there is inadmissible while no scheme is admitted.
- One current version and one current channel form a single identity: a valid-but-incompatible pair fails closed at service construction, in status validation (for both the current and the candidate version) and in the About read model.
- A status snapshot is a closed object: exact key sets at the top level, in the error object and in every event; per-event vocabulary and structural legality; state-dependent candidate (`required` / `forbidden` / either) and error invariants; a maximum event count. It is validated and then **reconstructed** from validated fields — never returned as the caller's object cast to `UpdateStatus`.
- Validation reads **plain own-data records only**: no custom prototype or class instance, no accessor-backed property, no non-enumerable or symbol-keyed field, no sparse or accessor-backed event array. Values come from own property descriptors, so validation never executes a getter. The rule applies to status, error, event and proof objects.
- Numeric identifiers compare exactly, by digit length then lexicographically, for core identifiers and prerelease identifiers alike.
- Error metadata is a closed code vocabulary plus bounded detail drawn from a narrow charset and free of credential shapes.

## UpdateService boundary
- Product code depends on the `UpdateService` interface, never on an updater plugin or endpoint.
- The production implementation is `InertUpdateService`: it reports version, channel, availability and status, and evaluates pure contract law. It exposes **no** mutating, transport or installation member.
- `FORBIDDEN_UPDATE_SERVICE_MEMBERS` and `exposesForbiddenMember` make the boundary property testable rather than stylistic.
- Any test-only stand-in must live inside a test file so it cannot be imported by production code.

## Settings/About read model
- Bounded, read-only, UI-framework-free; carries version, channel label and update status.
- No update trigger, no background check, no notification centre, no redesign.
- Compatible with later UX/i18n work without expanding into Issue #71.

## Backend selection gate
None. This slice adds no dependency. If completing it appears to require an updater plugin, an HTTP client or any distribution dependency, the slice is out of scope and must STOP for a governed decision.

## Hive Harness execution laws
- **Capability Budget:** zero new authority. Any request outside it stops rather than escalating.
- **Mutation Budget:** the allowed-file set in the Context Lock, and nothing else.
- **Proof-Carrying Action:** every contract claim must be an executable test, not prose.
- **Counterfactual Gate:** promotion requires evidence that malformed, unknown, drifted, replayed, downgraded, cross-channel and proof-less variants fail, not merely that the happy path passes.
- **Uncertainty Ledger:** unresolved assumptions are explicit gates and never silently become implementation facts.

- Refusal attempts on `verifying -> ready`, failure edges such as `verifying -> failure`, and all ordinary reachable pre-gate history remain valid: verification is not globally banned, and history may record a refused attempt.

## Tests before promotion
Contract tests must cover: SemVer acceptance and rejection under the bounded profile; exact numeric comparison for core and prerelease identifiers above `2^53`; cross-language parity vectors consumed by both the TypeScript and Python suites (huge core values, huge prerelease values, malformed forms, trailing LF/CR/CRLF and Unicode line separators, non-ASCII and Unicode-digit content, the 128-character boundary); canonical/mirror drift, missing and malformed mirrors; channel vocabulary and unknown-channel refusal; version-shape/channel matching derived from the single canonical parser; same-channel upgrade eligibility; downgrade, identical-version and prerelease-mismatch refusal; cross-channel refusal with governed-decision reporting; the full transition table including illegal transitions; proof-gated refusal on every edge entering an authenticity-dependent state; exhaustive unreachability of `ready`, `installing` and `success` as transition destinations; malformed proof refusal; bounded and credential-shaped error-detail refusal; status closure (unknown keys at every level, per-event validation, required keys, candidate and error invariants, canonical reconstruction); refusal of direct authenticity-dependent snapshots; the persisted-event matrix (unreachable source states rejected for every destination and reason, `verifying -> ready` accepted only with the bounded refusal outcomes, ordinary edges accepted only with `legal_transition`, `illegal_transition`/`unknown_state` refused on persisted events); plain own-data record validation (inherited fields, class instances, accessor-backed records, non-enumerable and symbol keys, sparse and accessor-backed arrays) with a proven zero getter-invocation count; version/channel identity at every boundary; inert-boundary member absence; and absence of any network/process/update side-effect surface.

Native proof runs independently on Windows, Linux and macOS. Platform skips cannot promote that platform.

## Evidence required
Exact head, workflow/run/job IDs, runner OS/version/architecture, focused test counts with zero implementation skips, drift-gate output against live manifests, explicit confirmation that `bundle.active` remains `false` and that no updater/download/install/signing/release path exists, and HEDS HIGH/CRITICAL `0/0`.

## STOP
No updater activation, network, download, install, restart, signing, notarization, release publication, dependency addition, `bundle.active=true`, or weakening of an existing HIGH_ASSURANCE gate.
