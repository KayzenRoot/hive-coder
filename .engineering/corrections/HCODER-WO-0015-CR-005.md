# HCODER-WO-0015-CR-005 — Apple-specific font-reference removal

**Severity:** LOW  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0015`

## Finding
The initial CSS fallback stacks referenced `-apple-system`, `BlinkMacSystemFont` and `SFMono-Regular`. No Apple font was bundled or copied, but those references were unnecessary for Hive's original identity boundary.

## Correction
- Replaced the references with generic/system Windows/Linux-safe font stacks.
- Extended the static desktop security gate to scan CSS and fail if those Apple-specific font references reappear.
- Original HiveMark SVG and Hive-owned styling remain the only first-party visual identity assets in the slice.

## Closure gate
RESOLVED becomes final only after the promotion head passes exact-head Governance + Desktop Shell and final HEDS reports no unresolved HIGH/CRITICAL finding.
