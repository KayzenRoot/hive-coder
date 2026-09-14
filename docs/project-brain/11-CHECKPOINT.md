# Checkpoint — Hive Coder

**Checkpoint:** HCODER-CP-0002  
**Status:** APPROVED  
**Date:** 2026-09-14  
**Repository:** `KayzenRoot/hive-coder`  
**Approved Work Order:** `HCODER-WO-0002`  
**PR:** `#4`

## Proven canonical state
- The initial Source Pack and GEF/HEDS governance from HCODER-CP-0001 remain authoritative.
- Open Interpreter `0.0.43` is pinned to tag `rust-v0.0.43`, commit `6e7c4bb78bb1c349b82f584f7e21a529ec39a74f`, Apache-2.0.
- Cua Driver `0.28.1` is pinned to tag `cua-driver-rs-v0.28.1`, commit `d8028a7943087ee258dc1b4d19dc12a7cd27669c`, MIT.
- Official Windows x64 artifact names and SHA-256 digests for both foundations are frozen in `foundations/foundations.lock.json`.
- Interpreter primary boundary is ACP / JSON-RPC over stdio; exec JSONL is fallback.
- Cua Driver primary boundary is MCP / JSON-RPC 2.0 over stdio.
- `tools/foundations/verify_lock.py` validates the foundation contract fail-closed.
- `tools/foundations/doctor.py --inventory-only` inventories locked foundations without executing external processes.
- Normal doctor mode is non-installing and explicitly reports `EXTERNAL_VERSION_PROBE` when it may execute pinned `--version` commands.
- Unit tests cover invalid licenses/policies, missing binaries, exact version matching, version mismatch and inventory side-effect classification.
- `HCODER-WO-0002-CR-001` and `HCODER-WO-0002-CR-002` were resolved in the same Work Order/PR.
- Exact-head Governance passed on the reviewed implementation candidate before this checkpoint promotion.

## Product state
The foundation discovery/verification layer is functional. No proven Hive Desktop shell, OpenCode Go provider integration, live Open Interpreter session bridge, live Cua computer-use session, permission engine, packaging or production deployment exists yet.

## Safety state
- No foundation repository or binary is vendored.
- Automatic foundation download/install is disabled.
- OmniParser/Ultralytics are excluded from the approved first foundation set.
- Live mouse/keyboard/desktop control remains unimplemented and requires HIGH_ASSURANCE proof obligations, explicit permission mediation, emergency stop/user takeover, bounded scopes and rollback/containment.

## Next necessary increment
Implement the smallest Hive-owned runtime bridge for Open Interpreter ACP and Cua MCP process lifecycle with mocked/contract-tested transports first. Do not enable real desktop actions until permission policy, emergency stop, user takeover and audit semantics are proven in the same HIGH_ASSURANCE increment or an earlier approved prerequisite.
