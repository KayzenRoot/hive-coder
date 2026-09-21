# HCODER-WO-0027 — Tauri Updater Integration Behind Hive Adapter

**Status:** PREBUILT / IMPLEMENTATION NOT STARTED  
**Issue:** #89  
**Parent epic:** HCODER-DIST-001 / Issue #72  
**Slice:** HCODER-DIST-001D  
**Canonical base:** HCODER-CP-0026 / DEC-030 / `5d97df6cf2f69a35d14af140e28088a7659eff7a`  
**Risk:** HIGH_ASSURANCE — remote update metadata/artifact transport can lead to future binary replacement

## OBJECTIVE

Integrate the official Tauri v2 updater behind a Hive-owned admission boundary without exposing the updater plugin directly to frontend code and without admitting installation/restart authority in this slice.

The implementation must make a signed, same-channel, strictly-newer update candidate capable of moving through:

`idle -> checking -> available -> downloading -> verifying -> ready`

where `ready` means: the bytes held by the trusted Rust bridge were downloaded by the updater, the updater's signature verification succeeded, signed-version binding succeeded, Hive version/channel law succeeded, and a bounded `hive-update-admission-v1` receipt can be derived.

This Work Order deliberately stops **before frontend-reachable install/restart**. DIST-001E will govern the user-facing confirmation/install/restart surface.

## CONTEXT

Canonical predecessors already provide:
- DEC-028: canonical version/channel/state law and inert `UpdateService`;
- DEC-029: deterministic six-target package evidence;
- DEC-030: release-provenance/protection substrate, without updater transport;
- desktop security gate: a single frontend invoke bridge and zero plugin permissions.

Current Tauri core is 2.11.5; current CLI is 2.11.4. The updater dependency is not installed. `bundle.active=false` remains canonical.

Current upstream facts to preserve:
- Tauri updater supports Windows/macOS/Linux and requires signed update artifacts;
- `Update::download` verifies the updater signature before returning bytes;
- Tauri's current signed-version protection must be enabled to prevent an endpoint response from pairing an inflated version with an older validly-signed artifact;
- downgrade mode must remain disabled;
- Windows install semantics differ from macOS/Linux restart semantics.

## SCOPE

1. Add the exact-pinned Rust updater dependency required by this design, together with lockfile resolution.
2. Align the Tauri CLI to a version that emits signed-version metadata required by the chosen updater protection, if current source verification confirms that alignment is required.
3. Add a Hive-owned Rust `UpdateAdmissionBridge` with one in-memory pending candidate.
4. Add bounded, argument-free Tauri commands for **status**, **check**, and **download+verify** only.
5. Evolve `UpdateService` from inert-v1 to a bounded network-capable adapter for those three operations.
6. Admit exactly one authenticity scheme whose semantics match the real Tauri verification path.
7. Evolve the desktop security gate so the new authority is named, counted and negatively audited.
8. Add focused Rust/TypeScript/static tests.
9. Materialize DEC-031 as a proposal and evidence for this Work Order.

## OUT OF SCOPE

- frontend-reachable install;
- restart/relaunch;
- update UI/notifications;
- rollback/recovery/post-update health;
- N→N+1 native E2E;
- signing-key generation or access;
- protected-environment/secret provisioning;
- tag/GitHub Release/asset publication;
- `createUpdaterArtifacts=true` in canonical config;
- generic HTTP, shell, process, filesystem, Git, Cua, provider/model or credential authority;
- arbitrary frontend-supplied endpoint, public key, headers, proxy, target, installer args, channel or comparator;
- silent downgrade/cross-channel movement;
- production-distributable claims.

## FILES / SOURCES TO READ FIRST

Canonical:
- `AGENTS.md`
- `docs/project-brain/11-CHECKPOINT.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md`
- `docs/project-brain/adrs/DEC-028-DISTRIBUTION-VERSION-CHANNEL-CONTRACT.md`
- `docs/project-brain/adrs/DEC-030-SIGNING-NOTARIZATION-RELEASE-PROVENANCE.md`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/09-DEFINITION-OF-DONE.md`
- this Work Order + Context Lock.

Implementation:
- `apps/desktop/src/contracts/updateState.ts` + test
- `apps/desktop/src/lib/updateService.ts` + test
- `apps/desktop/src/lib/desktopBridge.ts`
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src-tauri/Cargo.toml` / `Cargo.lock`
- `apps/desktop/src-tauri/tauri.conf.json`
- `apps/desktop/src-tauri/capabilities/desktop-read-only.json`
- `tools/desktop/security_gate.py`.

External source check:
- current official Tauri updater guide;
- exact crate docs/source for the selected updater version;
- exact Tauri CLI release notes for signed-version binding.

## REQUIREMENTS

### R1 — Zero-Guest Updater Surface
- Do not add `@tauri-apps/plugin-updater`.
- Do not add `updater:*` capability permissions.
- Do not add a second frontend `invoke` file.
- All frontend update calls go through `desktopBridge.ts`.

### R2 — Argument-free frontend authority
Allowed frontend commands in this slice:
- `get_update_status`
- `check_for_update`
- `download_update_candidate`

They accept no endpoint, key, URL, version, channel, headers, proxy, target, file path, installer arg, downgrade flag, token or credential.

### R3 — Trusted configuration capsule
The backend consumes a bounded, non-secret `UpdateTrustConfig` determined outside frontend input. Missing or invalid real endpoint/public-key configuration yields `unavailable`; no fake key or placeholder endpoint may become an accepted trust root.

The capsule must bind:
- channel;
- HTTPS endpoint set;
- public updater verification key fingerprint/identity;
- `requireSignedVersion=true`;
- `allowDowngrades=false`;
- dangerous TLS/transport options false.

