# Checkpoint — Hive Coder

**Checkpoint:** `HCODER-CP-0018`  
**Status:** CANDIDATE / NOT CANONICAL  
**Date:** 2026-09-15  
**Repository:** `KayzenRoot/hive-coder`  
**Work Order:** `HCODER-WO-0018` — PROMOTION CANDIDATE  
**Issue:** `#44` — OPEN  
**Product PR:** `#45` — DRAFT  
**Base checkpoint:** `HCODER-CP-0017` — APPROVED / CANONICAL  
**Canonical base main SHA:** `79e6eb60288c8e0adcb26bdcffdfe0ae21ef8db7`  
**Technical reviewed head:** `9df7202835a47f2c18af77bbefa665afa5358b38`  
**HEDS technical review:** `5215646309`

## Candidate product state
- All CP-0005 through CP-0017 permission/security/observability boundaries remain authoritative and unchanged.
- `hive-runtime-status-ipc-v1` is the candidate cross-runtime presentation protocol.
- The only protocol operation is `status.snapshot`; no generic RPC namespace is admitted.
- Request wire is deterministic canonical JSON and bounded to 512 UTF-8 bytes.
- Canonical `RuntimeStatusSnapshot v1` remains bounded to 32,768 bytes.
- Total response envelope is bounded to 33,024 bytes.
- Canonical JSON ordering/escaping is explicitly proven across Python and TypeScript, including non-ASCII presentation text.
- Python rejects duplicate keys while parsing; desktop admission requires raw wire to equal the canonical normalized reserialization after semantic validation.
- The desktop public response-admission API is `decodeRuntimeStatusEnvelope(raw)`; the lower-level object semantic parser is private.
- Runtime/provider/task/permission provenance, operational states, provider readiness, uniqueness and counter invariants are revalidated across the language boundary.
- The Python `serve_one()` primitive accepts a prebuilt validated presentation snapshot, one bounded request line and emits one bounded response line. It owns no provider/model/process/task/permission lifecycle.
- No Tauri command, capability permission, process launcher, provider/model/network call, credential access, task/permission mutation, filesystem/Git/terminal/computer-use mutation, remote control, billing/purchase path or automatic skill activation is introduced by WO-0018.

## Correction
`HCODER-WO-0018-CR-001` MEDIUM: **RESOLVED IN CANDIDATE**. The public desktop response boundary is raw-wire-only; semantic-parser bypass is removed and Python/TypeScript Unicode canonical-wire parity is explicitly tested. A later CI failure was fixture-only and corrected without changing the decoder or protocol rules.

## Technical exact-head proof
Exact head `9df7202835a47f2c18af77bbefa665afa5358b38`:
- Governance `35022149949` (#241): **SUCCESS**; Ubuntu **283/283 PASS**; Windows Server 2025 HIGH_ASSURANCE **56/56 PASS**.
- Desktop Shell `35022149971` (#77): **SUCCESS**; security gate PASS; TypeScript PASS; Vitest **23/23 PASS**; Vite production build PASS; npm audit **0 vulnerabilities**; RustSec scanned 432 locked dependencies with **7 allowed warning-class advisories**; Windows Rust **11/11 PASS**; `cargo check --locked` PASS; Tauri release build PASS; `DESKTOP_LAUNCH_SMOKE=PASS`.
- HEDS exact-head review `5215646309`: **APPROVED FOR PROMOTION CANDIDATE**, unresolved HIGH/CRITICAL **0**.

GitHub prohibits the author account from formally approving its own PR, so the HEDS verdict is recorded as an exact-head review COMMENT rather than a GitHub APPROVE event.

## Candidate decision
Standalone governed ADR `DEC-022 — Cross-Runtime Status IPC Contract` is **CANDIDATE — APPROVAL PENDING**. It has no canonical authority until the promotion/final gates and post-merge validation complete.

## Explicit residual boundaries
- CP-0017 remains the canonical checkpoint until CP-0018 finishes promotion.
- No actual desktop-to-Python child-process transport/supervisor exists yet.
- Helper executable identity/authenticity, process containment, restart policy and shutdown lifecycle remain unproven.
- Provider READY remains catalog presentation only, not network/authentication or VERIFIED capability evidence.
- Permission private internals remain outside status transport.
- Seven RustSec warning-class transitive advisories remain dependency debt.
- Stricter CSP, native/full desktop interaction E2E, visual screenshot/pixel fidelity and accessibility automation remain open.
- Installer/signing/updater/release packaging and rollback/roll-forward proof remain open.
- Final Hive Coder project license remains undecided.

## Promotion gate
This checkpoint is only `CANDIDATE`. Promotion requires this documentation/governance delta to pass fresh exact-head Governance + Desktop Shell, promotion HEDS with unresolved HIGH/CRITICAL 0, a final approval mutation with fresh exact-head gates/HEDS, squash merge of PR #45, and post-merge validation on canonical `main`. Only after those gates may CP-0018 be recorded APPROVED / CANONICAL.

## Next governed increment after canonical CP-0018
Reconstruct `HCODER-WO-0019 — Runtime Status Sidecar Helper` on the future canonical CP-0018 main. Historical stacked ancestry must not be merged directly. Process identity/authenticity and lifecycle authority must remain explicitly bounded and separately reviewed.
