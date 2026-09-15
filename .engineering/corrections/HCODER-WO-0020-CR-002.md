# HCODER-WO-0020-CR-002 — Preserve unknown permission counters in System Truth

**Severity:** MEDIUM  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0020`

## Finding
The first System Truth rendering candidate used `?? 0` when Permission state was `READY`. If `activeSessions` or `pendingApprovals` were legitimately unobserved (`null`), the UI would display them as measured zeroes.

That would manufacture presentation data inside a surface explicitly named System Truth. It does not grant execution authority, but it can mislead a user about permission/control-plane state.

## Correction
- Preserve `null` as unknown/unexposed rather than coercing it to zero.
- Show concrete counts only when both counters are actually present.
- When Permission is `READY` but counters are absent, state explicitly that the counters are not exposed.
- Add component regression proving no `0 active session(s)` text is fabricated from null counters.

## Authority impact
None. Safety/mutation controls continue to use the unchanged `DesktopSnapshot.safety` authority path and remain disabled.

## Closure gate
Resolved only if the corrected exact head passes Governance + Desktop Shell and HEDS confirms no unresolved HIGH/CRITICAL truthfulness or authority finding.
