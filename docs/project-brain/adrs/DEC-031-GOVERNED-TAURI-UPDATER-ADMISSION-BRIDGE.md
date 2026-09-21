# DEC-031 — Governed Tauri Updater Admission Bridge

**Status:** PROPOSED / NOT CANONICAL  
**Work Order:** HCODER-WO-0027  
**Issue:** #89  
**Parent:** HCODER-DIST-001 / #72  
**Slice:** HCODER-DIST-001D  
**Canonical predecessor:** HCODER-CP-0026 / DEC-030  
**Materialised base:** `5d97df6cf2f69a35d14af140e28088a7659eff7a`

## Context

DEC-028 intentionally made update behavior inert. DEC-030 intentionally withheld updater transport. The next safe step is not “turn on auto-update”; it is to introduce a cryptographically and policy-gated transport boundary whose authority can be named precisely.

A direct JavaScript updater plugin would create a wide guest-facing command surface and let frontend code provide options the product does not need. Hive instead keeps the official updater in trusted Rust and exposes only its own narrow operations.

Current Tauri updater behavior relevant to this Decision:
- updater artifacts are signature verified before downloaded bytes are returned to the caller;
- current Tauri provides signed-version binding so a valid older signed artifact cannot be relabeled by an endpoint as a newer version when that protection is enabled;
- downgrade mode and custom comparators can weaken version admission and therefore are prohibited;
- updater platform install behavior differs across Windows versus macOS/Linux.

## Decision candidate

### 1. Zero-Guest Updater Surface
The official updater exists in Rust only. Hive does not add the JavaScript guest updater dependency and grants no `updater:*` capability. Product code speaks only to Hive-owned commands through the single canonical desktop bridge.

### 2. Three operations, all argument-free
This slice admits:
- get update status;
- check fixed configuration for an update;
- download and verify the exact pending candidate.

No install/restart command exists in this slice.

### 3. UpdateTrustConfig is trusted configuration, not user input
A bounded non-secret configuration capsule supplies channel, endpoint(s) and public verification-key identity. It must be fixed for the build/runtime trust domain, never supplied by the webview. Missing real configuration means unavailable.

Dangerous insecure transport, invalid certificate/hostname acceptance, downgrade allowance, caller headers/proxy and custom weakening comparator are forbidden.

### 4. Hive Update Admission Bridge v1
Trusted Rust owns one candidate:
`none -> checked -> verified-bytes`.

A check admits only a DEC-028 strictly-newer candidate in the current channel. A download may target only that exact candidate. Successful download means the official updater returned bytes after signature verification; Hive then hashes those returned bytes and records a bounded metadata identity. Only that conjunction can produce `ready`.

### 5. Signed version is part of authenticity
The updater must require a signature that carries the version identity and must reject missing signed version or signed/announced mismatch. A signature over an older genuine artifact is therefore insufficient to satisfy a forged newer endpoint response.

### 6. Two independent gates
- **Cryptographic gate:** updater signature + signed-version verification.
- **Policy gate:** Hive strict version/channel eligibility.

Neither substitutes for the other.

### 7. hive-update-admission-v1
A deterministic internal receipt binds:
- scheme;
- current/candidate version;
- channel;
- target;
- verified artifact SHA-256;
- deterministic admitted-metadata SHA-256;
- public verification-key fingerprint/identity class.

It contains no private key, credential, Authorization header or arbitrary response body.

The existing TypeScript `AuthenticityProof` may carry the resulting two hashes and scheme for presentation/state validation. It is not an authorization token.

### 8. Verified Bytes Vault
The ready artifact exists only in trusted backend memory for this slice. No Hive filesystem write primitive is used to stage an arbitrary path. A second candidate cannot silently replace a verified candidate.

### 9. Installation is deliberately deferred
The official updater's install primitive may be wrapped internally for future use only if it remains unreachable from Tauri commands and frontend code. DIST-001E must separately govern user consent and frontend-reachable install/restart. DIST-001F owns recovery/health; DIST-001G owns native N→N+1 proof.

### 10. Platform semantics remain distinct
No state/result in this slice claims a uniform restart contract. Windows may terminate while launching its installer; macOS/Linux need relaunch after installation. That difference becomes relevant only once install is separately admitted.

## Security invariants

1. No private updater signing key in repo/runtime prompts/logs/HIVE.
2. No frontend-selected trust root or transport.
3. HTTPS only.
4. Signed-version required.
5. Downgrade disabled; no custom comparator that admits non-newer versions.
6. Same-channel required.
7. Verified bytes only.
8. Ready proof is evidence, not authority.
9. Capability permissions remain empty.
10. No JS updater guest dependency.
11. No install/restart invoke.
12. Missing config fails closed.
13. Unknown/malformed state fails closed.
14. No generic network capability is created.
15. Every new refusal has focused negative test coverage.

## Non-decision

DEC-031 does not approve updater signing-key provisioning, update artifact publication, production endpoint/public-key provisioning, UI/notification design, frontend installation/restart, rollback, post-update health, native update E2E or production-distributable status. It does not amend DEC-030 release publication authority or any Hive runtime capability.

## Promotion gate

DEC-031 remains PROPOSED until:
- implementation follows the locked allowed-file/authority set;
- exact dependency/source semantics are verified;
- focused/adversarial tests are green;
- Governance + Desktop Shell + Native Package Matrix + Protected Release are green on exact head;
- independent HEDS returns unresolved CRITICAL/HIGH 0/0;
- governed merge/closeout creates a separately reviewed checkpoint predicate.

No text in this ADR self-promotes it.