No private signing key belongs in this capsule.

### R4 — Hive Update Admission Bridge v1
Exactly one pending candidate is owned by trusted Rust state.

Check:
- invokes only the official updater check path;
- emits bounded metadata;
- re-applies DEC-028 same-channel / strictly-newer law;
- refuses malformed/unknown/current/older/cross-channel candidates.

Download:
- acts only on the exact pending candidate identity;
- uses updater download so signature verification happens before bytes return;
- requires signed-version binding;
- computes SHA-256 over the verified returned bytes;
- derives a deterministic metadata identity hash over the bounded admitted candidate projection;
- stores verified bytes only in trusted in-memory state;
- never writes arbitrary paths.

A second check/download cannot silently replace an already-ready candidate.

### R5 — Authenticity receipt
Admit one explicit scheme, provisionally named `tauri-minisign-signed-version-v1`, only after confirming exact upstream semantics.

The existing `AuthenticityProof` remains **evidence/presentation data, not install authority**. A frontend-manufactured proof never authorizes installation. Future install authority must independently consume the Rust bridge's own pending verified candidate.

### R6 — Signed-version anti-replay law
- selected updater version must support signed-version binding;
- `requireSignedVersion=true` is mandatory;
- `allowDowngrades=false` is mandatory;
- no custom comparator may weaken strictly-newer behavior;
- missing signed version and signed/announced mismatch fail closed.

### R7 — HTTPS and request authority
- production endpoint URLs are HTTPS only;
- insecure transport, invalid-certificate and invalid-hostname switches are forbidden;
- no frontend-controlled headers, Authorization, proxy or no-proxy toggle;
- no credentialed updater endpoint in this slice.

### R8 — No installation surface yet
The Rust module may define an internal future installation seam only if unreachable from `tauri::command`, `desktopBridge.ts`, `UpdateService` and product UI in this slice. No install or restart command is registered.

### R9 — Platform truth
Do not claim one uniform post-install behavior. Windows updater installation may terminate the current process; macOS/Linux need relaunch to execute the new version. This Work Order stops before that behavior is exposed.

### R10 — Exact pinning and supply chain
Pin the updater crate exactly. Prefer the smallest dependency surface. No JavaScript guest updater dependency. Any Tauri CLI bump must be exact and lockfile-consistent. Run npm audit and RustSec through the existing Desktop Shell lane.

## ARCHITECTURE RULES

`Product -> UpdateService -> desktopBridge -> named Hive Tauri commands -> UpdateAdmissionBridge -> official Tauri updater -> HTTPS release endpoint`

Never:
`Product -> @tauri-apps/plugin-updater -> plugin command`.

The Rust bridge is the trust choke point. Tauri's signature verification is cryptographic evidence; Hive channel/version admission is policy evidence. Both are required before `ready`.

## CONSTRAINTS

- preserve CP-0026 and all prior authority;
- no secret values;
- no `bundle.active=true`;
- no updater artifact generation in ordinary PR CI;
- no live release endpoint required for hosted acceptance;
- deterministic fake/test backend is required for positive state-machine coverage;
- production path missing trust config must remain unavailable;
- no broad refactor/formatting.

## ACCEPTANCE CRITERIA

1. Source check proves selected updater + CLI behavior from current official sources.
2. Rust updater dependency exact-pinned; no JS guest package.
3. Capability permissions remain `[]`.
4. Security gate knows exactly the new commands and rejects any extra updater invoke/plugin/permission/argument surface.
5. Missing config => unavailable; no network attempt.
6. Unsafe HTTP/TLS settings => refused.
7. Wrong channel/current/older/cross-channel => refused.
8. Signature failure => no bytes admitted.
9. missing signed version / signed-version mismatch => refused.
10. verified bytes + policy admission => one `ready` status with truthful proof.
11. duplicate/replacement/stale-candidate paths fail closed.
12. no install/restart surface reachable from frontend.
13. canonical config packaging law remains intact.
14. focused tests + full relevant suite green.
15. exact-head Governance + Desktop Shell + Native Package Matrix + Protected Release green.
16. independent HEDS unresolved CRITICAL/HIGH = 0/0.

## TESTS

During development:
- targeted Rust unit tests for trust config, candidate identity, policy admission and verified-byte state;
- TypeScript contract/service tests;
- static security-gate tests;
- only targeted mutants for newly added guards.

Final:
- Rust fmt/check/test with locked graph;
- frontend typecheck/component-contract tests/build;
- `tools/desktop/security_gate.py`;
- version drift;
- full discovered Python suite once;
- npm audit;
- hosted four-lane exact-head evidence.

No marathon mutation campaigns.

## DELIVERABLES

- DEC-031 candidate;
- bounded Rust updater bridge;
- evolved Hive UpdateService + state proof semantics;
- updated desktop security gate;
- exact lockfiles;
- focused tests;
- Evidence Bundle;
- Draft PR.

## REVIEW FORMAT

Return:
- base/head SHA;
- exact file list;
- dependency versions;
- source-check evidence;
- changed authority surface;
- tests and negative cases;
- exact-head run IDs;
- blockers/unknowns;
- proposed checkpoint delta only after technical approval.

## STOP CONDITION

STOP if:
- a private signing key/credential would need to be read or generated;
- a placeholder key/endpoint would be treated as production trust;
- direct frontend updater plugin permission/import is required;
- install/restart becomes frontend reachable;
- downgrade/custom comparator/insecure TLS must be enabled;
- new generic HTTP/shell/filesystem/process authority is needed;
- bundle/update artifacts must be published;
- any HIGH/CRITICAL remains unresolved;
- any required exact-head gate is red;
- the exact candidate head changes after evidence.

Never merge implementation from the executor.