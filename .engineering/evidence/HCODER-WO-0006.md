# Evidence Bundle — HCODER-WO-0006

**Risk:** HIGH_ASSURANCE  
**Base:** `02034116ed0d3fcfcf8650e7b53555fad567b6dc`

## First-party pinned-source verification
Pinned Cua commit `d8028a7943087ee258dc1b4d19dc12a7cd27669c` confirms modern MCP `2026-07-28` over stdio, per-request protocol metadata, canonical `tools/list`, and MCP skills/resources whose reading does not itself activate a skill. Cua tool inventory advertises `inputSchema`, annotations and capability tokens.

## HEDS findings resolved
- HIGH: real inventory is `tools/list`, not discovery-embedded tool names.
- HIGH: every modern `tools/call` requires MCP protocol metadata.
- HIGH: concrete Cua tool names must be trusted capability/schema-derived bindings, not Hive/model strings.
- HIGH: Win32 HWND/HANDLE ctypes signatures must be 64-bit safe.
- MEDIUM: synthetic legacy test compatibility isolated from production `from_binary` path.

## Deterministic evidence
Implementation candidate `0c8a18609fe2414cf892ccbeff25c3923d58c2d4`:
- Governance run `34914734955`: SUCCESS.
- Ubuntu exact-head broad regression: **82/82 PASS**.
- Windows Server 2025 exact-head HIGH_ASSURANCE suite: **56/56 PASS**.
- `ResourceWarning` treated as error.

## Physical E2E
**UNKNOWN by design.** Hosted CI does not provide the pinned Cua Driver binary plus a controlled interactive Windows desktop sandbox. No physical click/type claim is promoted.

## HEDS verdict
**APPROVED for the real-Cua integration harness contract and Windows target-resolution/wiring logic.** Physical mutation remains a later opt-in environment proof.

Final promoted head requires fresh exact-head Governance before merge.