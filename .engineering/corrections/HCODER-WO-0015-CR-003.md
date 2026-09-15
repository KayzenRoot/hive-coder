# HCODER-WO-0015-CR-003 — Main-window read-model scope

**Severity:** MEDIUM  
**Status:** RESOLVED IN CANDIDATE  
**Work Order:** `HCODER-WO-0015`

## Finding
Tauri application commands registered directly through `invoke_handler` are application command surfaces rather than plugin capabilities. A future additional Hive window could therefore reach the read-model command unless the command itself enforced the intended caller boundary.

## Correction
`get_desktop_snapshot` now receives the invoking `WebviewWindow` and fails closed unless `window.label() == "main"`. The declarative capability also targets only `main`, and the static security gate independently requires both controls.

No new plugin permission or privileged command was added.

## Closure gate
RESOLVED becomes final only after the promotion head passes exact-head Governance + Desktop Shell and final HEDS reports no unresolved HIGH/CRITICAL finding.
