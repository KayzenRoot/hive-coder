# Correction Delta — HCODER-WO-0002 / CR-002

**MODE:** CORRECTION  
**ACCEPTED/FROZEN:** upstream versions/commits/artifact hashes/licenses and CR-001 exact-version matching.  
**OPEN FINDINGS:** (1) Cua boundary described JSON-RPC 2.0 as independent from MCP; pinned driver actually exposes MCP JSON-RPC 2.0 over stdio. (2) normal doctor mode labeled side effects `NONE` despite executing external `--version` processes.  
**SEVERITY:** MEDIUM  
**ROOT CAUSE:** transport and application protocol were modeled separately; doctor metadata did not distinguish inventory-only from executable probing.  
**DECISION:** model Cua primary boundary as `mcp-jsonrpc-2.0-stdio`; restrict discovery to `cua-driver`; disclose `EXTERNAL_VERSION_PROBE` for normal doctor mode while preserving `NONE` for inventory-only.  
**TARGETS:** foundation lock/docs/readme, doctor, doctor tests.  
**FORBIDDEN:** runtime tool calls, installation, desktop control, provider expansion.  
**REQUIRED TESTS:** foundation suite + exact-head Governance.  
**STOP:** corrected candidate only.
