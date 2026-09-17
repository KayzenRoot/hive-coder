# HCODER-WO-0024 — Acceptance & Security Map

**Status:** PREBUILT — every row is an executable test obligation  
**Issue:** `#77`

Required negative proofs are the point of this slice. A row is satisfied only by a
test that fails if the guard is removed.

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
| B3 | Version shape must match the channel | `releaseChannel.test.ts` | MATERIALISED |
| B4 | Only strictly newer same-channel upgrade is eligible | `releaseChannel.test.ts` | MATERIALISED |
| B5 | Downgrade and identical version refused with distinct reasons | `releaseChannel.test.ts` | MATERIALISED |
| B6 | Numerically newer but wrong-channel version refused | `releaseChannel.test.ts` | MATERIALISED |
| B7 | Cross-channel movement never implicit; explicit intent requires a governed decision | `releaseChannel.test.ts` | MATERIALISED |
| C1 | State vocabulary is closed; unknown state fails closed | `updateState.test.ts` | MATERIALISED |
| C2 | Only declared transitions are legal | `updateState.test.ts` | MATERIALISED |
| C3 | Illegal transitions refused | `updateState.test.ts` | MATERIALISED |
| C4 | No cryptographic scheme admitted in this slice | `updateState.test.ts` | MATERIALISED |
| C5 | Install refused without an accepted authenticity proof | `updateState.test.ts`, `updateService.test.ts` | MATERIALISED |
| C6 | Malformed proof refused before any policy question | `updateState.test.ts` | MATERIALISED |
| C7 | Error code vocabulary closed; unknown code refused | `updateState.test.ts` | MATERIALISED |
| C8 | Oversized error detail refused | `updateState.test.ts` | MATERIALISED |
| C9 | Credential-shaped detail refused even when charset-valid | `updateState.test.ts` | MATERIALISED |
| C10 | Detail containing URLs, paths, uppercase blobs or control characters refused | `updateState.test.ts` | MATERIALISED |
| C11 | Status snapshot bounded; unknown fields and oversized event lists refused | `updateState.test.ts` | MATERIALISED |
| D1 | Boundary identity fixed | `updateService.test.ts` | MATERIALISED |
| D2 | Inert service reports unavailable and never claims readiness | `updateService.test.ts` | MATERIALISED |
| D3 | Inert service exposes no mutating/transport/install member | `updateService.test.ts` | MATERIALISED |
| D4 | Forbidden-member guard is not vacuous (detects a violating service) | `updateService.test.ts` | MATERIALISED |
| D5 | Test-only stand-in cannot be imported by production code | `updateService.test.ts` + security gate | MATERIALISED |
| D6 | Invalid configuration fails closed (malformed version, unknown channel) | `updateService.test.ts` | MATERIALISED |
| E1 | About read model bounded, read-only, no authority surface | `aboutReadModel.test.ts` | MATERIALISED |
| E2 | About fails closed on unknown channel, malformed version, invalid status, oversized name | `aboutReadModel.test.ts` | MATERIALISED |
| E3 | Updater never reported available in this slice | `aboutReadModel.test.ts` | MATERIALISED |
| F1 | Drift verifier imports no network or process module | `tests/desktop/test_version_drift.py` | MATERIALISED |
| F2 | `bundle.active` remains `false` | `tools/desktop/security_gate.py` (existing gate) | MATERIALISED |
| F3 | No updater plugin, shell, filesystem or process primitive reachable | `tools/desktop/security_gate.py` (existing gate) | MATERIALISED |
| G1 | Native contract proof on Windows, Linux and macOS | Governance lanes | PENDING EXACT-HEAD CI |
| G2 | Version drift gate runs in the Desktop Shell lane | `.github/workflows/desktop-shell.yml` | MATERIALISED |

## Security invariants this slice must not weaken
The existing `tools/desktop/security_gate.py` assertions — zero frontend invokes
beyond the three governed commands, zero capability permissions, `desktop-read-only`
scope, zero filesystem mutation primitives, zero generic process execution, one
fixed runtime sidecar process, zero Apple-specific font references, committed
lockfiles — must remain unchanged and passing.

## STOP
Any row that cannot be satisfied without distribution authority, an updater
dependency or a weakened gate is a STOP condition, not an implementation task.
