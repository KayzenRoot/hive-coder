# Evidence Bundle — HCODER-WO-0018

**Work Order:** `HCODER-WO-0018`  
**Issue:** `#44`  
**PR:** `#45`  
**Canonical base:** `79e6eb60288c8e0adcb26bdcffdfe0ae21ef8db7` (`HCODER-CP-0017`)  
**Technical reviewed head:** `9df7202835a47f2c18af77bbefa665afa5358b38`  
**Status:** APPROVED FOR PROMOTION CANDIDATE

## Objective evidence
WO-0018 freezes a cross-runtime presentation-only status protocol before any desktop runtime process lifecycle is approved. The protocol is exactly `hive-runtime-status-ipc-v1` with one operation, `status.snapshot`.

The implementation carries canonical `RuntimeStatusSnapshot v1` data between Python and the desktop TypeScript contract without adding generic RPC, subprocess launch/supervision, provider/network/model execution, credentials, task/permission mutation, filesystem/Git mutation, Tauri permission expansion or computer-use mutation.

## Wire contract
- request ID: ASCII `[A-Za-z0-9_.:-]`, 1..64 chars;
- request ceiling: **512 UTF-8 bytes**;
- canonical snapshot ceiling remains **32,768 bytes**;
- total response envelope ceiling: **33,024 bytes** (`MAX_STATUS_BYTES + 256`);
- canonical JSON: recursively sorted object keys, compact separators and Python-compatible ASCII escaping;
- unknown/extra fields, protocol/schema drift, duplicate/noncanonical wire and malformed UTF-8/JSON fail closed;
- Python one-shot handler accepts a prebuilt `RuntimeStatusSnapshot`, reads one bounded newline-framed request and emits exactly one bounded response line.

## Cross-runtime semantic parity
The desktop decoder independently re-enforces:
- `READY | UNKNOWN | DISCONNECTED | DEGRADED` states;
- runtime provenance `hive-runtime-status`;
- provider provenance `hive-provider-catalog`;
- task provenance `hive-agent-task-runtime`;
- permission provenance `hive-permission-control-plane`;
- provider/model collection ceilings and duplicate rejection;
- READY provider requires concrete observed models;
- task counter consistency;
- UNKNOWN/DISCONNECTED permission state cannot carry authoritative-looking counters;
- snapshot byte ceiling.

The only public desktop response-admission API is `decodeRuntimeStatusEnvelope(raw)`, so callers cannot bypass raw-wire canonicality by importing the lower-level semantic object parser.

## Correction evidence
### HCODER-WO-0018-CR-001 — MEDIUM — RESOLVED
Semantic pre-review found that the initial TypeScript semantic parser was exported and could allow a future consumer to bypass the raw canonical-wire proof after arbitrary `JSON.parse()`. The correction made that parser private, moved adversarial tests to the raw decoder and added explicit Python/TypeScript Unicode ASCII-escape parity for `café 🍯`.

A subsequent desktop-web failure on the corrected head was traced to test-fixture construction only: one provenance replacement targeted the protocol prefix and one valid provider fixture used noncanonical key order. The implementation was unchanged; the fixtures were corrected in `9df7202835a47f2c18af77bbefa665afa5358b38`.

## Exact-head Governance evidence
Governance run `35022149949` (#241) on `9df7202835a47f2c18af77bbefa665afa5358b38`: **SUCCESS**.
- Ubuntu source-pack: **283/283 PASS**.
- Windows Server 2025 HIGH_ASSURANCE: **56/56 PASS**.

## Exact-head Desktop Shell evidence
Desktop Shell run `35022149971` (#77) on the same exact head: **SUCCESS**.

Desktop-web:
- `DESKTOP_SECURITY_GATE=PASS`;
- TypeScript typecheck PASS;
- Vitest **23/23 PASS**, including **11** runtime-status IPC tests;
- Vite production build PASS;
- npm audit: **0 vulnerabilities**.

Desktop-windows:
- RustSec scanned **432** locked crate dependencies with no blocking vulnerability and **7 allowed warning-class advisories**;
- Rust unit tests **11/11 PASS**;
- `cargo check --locked` PASS with warnings denied;
- Tauri Windows release build PASS;
- `DESKTOP_LAUNCH_SMOKE=PASS`.

## HEDS technical review
Review `5215646309`, anchored to exact head `9df7202835a47f2c18af77bbefa665afa5358b38`: **APPROVED FOR PROMOTION CANDIDATE**. Unresolved HIGH/CRITICAL findings: **0**.

GitHub does not allow the PR author account to submit a formal APPROVE event on its own pull request, so the HEDS verdict is recorded as an exact-head review COMMENT. This is not represented as a GitHub branch-review approval.

## Explicit residual boundaries
- No desktop-to-Python child-process transport or supervisor is implemented by WO-0018.
- No helper executable identity/authenticity, restart policy, shutdown lifecycle or process containment is proven here.
- No provider/network/model call or credential access exists in the protocol path.
- No task or Permission & Control Plane mutation exists; status is not authorization.
- No generic RPC namespace, socket listener, WebSocket or HTTP service is introduced.
- Seven RustSec warning-class transitive advisories remain inherited dependency debt.
- Actual runtime sidecar lifecycle remains a separately governed later increment.

## Promotion rule
The technical implementation is approved only for promotion staging. `HCODER-CP-0018` remains non-canonical until the promotion/final approval deltas pass fresh exact-head Governance + Desktop Shell, HEDS reports unresolved HIGH/CRITICAL = 0, PR #45 is squash-merged, and post-merge validation succeeds on canonical `main`.
