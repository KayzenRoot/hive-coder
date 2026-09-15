# HCODER-WO-0020-CR-001 — System Truth null-counter/provenance hardening

**Severity:** MEDIUM  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0020`

## Finding
The first canonical reconstruction rendered permission counters with `?? 0` when the Permission Plane state was READY but counters were absent. That could present unknown counters as observed zeroes. Provider/permission status cards also used a generic transport provenance instead of the canonical subsystem provenance already present in the validated snapshot.

## Correction
- READY permission state with unknown counters now reports counters as unavailable rather than zero.
- Permission provenance is rendered from canonical `hive-permission-control-plane` data.
- Provider provenance is rendered from canonical provider provenance when a provider exists, otherwise from the runtime observation provenance.
- Added component regression proving null counters are never fabricated as zero and canonical provenance remains visible.

## Authority impact
None. This correction narrows presentation claims and does not enable any action, process argument, provider/model call, permission mutation, filesystem/Git mutation or computer-use authority.

## Closure gate
Resolved only after the corrected exact head passes Governance + Desktop Shell and HEDS finds no unresolved HIGH/CRITICAL.