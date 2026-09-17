# HCODER-WO-0024 — Acceptance & Security Map

**Status:** IMPLEMENTED IN SOURCE — EXTERNAL PROMOTION EVIDENCE REQUIRED  
**Issue:** `#77`  
**Authority:** `HCODER-WO-0024` Context Lock Deltas `001`–`004`

Required negative proofs are the point of this slice. A row is satisfied only by a
test that fails if the guard is removed.

## How to read this map

The **Implementation** column is a durable statement about the repository, not about
any CI run or review outcome, so it does not change as evidence advances. `IMPLEMENTED`
means the law exists in source with a test written to fail when the guard is removed,
and the suite is green locally. `EXTERNAL` means the row is inherently an evidence
requirement rather than code.

**External promotion evidence is required for every row and is deliberately not encoded
per row**, because a per-row state such as "pending exact-head proof" becomes false the
moment hosted evidence arrives. Green hosted exact-head gates, an independent HEDS
review with unresolved HIGH/CRITICAL `0/0`, and a governed expected-head merge must each
be produced against whichever exact head a promotion decision names; that mutable state
is tracked in PR #80 and Issue #30.

Mutation non-vacuity was performed during the corrections for the guards this Work Order
changed: the authenticity gate edge, status closure and unknown-key rejection, exact
numeric comparison, the single-parser channel law, plain own-data record validation with
zero getter invocation, the persisted-event source rule, the persisted-event
outcome/edge coupling, and the toolchain core bound. In each case the guard was disabled
or the defective behaviour restored, the corresponding tests were observed to fail, and
the guard was restored before commit.

Immutable review history for this Work Order (every one of these heads had green hosted
gates, which is exactly why each finding is preserved rather than superseded):

| Reviewed head | Review | Verdict |
|---|---|---|
| `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d` | `5236275753` | CORRECTION_REQUIRED — CRITICAL `0` / HIGH `4` / MEDIUM `2` |
| `97c533de73c9d8f007b6dfc4eaf73804fb1de220` | `5236688350` | CORRECTION_REQUIRED — CRITICAL `0` / HIGH `2` / MEDIUM `1` |
| `92b6b80fb599b3e2f810b1591b63a68e6b11ddf0` | `5237206705` | CORRECTION_REQUIRED — CRITICAL `0` / HIGH `1` / MEDIUM `1` |
| `a3e585823695f889dae92acc7cc5b57a17ba617d` | `5237592683` + addendum `5716617080` | CORRECTION_REQUIRED — CRITICAL `0` / HIGH `1` / MEDIUM `1` |
| `0ec09d7e0d67018d51ee791a2bbca9f39f41c131` | `5238290797` | CORRECTION_REQUIRED — CRITICAL `0` / HIGH `0` / MEDIUM `2` (documentation-only) |

