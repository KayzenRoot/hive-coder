# Evidence Bundle — HCODER-WO-0005

**Risk:** HIGH_ASSURANCE  
**Base:** `31740c39990ba7902b67146da004dac2f0c8a7c4`  
**Implementation/correction evidence head:** `28e696f57882bbca9e3e3a47184ca3d35e19f058`

## HEDS findings resolved
- HIGH: arbitrary argument forwarding for safe tool names → exact action schemas/bounds.
- HIGH: cancellation event alone could not interrupt blocking JSON-RPC → cancellation closes Cua peer.
- MEDIUM: Windows gate omitted executor tests → executor included.
- MEDIUM: stale ControlPolicy test fixture → canonical builders used.

## Deterministic evidence
- Ubuntu exact-head: `28e696f57882bbca9e3e3a47184ca3d35e19f058`.
- Ubuntu broad regression: **74/74 PASS**.
- Windows Server 2025 exact-head: same SHA.
- Windows HIGH_ASSURANCE targeted suite: **48/48 PASS**.
- `PYTHONWARNINGS=error::ResourceWarning`.

## HEDS verdict
**APPROVED for the bounded executor contract.**

The approval is deliberately narrower than physical desktop E2E. Real Cua Driver mutation, target acquisition from Windows and irreversible OS-side action cancellation remain UNKNOWN until the next opt-in real-Cua harness proves them.

## Promotion rule
`DEC-008` and `HCODER-CP-0005` may promote only the bounded facts above. Final promoted head requires a fresh exact-head Governance run before merge.
