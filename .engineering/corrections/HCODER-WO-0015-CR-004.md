# HCODER-WO-0015-CR-004 — Truthful inactive desktop affordances

**Severity:** MEDIUM  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0015`

## Finding
The first shell rendered a Tasks navigation affordance as apparently usable and described the task surface as "Ready for a governed session" even though no execution session or task route existed in WO-0015. That presentation could overstate product readiness.

## Correction
- Only Workspace remains active in the first shell.
- Tasks, Code, Computer and Evidence navigation remain disabled until their governed implementations exist.
- Task execution copy explicitly states that no execution session is attached and the composer/Run control is unavailable in read-only mode.
- Component tests assert these inactive states and reject the prior fake-ready copy.

## Closure gate
RESOLVED becomes final only after the promotion head passes exact-head Governance + Desktop Shell and final HEDS reports no unresolved HIGH/CRITICAL finding.
