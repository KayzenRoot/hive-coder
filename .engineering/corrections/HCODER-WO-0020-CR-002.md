# HCODER-WO-0020-CR-002 — Fixed supervisor security-gate enforcement

**Severity:** MEDIUM  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0020`

## Finding
The first reconstructed security gate allowed process execution only in the dedicated supervisor file, but did not prove every HIGH_ASSURANCE invariant promised by WO-0020. In particular it did not enforce an exact single `Command::new` site, the exact 33,024-byte response ceiling, the canonical request bytes, or mandatory frontend admission through `decodeRuntimeStatusEnvelope(raw)` while rejecting a `JSON.parse(raw)` bypass.

## Correction
The gate now requires:
- exactly one production `Command::new`, only in `runtime_status_supervisor.rs`;
- exact fixed sidecar mode, exact canonical request and exact `MAX_STATUS_RESPONSE_BYTES: u64 = 33_024`;
- `current_exe()` sibling identity, `env_clear`, timeout and child termination helper;
- no dynamic `.args`, `.env`, environment lookup or shell command surface;
- argument-free runtime-status invoke;
- mandatory `decodeRuntimeStatusEnvelope(raw)` and no `JSON.parse(raw)` bypass;
- runtime-status Tauri command signature with no caller-controlled string/path/value payload.

## Authority impact
None. This change strengthens static enforcement of the already approved read-only boundary.

## Closure gate
Resolved only after the corrected exact head passes Governance + Desktop Shell and HEDS reports no unresolved HIGH/CRITICAL.