| # | Property | Test location | Implementation |
|---|---|---|---|
| A1 | Strict SemVer accepted for release, prerelease and build forms | `apps/desktop/src/contracts/version.test.ts`, `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| A2 | Malformed SemVer rejected, never coerced (leading zeros, missing fields, empty identifiers, non-ASCII, oversized, non-string) | same | IMPLEMENTED |
| A3 | SemVer precedence: prerelease below release, numeric-vs-lexical identifiers, shorter prerelease lower, build metadata ignored | `version.test.ts` | IMPLEMENTED |
| A4 | Canonical version present, well formed and mirrored exactly | both | IMPLEMENTED |
| A5 | Missing canonical version fails closed | both | IMPLEMENTED |
| A6 | Malformed canonical version fails closed | both | IMPLEMENTED |
| A7 | Missing mirror version is drift, not silence | both | IMPLEMENTED |
| A8 | Malformed mirror version is distinguished from plain drift | `version.test.ts` | IMPLEMENTED |
| A9 | Mirror drift detected and offending paths named | both | IMPLEMENTED |
| A10 | A newer-but-different mirror is still drift | `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| A11 | Verifier does not mutate manifests | `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| A12 | Manifest reader helpers fail closed on broken JSON/TOML | `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| B1 | Channel vocabulary is exactly `stable`/`beta`/`dev`, stable default | `releaseChannel.test.ts` | IMPLEMENTED |
| B2 | Unknown channel fails closed everywhere | `releaseChannel.test.ts` | IMPLEMENTED |
| B3 | Version shape must match the channel, derived from the canonical strict parser and **not** from a second, looser pattern (`M-20-05`) | `releaseChannel.test.ts` | IMPLEMENTED |
| B4 | Only strictly newer same-channel upgrade is eligible | `releaseChannel.test.ts` | IMPLEMENTED |
| B5 | Downgrade and identical version refused with distinct reasons | `releaseChannel.test.ts` | IMPLEMENTED |
| B6 | Numerically newer but wrong-channel version refused | `releaseChannel.test.ts` | IMPLEMENTED |
| B7 | Cross-channel movement never implicit; explicit intent requires a governed decision | `releaseChannel.test.ts` | IMPLEMENTED |
| C1 | State vocabulary is closed; unknown state fails closed | `updateState.test.ts` | IMPLEMENTED |
| C2 | Only declared transitions are legal | `updateState.test.ts` | IMPLEMENTED |
| C3 | Illegal transitions refused | `updateState.test.ts` | IMPLEMENTED |
| C4 | No cryptographic scheme admitted in this slice | `updateState.test.ts` | IMPLEMENTED |
| C5 | Every edge entering an authenticity-dependent state is refused without an accepted authenticity proof (`H-20-01`, `H-21-01`) | `updateState.test.ts`, `updateService.test.ts` | IMPLEMENTED |
| C6 | Malformed proof refused before any policy question | `updateState.test.ts` | IMPLEMENTED |
| C7 | Error code vocabulary closed; unknown code refused | `updateState.test.ts` | IMPLEMENTED |
| C8 | Oversized error detail refused | `updateState.test.ts` | IMPLEMENTED |
| C9 | Credential-shaped detail refused even when charset-valid | `updateState.test.ts` | IMPLEMENTED |
| C10 | Detail containing URLs, paths, uppercase blobs or control characters refused | `updateState.test.ts` | IMPLEMENTED |
| C11 | Status snapshot closed and bounded: unknown keys refused at top level, in the error object and in **every** event; per-event vocabulary and structural legality; state-dependent candidate and error invariants; canonical reconstruction instead of a cast; direct `ready`/`installing`/`success` snapshots refused; proof-gated successful history refused while pre-gate history stays valid (`H-20-01`, `H-20-03`, `H-21-01`) | `updateState.test.ts` | IMPLEMENTED |
| D1 | Boundary identity fixed | `updateService.test.ts` | IMPLEMENTED |
| D2 | Inert service reports unavailable and never claims readiness | `updateService.test.ts` | IMPLEMENTED |
| D3 | Inert service exposes no mutating/transport/install member | `updateService.test.ts` | IMPLEMENTED |
| D4 | Forbidden-member guard is not vacuous (detects a violating service) | `updateService.test.ts` | IMPLEMENTED |
| D5 | Test-only stand-in cannot be imported by production code | `updateService.test.ts` + security gate | IMPLEMENTED |
| D6 | Invalid configuration fails closed (malformed version, unknown channel, **and** a valid-but-incompatible version/channel pair) (`H-20-02`) | `updateService.test.ts` | IMPLEMENTED |
| E1 | About read model bounded, read-only, no authority surface | `aboutReadModel.test.ts` | IMPLEMENTED |
| E2 | About fails closed on unknown channel, malformed version, invalid status, oversized name, and any version/channel/status identity disagreement (`H-20-02`) | `aboutReadModel.test.ts` | IMPLEMENTED |
| E3 | Updater never reported available in this slice | `aboutReadModel.test.ts` | IMPLEMENTED |
| F1 | Drift verifier imports no network or process module | `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| F2 | `bundle.active` remains `false` | `tools/desktop/security_gate.py` (existing gate) | IMPLEMENTED |
| F3 | No updater plugin, shell, filesystem or process primitive reachable | `tools/desktop/security_gate.py` (existing gate) | IMPLEMENTED |
| G1 | Native contract proof on Windows, Linux and macOS | Governance lanes | EXTERNAL - hosted exact-head gates required |
| G2 | Version drift gate runs in the Desktop Shell lane | `.github/workflows/desktop-shell.yml` | IMPLEMENTED |

## Additional rows carried by Context Lock Delta 001

| # | Property | Test location | Implementation |
|---|---|---|---|
| H1 | Numeric prerelease identifiers compare exactly above `2^53`, and a very long identifier still orders by value (`H-20-04`) | `version.test.ts` | IMPLEMENTED |
| H2 | No later transition into `ready` or `installing` succeeds anywhere in the state vocabulary while the scheme allowlist is empty (`H-20-01`) | `updateState.test.ts` | IMPLEMENTED |
| H3 | A direct `ready`/`installing` status snapshot is refused, with and without proof material (`H-20-01`) | `updateState.test.ts` | IMPLEMENTED |
| H4 | Version and channel are one identity at every boundary that asserts it (`H-20-02`) | `updateState.test.ts`, `updateService.test.ts`, `aboutReadModel.test.ts` | IMPLEMENTED |
| H5 | Transition-reason vocabulary is closed and enumerable | `updateState.test.ts` | IMPLEMENTED |
| H6 | Every declared status key is required; unknown keys are refused at every level | `updateState.test.ts` | IMPLEMENTED |
| H7 | `DEC-028` exists as `PROPOSED / NOT CANONICAL` with a matching ledger entry (`M-20-06`) | `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md`, `docs/project-brain/10-DECISIONS-LEDGER.md` | IMPLEMENTED |

## Additional rows carried by Context Lock Delta 002

| # | Property | Test location | Implementation |
|---|---|---|---|
| I1 | The gated edge set is exactly the set of legal edges whose destination is authenticity-dependent, so no entering edge is left ungated (`H-21-01`) | `updateState.test.ts` | IMPLEMENTED |
| I2 | No transition anywhere in the state vocabulary reaches `ready`, `installing` or `success`, with or without a well-formed but unadmitted proof (`H-21-01`) | `updateState.test.ts` | IMPLEMENTED |
| I3 | A direct `success` status snapshot is refused, with and without proof material (`H-21-01`) | `updateState.test.ts` | IMPLEMENTED |
| I4 | A history entry reporting a `legal_transition` into an authenticity-dependent state is refused, while refusal attempts on `verifying -> ready` and ordinary reachable pre-gate history remain accepted (`H-21-01`) | `updateState.test.ts` | IMPLEMENTED |
| I5 | The product TypeScript parser accepts core identifiers far above `2^53` with no precision loss, and orders them exactly (`H-21-02`) | `version.test.ts` | IMPLEMENTED |
| I6 | Both languages accept and reject exactly the shared parity vector set, including the 128-character boundary (`H-21-02`) | `version.test.ts`, `tests/desktop/test_version_drift.py`, `apps/desktop/src/contracts/semverParityVectors.json` | IMPLEMENTED |
| I7 | The Python gate refuses a trailing LF/CR/CRLF and Unicode line separators, so it can never report `LOCKED` for a version the product parser rejects (`H-21-02`) | `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| I8 | Python refuses Unicode decimal digits inside numeric identifiers, matching the ASCII-only JavaScript parser (`H-21-02`) | `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| I9 | Inherited fields, class instances, custom prototypes, accessor-backed records, non-enumerable fields, symbol keys, and sparse or accessor-backed event arrays are refused at every level (`M-21-03`) | `updateState.test.ts` | IMPLEMENTED |
| I10 | Validation invokes zero getters, proven by an invocation counter, for status, error, event and proof records (`M-21-03`) | `updateState.test.ts` | IMPLEMENTED |

## Additional rows carried by Context Lock Delta 003

| # | Property | Test location | Implementation |
|---|---|---|---|
| J1 | A persisted event whose source is an authenticity-dependent state is refused for every destination and every reason, including the matching refusal reasons (`H-22-01`) | `updateState.test.ts` (`evaluatePersistedEvent`, `evaluateStatus`) | IMPLEMENTED |
| J2 | `ready -> idle`, `ready -> failure`, `installing -> failure` and `success -> idle` recorded as `legal_transition` are all refused (`H-22-01`) | `updateState.test.ts` | IMPLEMENTED |
| J3 | The only reachable proof-gated attempt, `verifying -> ready`, accepts exactly the bounded refusal outcomes and refuses `legal_transition` (`M-22-02`) | `updateState.test.ts` | IMPLEMENTED |
| J4 | An ordinary reachable legal edge accepts only `legal_transition` and refuses `authenticity_proof_required`, `malformed_authenticity_proof`, `illegal_transition` and `unknown_state` (`M-22-02`) | `updateState.test.ts` | IMPLEMENTED |
| J5 | `UpdateEvent.reason` uses the closed persisted vocabulary, which is strictly narrower than `TransitionReason` and whose non-success members are exactly the bounded refusal outcomes (`M-22-02`) | `updateState.test.ts` | IMPLEMENTED |
| J6 | `evaluatePersistedEvent` reports distinct rejection reasons (`unknown_state`, `unreachable_source_state`, `undeclared_edge`, `inadmissible_outcome`) and is the single law reused by `evaluateStatus` (`M-22-02`) | `updateState.test.ts` | IMPLEMENTED |
| J7 | Non-vacuity: removing the unreachable-source guard or the outcome-coupling guard makes the new tests fail (verified by mutation during the correction) | `updateState.test.ts` | IMPLEMENTED |
| J8 | No migration or legacy-event semantics exist; a record from another contract version is out of scope for v1 and would STOP for a versioned design | Work Order / DEC-028 (contract statement) | IMPLEMENTED |

## Additional rows carried by Context Lock Delta 004

| # | Property | Test location | Implementation |
|---|---|---|---|
| K1 | Every core identifier is bounded to `0..9007199254740991`, in every core position (`H-23-01`) | `version.test.ts`, `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| K2 | Core values only a wider consumer would accept — `u64::MAX`, `u64::MAX+1`, 30-digit cores and the former oversized-core boundary — are refused (`H-23-01`) | same | IMPLEMENTED |
| K3 | Accepted core values order exactly with no precision collapse, and beyond-bound values fail precedence closed (`H-23-01`) | `version.test.ts` | IMPLEMENTED |
| K4 | The core bound is exact string logic, independent of platform integer width, with no integer or float coercion (`H-23-01`) | `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| K5 | Numeric prerelease identifiers are not core-bounded and stay exact at any length within the string bound (`H-23-01`, `H-20-04`) | `version.test.ts`, `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| K6 | The 128-character profile boundary is exercised with legal non-core content, and 129 characters is refused (`H-23-01`) | `version.test.ts`, `tests/desktop/test_version_drift.py` | IMPLEMENTED |
| K7 | Cross-language acceptance parity covers the core boundaries, u64 boundaries and the rebuilt length boundary through the shared vector file (`H-23-01`) | both suites reading `semverParityVectors.json` | IMPLEMENTED |
| K8 | Non-vacuity: relaxing the core bound makes a `MAX_SAFE+1` regression fail | verified by mutation during the correction | IMPLEMENTED |

## Security invariants this slice must not weaken
The existing `tools/desktop/security_gate.py` assertions — zero frontend invokes
beyond the three governed commands, zero capability permissions, `desktop-read-only`
scope, zero filesystem mutation primitives, zero generic process execution, one
fixed runtime sidecar process, zero Apple-specific font references, committed
lockfiles — must remain unchanged and passing. The gate runs before `npm ci` in the
Desktop Shell lane, so a local run against an installed `node_modules` tree is not
the gate's CI condition.

## STOP
Any row that cannot be satisfied without distribution authority, an updater
dependency or a weakened gate is a STOP condition, not an implementation task.
`IMPLEMENTED` is not a promotion claim: promotion requires the external evidence
described above against the exact promotion head, and no merge, `DEC-028` canonicalisation
or successor distribution slice is authorised by this map.
