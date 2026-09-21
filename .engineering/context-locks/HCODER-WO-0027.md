# HCODER-WO-0027 — Context Lock

**Status:** LOCKED FOR PREBUILT / IMPLEMENTATION NOT STARTED  
**Issue:** #89  
**Parent:** #72 / HCODER-DIST-001  
**Slice:** HCODER-DIST-001D  
**Canonical base:** HCODER-CP-0026 / `5d97df6cf2f69a35d14af140e28088a7659eff7a`  
**Risk:** HIGH_ASSURANCE

## Source check

Canonical predecessor is HCODER-CP-0026 / DEC-030. CP-0026 admits release-trust evidence and workflow structure but explicitly withholds updater transport, download, install, restart and rollback.

DEC-028 established:
- one canonical product version;
- stable/beta/dev channel law;
- same-channel strictly-newer admission;
- closed update state machine;
- authenticity-dependent `ready/installing/success`;
- empty authenticity scheme allowlist;
- an inert Hive-owned `UpdateService`.

Current desktop security baseline:
- one frontend invoke file: `apps/desktop/src/lib/desktopBridge.ts`;
- exactly three current invokes/commands;
- capability `desktop-read-only` with permissions `[]`;
- no JS Tauri plugin dependencies;
- `bundle.active=false`.

Current upstream constraint snapshot for design purposes:
- updater download verifies signature before returning bytes;
- signed-version binding is available in current updater generation and must be required;
- updater downgrade mode exists but is forbidden here;
- current plugin supports Windows/macOS/Linux;
- Windows install exits/launches installer while macOS/Linux require relaunch.

All upstream details must be refreshed against exact current official docs/source by the executor before dependency edits.

## Authority delta

This Work Order may add exactly:
1. outbound HTTPS update metadata checks to a fixed trusted configuration;
2. download of exactly the candidate admitted by the check;
3. cryptographic verification performed by the official updater before bytes enter Hive ready state;
4. trusted in-memory retention of one verified update candidate;
5. three argument-free Hive-owned Tauri commands: status/check/download+verify.

It grants **no install/restart authority to the frontend**, no signing key access and no generic network surface.

## Allowed implementation paths

Governance:
- `.engineering/work-orders/HCODER-WO-0027.md`
- `.engineering/context-locks/HCODER-WO-0027.md`
- `.engineering/prebuilt/HCODER-WO-0027-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0027-EXECUTOR-BRIEF.md`
- `.engineering/prebuilt/HCODER-WO-0027-ACCEPTANCE-SECURITY-MAP.md`
- `.engineering/evidence/HCODER-WO-0027.md`
- `docs/project-brain/adrs/DEC-031-GOVERNED-TAURI-UPDATER-ADMISSION-BRIDGE.md`
- `docs/project-brain/10-DECISIONS-LEDGER.md` — append/update only the new DEC-031 entry while proposed
- `AGENTS.md` — current execution summary only

Product/desktop:
- `apps/desktop/src/contracts/updateState.ts`
- `apps/desktop/src/contracts/updateState.test.ts`
- `apps/desktop/src/lib/updateService.ts`
- `apps/desktop/src/lib/updateService.test.ts`
- `apps/desktop/src/lib/desktopBridge.ts`
- `apps/desktop/src-tauri/src/lib.rs`
- `apps/desktop/src-tauri/src/update_admission.rs` — new
- `apps/desktop/src-tauri/Cargo.toml`
- `apps/desktop/src-tauri/Cargo.lock`
- `apps/desktop/package.json` — only exact Tauri CLI alignment if source check requires
- `apps/desktop/package-lock.json` — lock mirror of the same
- `tools/desktop/security_gate.py`

## Frozen paths / constraints

Frozen unless a new Context Lock Delta is recorded **before** touching:
- `apps/desktop/src-tauri/tauri.conf.json`;
- `apps/desktop/src-tauri/capabilities/desktop-read-only.json`;
- `.github/workflows/**`;
- `tools/desktop/package_inventory.py`;
- `tools/desktop/version_drift.py`;
- release provenance validator/contract;
- runtime/control-plane/Git/filesystem adapters;
- requirements/scope/architecture/security/DoD/checkpoint;
- every historical Decision/WO/Context Lock/evidence file.

The capability file is expected to stay byte-identical with permissions `[]`.

## High-assurance law

### Zero-Guest
No `@tauri-apps/plugin-updater`, no `updater:*` capability permission, no global Tauri API, no second invoke file.

### No caller-selected trust
Frontend cannot provide endpoint, key, version, channel, URL, signature, headers, proxy, target, installer args or comparator.

### Signed-version required
The selected upstream version must support binding the signed artifact's trusted version identity to the endpoint-announced version. That protection is mandatory. Downgrade mode is forbidden.

### Verified bytes vault
Only bytes returned by the updater's verified download operation may be retained as a ready candidate. Candidate identity must be bound before and after download. No arbitrary filesystem path is written by Hive.

### Policy + crypto are conjunctive
Tauri signature verification alone does not satisfy Hive version/channel policy; Hive policy alone does not satisfy artifact authenticity. `ready` requires both.

### Presentation proof is not authorization
A TypeScript `AuthenticityProof` can describe evidence but can never authorize future installation. Installation must later depend on trusted Rust pending state and separately governed user consent.

### Missing trust root is unavailable
No real public key/endpoint => service unavailable. Empty/sentinel data cannot be used for a real request.

## Explicit forbidden authority

- private updater signing key;
- signing/notarization credentials;
- GitHub release environment/secret changes;
- tag/release publication;
- install/restart/relaunch invoke command;
- updater UI;
- rollback/health/E2E claims;
- generic HTTP client exposed to product;
- request headers/Authorization/proxy from frontend;
- unsafe TLS;
- downgrade/custom weakening comparator;
- arbitrary file writes;
- shell/process/Git/Cua expansion.

## Evidence law

A new head invalidates prior head CI receipts. Final candidate requires:
- Governance;
- Desktop Shell;
- Native Package Matrix;
- Protected Release;
all on the exact same candidate SHA.

A test proving a fake backend can reach `ready` proves contract behavior, not that a real production update was downloaded. Live N→N+1 stays UNPROVEN until DIST-001G.

## STOP CONDITION

STOP before any edit outside the allowed set without an append-only Delta. STOP before secret access, install/restart exposure, placeholder trust, unsafe transport/downgrade, workflow/release publication change, unrelated refactor, or any unresolved HIGH/CRITICAL/red required gate. Never merge from executor.