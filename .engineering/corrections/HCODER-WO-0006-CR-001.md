# Correction Delta — HCODER-WO-0006-CR-001

## Findings
1. **HIGH · real MCP inventory mismatch:** CP-0003-era adapter assumed tool names could be taken from `server/discover`; pinned Cua 0.28.1 modern MCP exposes canonical executable inventory through `tools/list`.
2. **HIGH · modern tools/call metadata missing:** CP-0005 executor carried only Hive fingerprint metadata; pinned modern MCP requires protocolVersion + clientCapabilities on every request.
3. **HIGH · concrete Cua tool names differed from Hive semantic names:** hardcoding Hive names as upstream names would fail or invite unsafe model-selected mapping.
4. **HIGH · initial Win32 ctypes calls lacked 64-bit-safe signatures:** default ctypes return types can truncate HWND/HANDLE values.
5. **MEDIUM · old synthetic discovery test required migration compatibility while production must use canonical tools/list.

## Corrections
- Production `CuaAdapter.from_binary` now always performs `server/discover` followed by modern `tools/list` and validates schemas/capabilities/annotations.
- Executor adds required modern MCP metadata on `tools/call`.
- `CuaContractResolver` maps Hive semantics to exactly one compatible advertised capability and required schema. Model/task text cannot select the upstream tool name.
- Win32 resolver declares explicit `argtypes`/`restype` for HWND/HANDLE/PID/image APIs.
- Real harness wires the trusted discovered contract into `GatedCuaActionExecutor` only after pinned version preflight, explicit opt-in and sandbox foreground validation.
- Synthetic non-production fixture compatibility is isolated to adapters constructed without production preflight.

## Residual UNKNOWN
Hosted CI does not contain the pinned Cua binary plus a controlled interactive desktop sandbox. Physical click/type E2E therefore remains UNKNOWN, not PASS. Contract and Windows platform logic can be approved independently if exact-head gates pass.