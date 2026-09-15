# Decisions Ledger — Hive Coder

## DEC-001 — Separate repository/product
**Status:** APPROVED  
Hive Coder is developed in `KayzenRoot/hive-coder`, separate from `hive-code`.

## DEC-002 — Foundation direction
**Status:** APPROVED FOR ARCHITECTURE/ASSESSMENT  
Use Open Interpreter and Cua as preferred foundations to evaluate/integrate behind Hive-owned adapters. This is not permission to copy blindly or lock architecture before license/API/prototype validation.

## DEC-003 — Visual direction
**Status:** APPROVED DIRECTION  
Premium desktop UX inspired by modern macOS qualities such as clarity, translucency and polished motion, while using original Hive branding/assets and avoiding Apple proprietary/trademarked assets.

## DEC-004 — Engineering workflow
**Status:** APPROVED  
Prompt mode `GEF_V1`; review mode `HEDS_DELTA`; exact-head evidence; same-WO Correction Delta; canonical source hierarchy defined in `00-SOURCE-HIERARCHY.md`.

## DEC-005 — First validated external foundations
**Status:** APPROVED  
`HCODER-WO-0002` validated Open Interpreter `0.0.43` and Cua Driver `0.28.1` as the first pinned external foundations behind Hive-owned boundaries. Open Interpreter uses ACP / JSON-RPC over stdio as the primary integration path with exec JSONL as fallback. Cua Driver uses MCP / JSON-RPC 2.0 over stdio. Full upstream repositories and binaries are not vendored by this decision; automatic installation remains disabled. Optional OmniParser/Ultralytics components remain excluded from the approved foundation set. Any live desktop-control action is a separate HIGH_ASSURANCE increment.

## DEC-006 — Hive-owned runtime bridge
**Status:** APPROVED  
`HCODER-WO-0003` establishes a Hive-owned shell-free stdio/process and strict NDJSON JSON-RPC boundary around the pinned foundations. Open Interpreter ACP v1 is approved for initialize, session create/cancel/update/close without prompt execution. Cua Driver modern MCP `2026-07-28` is approved for `server/discover` inventory only. Production adapter launch is gated by the canonical foundation lock and exact-version preflight; child environments use an explicit least-privilege allowlist. Cua `tools/call`, Open Interpreter prompt execution and all real desktop actions remain unapproved until their later governed increments.

## DEC-007 — Hive Permission & Control Plane authorization core
**Status:** APPROVED  
`HCODER-WO-0004` establishes the Hive-owned HIGH_ASSURANCE authorization choke point required before future privileged adapter execution. Capability/action/target policy is default-deny with explicit-deny precedence; high-risk mutation and critical capability classes have mandatory approval floors. Control sessions are bounded, security expiry uses monotonic time, and policy/global emergency epochs invalidate stale authorization. Approval grants and execution permits are HMAC-SHA256 signed with a 256-bit minimum key, request/session/epoch/expiry bound and single-use. Request fingerprints bind canonical executor arguments and target identity while untrusted model/task context cannot grant capability. Emergency stop, user takeover, cancellation, expiry and policy changes invalidate ephemeral authorization; cancellation callbacks execute outside the authorization critical lock. The control-plane audit surface is private, redacted and hash chained in memory. This decision does **not** approve Cua `tools/call`, a real desktop executor, OS-global emergency hotkeys, durable audit persistence, Open Interpreter prompt execution or production deployment. Those remain separate governed increments.
