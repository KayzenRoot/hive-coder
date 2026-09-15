# Decisions Ledger — Hive Coder

## DEC-001 — Separate repository/product
**Status:** APPROVED  
Hive Coder is developed in `KayzenRoot/hive-coder`, separate from `hive-code`.

## DEC-002 — Foundation direction
**Status:** APPROVED FOR ARCHITECTURE/ASSESSMENT  
Use Open Interpreter and Cua as preferred foundations behind Hive-owned adapters.

## DEC-003 — Visual direction
**Status:** APPROVED DIRECTION  
Premium desktop UX inspired by modern macOS qualities while using original Hive branding/assets.

## DEC-004 — Engineering workflow
**Status:** APPROVED  
Prompt mode `GEF_V1`; review mode `HEDS_DELTA`; exact-head evidence; same-WO Correction Delta.

## DEC-005 — First validated external foundations
**Status:** APPROVED  
Open Interpreter `0.0.43` and Cua Driver `0.28.1` are pinned behind Hive-owned boundaries. Automatic installation is disabled; optional OmniParser/Ultralytics remain excluded.

## DEC-006 — Hive-owned runtime bridge
**Status:** APPROVED  
`HCODER-WO-0003` establishes shell-free stdio/process and strict NDJSON JSON-RPC boundaries. Open Interpreter ACP v1 session lifecycle and Cua modern MCP `2026-07-28` discovery are proven under deterministic contracts.

## DEC-007 — Hive Permission & Control Plane authorization core
**Status:** APPROVED  
`HCODER-WO-0004` establishes default-deny capability/action/target policy, mandatory approval floors, signed request-bound single-use permits, emergency epochs, cancellation/takeover and redacted hash-chained audit.

## DEC-008 — First gated Cua mutation boundary
**Status:** APPROVED  
`HCODER-WO-0005` makes `GatedCuaActionExecutor` the only approved Hive Cua `tools/call` surface. Initial allowlist is only `pointer.click` and `keyboard.type_text`, both mandatory approval, with live target revalidation and emergency/takeover interruption.

## DEC-009 — Real Cua Windows harness contract
**Status:** APPROVED  
`HCODER-WO-0006` corrects the production modern MCP contract to `server/discover` followed by `tools/list`, with protocol metadata on every request. Hive resolves concrete Cua click/type tool names only from the pinned driver's advertised capability tokens and required input schema, never from model/task text. The real Windows harness is explicit opt-in, exact-version preflighted, requires a named sandbox application, obtains HWND/PID/process identity through typed Win32 APIs and wires the trusted discovered bindings into the existing permit-gated executor. No capability is added beyond CP-0005. Hosted CI proves contract and Windows logic but does not prove a physical Cua click/type; physical desktop E2E remains UNKNOWN until a safe runner with the pinned binary is explicitly provisioned.

## DEC-010 — Advanced capability roadmap
**Status:** APPROVED DIRECTION  
Hive Coder will evolve toward model-aware capability negotiation, a Hive-owned versioned/provenance-aware Skills Engine with governed skill learning, long-running autonomous agent workflows and secure remote control from another authorized computer. Remote control is a zero-trust application control plane with encrypted authenticated device sessions, revocation, approvals, audit and emergency stop, not a publicly exposed raw desktop/Cua port.

## DEC-011 — Evidence-driven model capabilities and governed skills
**Status:** APPROVED  
`HCODER-WO-0007` makes explicit verified evidence the only authority for model capability negotiation. Model names, marketing labels, declarations and model-generated prose cannot enable capabilities. Hive skills are versioned/provenance-aware artifacts with separate ingest, deterministic evaluation, activation and rollback states. MCP skill resources are untrusted content regardless of transport trust. Skill activation is subordinate to the existing permission grant and can never mint or broaden authority.
