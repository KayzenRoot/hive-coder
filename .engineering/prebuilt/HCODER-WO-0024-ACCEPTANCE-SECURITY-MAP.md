# HCODER-WO-0024 — Acceptance & Security Map

**Status:** IMPLEMENTED / SECOND CORRECTION REVIEW PENDING — rows marked `MATERIALISED` were **withdrawn to PENDING** by reviews `5236275753` (CRITICAL `0` / HIGH `4` / MEDIUM `2`) and `5236688350` (CRITICAL `0` / HIGH `2` / MEDIUM `1`)  
**Issue:** `#77`

Required negative proofs are the point of this slice. A row is satisfied only by a
test that fails if the guard is removed.

A row may be marked `MATERIALISED` only when a test at the *named* exact head fails
if the guard is removed, and that head has passed its gates. Green hosted gates on
the reviewed heads `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d` and
`97c533de73c9d8f007b6dfc4eaf73804fb1de220` did **not** mean these properties held,
so the rows below were returned to `PENDING`.

| # | Property | Test location | State |
|---|---|---|---|
| A1 | Strict SemVer accepted for release, prerelease and build forms | `apps/desktop/src/contracts/version.test.ts`, `tests/desktop/test_version_drift.py` | MATERIALISED |
| A2 | Malformed SemVer rejected, never coerced (leading zeros, missing fields, empty identifiers, non-ASCII, oversized, non-string) | same | MATERIALISED |
| A3 | SemVer precedence: prerelease below release, numeric-vs-lexical identifiers, shorter prerelease lower, build metadata ignored | `version.test.ts` | MATERIALISED |
| A4 | Canonical version present, well formed and mirrored exactly | both | MATERIALISED |
| A5 | Missing canonical version fails closed | both | MATERIALISED |
| A6 | Malformed canonical version fails closed | both | MATERIALISED |
| A7 | Missing mirror version is drift, not silence | both | MATERIALISED |
| A8 | Malformed mirror version is distinguished from plain drift | `version.test.ts` | MATERIALISED |
| A9 | Mirror drift detected and offending paths named | both | MATERIALISED |
| A10 | A newer-but-different mirror is still drift | `tests/desktop/test_version_drift.py` | MATERIALISED |
| A11 | Verifier does not mutate manifests | `tests/desktop/test_version_drift.py` | MATERIALISED |
| A12 | Manifest reader helpers fail closed on broken JSON/TOML | `tests/desktop/test_version_drift.py` | MATERIALISED |
| B1 | Channel vocabulary is exactly `stable`/`beta`/`dev`, stable default | `releaseChannel.test.ts` | MATERIALISED |
| B2 | Unknown channel fails closed everywhere | `releaseChannel.test.ts` | MATERIALISED |
| B3 | Version shape must match the channel, derived from the canonical strict parser and **not** from a second, looser pattern (`M-20-05`) | `releaseChannel.test.ts` | PENDING EXACT-HEAD PROOF |
| B4 | Only strictly newer same-channel upgrade is eligible | `releaseChannel.test.ts` | MATERIALISED |
| B5 | Downgrade and identical version refused with distinct reasons | `releaseChannel.test.ts` | MATERIALISED |
| B6 | Numerically newer but wrong-channel version refused | `releaseChannel.test.ts` | MATERIALISED |
| B7 | Cross-channel movement never implicit; explicit intent requires a governed decision | `releaseChannel.test.ts` | MATERIALISED |
| C1 | State vocabulary is closed; unknown state fails closed | `updateState.test.ts` | MATERIALISED |
| C2 | Only declared transitions are legal | `updateState.test.ts` | MATERIALISED |
| C3 | Illegal transitions refused | `updateState.test.ts` | MATERIALISED |
| C4 | No cryptographic scheme admitted in this slice | `updateState.test.ts` | MATERIALISED |
| C5 | Every edge entering an authenticity-dependent state is refused without an accepted authenticity proof (`H-20-01`, `H-21-01`) | `updateState.test.ts`, `updateService.test.ts` | PENDING EXACT-HEAD PROOF |
| C6 | Malformed proof refused before any policy question | `updateState.test.ts` | MATERIALISED |
| C7 | Error code vocabulary closed; unknown code refused | `updateState.test.ts` | MATERIALISED |
| C8 | Oversized error detail refused | `updateState.test.ts` | MATERIALISED |
| C9 | Credential-shaped detail refused even when charset-valid | `updateState.test.ts` | MATERIALISED |
| C10 | Detail containing URLs, paths, uppercase blobs or control characters refused | `updateState.test.ts` | MATERIALISED |
| C11 | Status snapshot closed and bounded: unknown keys refused at top level, in the error object and in **every** event; per-event vocabulary and structural legality; state-dependent candidate and error invariants; canonical reconstruction instead of a cast; direct `ready`/`installing`/`success` snapshots refused; proof-gated successful history refused while pre-gate history stays valid (`H-20-01`, `H-20-03`, `H-21-01`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| D1 | Boundary identity fixed | `updateService.test.ts` | MATERIALISED |
| D2 | Inert service reports unavailable and never claims readiness | `updateService.test.ts` | MATERIALISED |
| D3 | Inert service exposes no mutating/transport/install member | `updateService.test.ts` | MATERIALISED |
| D4 | Forbidden-member guard is not vacuous (detects a violating service) | `updateService.test.ts` | MATERIALISED |
| D5 | Test-only stand-in cannot be imported by production code | `updateService.test.ts` + security gate | MATERIALISED |
| D6 | Invalid configuration fails closed (malformed version, unknown channel, **and** a valid-but-incompatible version/channel pair) (`H-20-02`) | `updateService.test.ts` | PENDING EXACT-HEAD PROOF |
| E1 | About read model bounded, read-only, no authority surface | `aboutReadModel.test.ts` | MATERIALISED |
| E2 | About fails closed on unknown channel, malformed version, invalid status, oversized name, and any version/channel/status identity disagreement (`H-20-02`) | `aboutReadModel.test.ts` | PENDING EXACT-HEAD PROOF |
| E3 | Updater never reported available in this slice | `aboutReadModel.test.ts` | MATERIALISED |
| F1 | Drift verifier imports no network or process module | `tests/desktop/test_version_drift.py` | MATERIALISED |
| F2 | `bundle.active` remains `false` | `tools/desktop/security_gate.py` (existing gate) | MATERIALISED |
| F3 | No updater plugin, shell, filesystem or process primitive reachable | `tools/desktop/security_gate.py` (existing gate) | MATERIALISED |
| G1 | Native contract proof on Windows, Linux and macOS | Governance lanes | PENDING EXACT-HEAD CI |
| G2 | Version drift gate runs in the Desktop Shell lane | `.github/workflows/desktop-shell.yml` | MATERIALISED |

## Additional rows carried by Context Lock Delta 001

| # | Property | Test location | State |
|---|---|---|---|
| H1 | Numeric prerelease identifiers compare exactly above `2^53`, and a very long identifier still orders by value (`H-20-04`) | `version.test.ts` | PENDING EXACT-HEAD PROOF |
| H2 | No later transition into `ready` or `installing` succeeds anywhere in the state vocabulary while the scheme allowlist is empty (`H-20-01`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| H3 | A direct `ready`/`installing` status snapshot is refused, with and without proof material (`H-20-01`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| H4 | Version and channel are one identity at every boundary that asserts it (`H-20-02`) | `updateState.test.ts`, `updateService.test.ts`, `aboutReadModel.test.ts` | PENDING EXACT-HEAD PROOF |
| H5 | Transition-reason vocabulary is closed and enumerable | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| H6 | Every declared status key is required; unknown keys are refused at every level | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| H7 | `DEC-028` exists as `PROPOSED / NOT CANONICAL` with a matching ledger entry (`M-20-06`) | `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md`, `docs/project-brain/10-DECISIONS-LEDGER.md` | PENDING EXACT-HEAD PROOF |

## Additional rows carried by Context Lock Delta 002

| # | Property | Test location | State |
|---|---|---|---|
| I1 | The gated edge set is exactly the set of legal edges whose destination is authenticity-dependent, so no entering edge is left ungated (`H-21-01`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| I2 | No transition anywhere in the state vocabulary reaches `ready`, `installing` or `success`, with or without a well-formed but unadmitted proof (`H-21-01`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| I3 | A direct `success` status snapshot is refused, with and without proof material (`H-21-01`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| I4 | A history entry reporting a `legal_transition` into an authenticity-dependent state is refused, while refusal events on those edges and ordinary pre-gate history remain accepted (`H-21-01`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| I5 | The product TypeScript parser accepts core identifiers far above `2^53` with no precision loss, and orders them exactly (`H-21-02`) | `version.test.ts` | PENDING EXACT-HEAD PROOF |
| I6 | Both languages accept and reject exactly the shared parity vector set, including the 128-character boundary (`H-21-02`) | `version.test.ts`, `tests/desktop/test_version_drift.py`, `apps/desktop/src/contracts/semverParityVectors.json` | PENDING EXACT-HEAD PROOF |
| I7 | The Python gate refuses a trailing LF/CR/CRLF and Unicode line separators, so it can never report `LOCKED` for a version the product parser rejects (`H-21-02`) | `tests/desktop/test_version_drift.py` | PENDING EXACT-HEAD PROOF |
| I8 | Python refuses Unicode decimal digits inside numeric identifiers, matching the ASCII-only JavaScript parser (`H-21-02`) | `tests/desktop/test_version_drift.py` | PENDING EXACT-HEAD PROOF |
| I9 | Inherited fields, class instances, custom prototypes, accessor-backed records, non-enumerable fields, symbol keys, and sparse or accessor-backed event arrays are refused at every level (`M-21-03`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |
| I10 | Validation invokes zero getters, proven by an invocation counter, for status, error, event and proof records (`M-21-03`) | `updateState.test.ts` | PENDING EXACT-HEAD PROOF |

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
dependency or a weakened gate is a STOP condition, not an implementation task. No
row marked `PENDING EXACT-HEAD PROOF` may be claimed as satisfied before the
corrected exact head passes its gates and an independent review returns unresolved
HIGH/CRITICAL `0/0`.
