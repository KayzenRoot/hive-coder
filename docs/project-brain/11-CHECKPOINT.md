# Checkpoint — Hive Coder

**Checkpoint:** HCODER-CP-0006  
**Status:** APPROVED  
**Date:** 2026-09-14  
**Repository:** `KayzenRoot/hive-coder`  
**Approved Work Order:** `HCODER-WO-0006`  
**PR:** `#13`

## Proven canonical state
- CP-0005 permit-gated mutation boundary remains authoritative.
- Production Cua modern MCP uses `server/discover` then canonical `tools/list`; schemas, capability tokens and annotations are validated.
- Every modern `tools/call` carries MCP `2026-07-28` per-request metadata plus Hive request fingerprint.
- Hive semantic click/type actions resolve to exactly one compatible concrete Cua tool using trusted advertised capability + required schema. Model/task text cannot choose the binding.
- Real harness requires `HIVE_ENABLE_REAL_CUA=1`, explicit binary, exact pinned-version preflight and explicit sandbox application.
- Foreground target identity is obtained from typed Win32 HWND/PID/process-image APIs and revalidated by the existing executor.
- Harness wires the trusted Cua peer and bindings into `GatedCuaActionExecutor`; all mutations still require CP-0005 approval + single-use permit.
- No new mutation capability was added.
- HEDS CR-001 resolved production inventory mismatch, missing modern mutation metadata, unsafe name coupling and 64-bit Win32 ctypes signatures.
- Implementation candidate `0c8a18609fe2414cf892ccbeff25c3923d58c2d4` passed Governance run `34914734955`: Ubuntu 82/82 PASS; Windows Server 2025 HIGH_ASSURANCE 56/56 PASS; ResourceWarning fatal.

## Physical E2E state
**UNKNOWN.** Hosted CI does not have the pinned Cua Driver plus a controlled interactive Windows desktop sandbox. This checkpoint does not claim that a physical click or keystroke was executed. The harness is ready for an explicitly provisioned safe environment proof.

## Product direction captured
- Model Capability Negotiator so Hive adapts features/tools to the selected LLM's proven abilities.
- Hive Skills Engine with discovery, provenance, versioning, evaluation, activation, rollback and governed learning of reusable skills.
- Long-running/resumable autonomous agent workflows.
- Secure Remote Hive Control from another authorized computer with encrypted authenticated device sessions, least privilege, approval relay, audit, revocation and emergency stop. No raw public Cua/RDP/VNC exposure.

## Next necessary increment
Implement the **Model Capability Registry + Skills Foundation** before broad autonomous execution. Normalize provider/model capabilities, define the Hive skill manifest/store/loader boundary, ingest verified MCP skill resources as untrusted content, and add deterministic skill validation/evaluation hooks. Keep skill activation unable to grant permissions. Remote Control follows as its own HIGH_ASSURANCE subsystem after identity/device-session architecture is frozen.