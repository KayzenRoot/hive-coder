# HCODER-WO-0027 — Implementation Pack

## Mission
Mechanically implement DEC-031. Do not redesign the updater architecture.

## Chosen shape
- Rust-only official Tauri updater.
- No JavaScript updater package.
- Existing single `desktopBridge.ts` remains the only invoke file.
- Add exactly three argument-free update commands.
- One Rust `UpdateAdmissionBridge` owns candidate/verified bytes.
- No frontend install/restart in this slice.

## Upstream dependency decision
Refresh exact official sources first. The intended baseline is:
- updater crate version that contains `requireSignedVersion` and `allowDowngrades` protections;
- exact pin, not a floating major/minor.
- Tauri CLI exact version aligned with signed-version metadata generation if required.

Do not mechanically choose “latest” if it conflicts with the repository's pinned Tauri graph; record compatibility evidence.

## Runtime sequence

### status
Return a bounded UpdateStatus snapshot. No network.

### check
1. require valid trusted config; otherwise unavailable;
2. refuse while a verified candidate is already held;
3. build updater from trusted endpoint/public key only;
4. check remote release;
5. validate candidate via DEC-028 strict parser/channel/strictly-newer law;
6. retain a bounded candidate identity;
7. return available/unavailable/failure without leaking remote body/URL/signature.

### download+verify
1. require exact checked candidate;
2. transition downloading;
3. invoke official updater download;
4. official updater cryptographically verifies bytes;
5. require signed-version protection to have accepted the release;
6. SHA-256 returned bytes;
7. deterministic hash of bounded candidate metadata projection;
8. store exact update handle + verified bytes in memory;
9. derive authenticity proof scheme;
10. transition verifying -> ready.

No frontend data chooses the artifact at step 3.

## Trust configuration

The implementation may choose the smallest upstream-supported way to register the plugin, but:
- canonical config must not contain a fake public key or fake production endpoint;
- missing public config must produce unavailable before a request;
- `requireSignedVersion=true`, `allowDowngrades=false`;
- dangerous TLS/transport flags false;
- endpoint/key cannot come from frontend.
Context Lock Delta 001 now authorizes exactly the `plugins.updater` node in `tauri.conf.json`. For this implementation candidate, keep it explicitly unconfigured with empty `pubkey` and empty `endpoints`, while setting `requireSignedVersion=true`, `allowDowngrades=false`, and all dangerous transport/TLS flags to false. Empty trust data means unavailable and must be rejected before any request. Do not invent or generate a real key/endpoint. No other `tauri.conf.json` key is authorized to change.

## State/proof changes

Provisional scheme: `tauri-minisign-signed-version-v1`.

Define its semantics in code/tests before adding it to `ADMITTED_AUTHENTICITY_SCHEMES`.

The proof's artifact hash is over bytes returned by the verified updater download. The metadata hash is over a deterministic Hive-owned admitted projection, not raw unordered JSON and not a log string.

Do not expose raw endpoint response, signature, URL, public key content or headers in UpdateStatus.

## Security-gate delta

The gate should:
- keep a single invoke file;
- update exact invoke count/command allowlist;
- prove new update commands are argument-free;
- reject `@tauri-apps/plugin-updater`;
- reject any `updater:` capability permission;
- require capability permissions remain [];
- reject dangerous updater config flags if they appear;
- reject frontend updater endpoint/key/header/proxy literals/surfaces;
- allow exactly the Rust updater dependency and no generic HTTP client addition;
- keep `bundle.active=false`.

## Tests

Rust:
- missing config;
- HTTP/insecure endpoint;
- invalid channel/current/older/cross-channel;
- no update;
- one admitted update;
- signature/download error;
- signed-version mismatch/missing mapping;
- verified bytes hash binding;
- candidate identity substitution;
- second check while ready;
- failure clears/retains state per declared law;
- no install exposure.

TypeScript:
- new service shape;
- status parsing;
- admitted proof scheme exact shape;
- no plugin import;
- check/download use only named bridge operations;
- install/restart members remain absent/forbidden.

Static:
- command/invoke allowlist;
- capability permissions [];
- no guest updater dependency;
- no unsafe updater flags.

## Test budget
Run focused tests during implementation. Final full relevant suite once. No broad mutation campaign; use targeted guard mutants only where useful.

## Handoff
Return exact head, file list, lockfile diff summary, selected upstream versions, tests, four hosted workflow IDs, blockers and proposed Checkpoint Delta.