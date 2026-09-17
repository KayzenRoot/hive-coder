# HCODER-WO-0024 — Prebuilt Implementation Pack

**Status:** PREBUILT CONTRACT / EXECUTION NOT YET PROVEN  
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
- A mirror is correct only when it parses as strict SemVer **and** equals the canonical value exactly.
- Malformed canonical or mirror versions fail closed and are reported by path.
- The verifier is offline, read-only, deterministic and reports `sideEffects: NONE`.

## Release-channel law
- Channels: `stable`, `beta`, `dev`. `dev` carries the product label `dev/internal`.
- Stable is the default production channel.
- Version shape must match the channel: stable admits no prerelease; `beta`/`dev` admit only a first prerelease identifier equal to their prefix.
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
- `ready -> installing` structurally requires an **accepted** authenticity proof.
- `ADMITTED_AUTHENTICITY_SCHEMES` is empty in this slice, so install-ready is unreachable by construction. No scheme may be invented, faked or bypassed.
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

## Tests before promotion
Contract tests must cover: strict SemVer acceptance and rejection; canonical/mirror drift, missing and malformed mirrors; channel vocabulary and unknown-channel refusal; version-shape/channel matching; same-channel upgrade eligibility; downgrade, identical-version and prerelease-mismatch refusal; cross-channel refusal with governed-decision reporting; the full transition table including illegal transitions; install-ready refusal without an accepted proof; malformed proof refusal; bounded and credential-shaped error-detail refusal; status bound enforcement; inert-boundary member absence; and absence of any network/process/update side-effect surface.

Native proof runs independently on Windows, Linux and macOS. Platform skips cannot promote that platform.

## Evidence required
Exact head, workflow/run/job IDs, runner OS/version/architecture, focused test counts with zero implementation skips, drift-gate output against live manifests, explicit confirmation that `bundle.active` remains `false` and that no updater/download/install/signing/release path exists, and HEDS HIGH/CRITICAL `0/0`.

## STOP
No updater activation, network, download, install, restart, signing, notarization, release publication, dependency addition, `bundle.active=true`, or weakening of an existing HIGH_ASSURANCE gate.
