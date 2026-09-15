# Work Order — HCODER-WO-0006

**Class:** HIGH_ASSURANCE  
**Base checkpoint:** HCODER-CP-0005  
**Base SHA:** `02034116ed0d3fcfcf8650e7b53555fad567b6dc`  
**Issue:** #12

## OBJECTIVE
Build an opt-in Windows harness that connects the pinned Cua Driver 0.28.1 to the CP-0005 gated executor without widening the mutation allowlist.

## SCOPE
- Correct modern MCP inventory flow: `server/discover` then `tools/list` with per-request metadata.
- Preserve and validate advertised tool schemas/capabilities.
- Resolve Hive semantic actions to compatible real Cua tools by advertised capability, not model-supplied names.
- Include modern MCP metadata on every `tools/call`.
- Add trusted Windows foreground target resolver using OS APIs.
- Add an opt-in harness that requires explicit binary and sandbox application/window constraints.
- Deterministic/mock tests run by default; real physical mutation requires explicit opt-in and may remain UNKNOWN in hosted CI.

## OUT OF SCOPE
- New mutation capabilities.
- Automatic Cua installation/download.
- Remote network control.
- Skill activation/execution.
- Shell/filesystem/clipboard/destructive/privileged tools.

## ACCEPTANCE CRITERIA
- Unknown/missing Cua schema/capability fails closed.
- Real tool selection cannot be supplied by model/task text.
- Modern MCP metadata is present on inventory and mutation calls.
- Windows target identity comes from OS state and is checked against an explicit sandbox constraint.
- Existing PermissionControlPlane remains mandatory for mutations.
- Broad Ubuntu and targeted Windows tests pass exact-head.

## STOP CONDITION
HEDS APPROVED; exact-head gates green; checkpoint promoted; squash merge completed; post-merge main validated. Physical Cua E2E is reported UNKNOWN rather than PASS when the pinned binary/sandbox is unavailable.