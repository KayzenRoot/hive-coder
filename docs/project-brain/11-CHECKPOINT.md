# Checkpoint — Hive Coder

**Checkpoint:** HCODER-CP-0005  
**Status:** APPROVED  
**Date:** 2026-09-14  
**Repository:** `KayzenRoot/hive-coder`  
**Approved Work Order:** `HCODER-WO-0005`  
**PR:** `#11`

## Proven canonical state
- HCODER-CP-0004 authorization/control-plane state remains authoritative.
- `GatedCuaActionExecutor` is the only approved Hive code surface that may issue Cua `tools/call`.
- Every dispatch consumes a request-bound, session/epoch-bound, expiring single-use permit from `PermissionControlPlane`.
- Initial allowlist: `pointer.click` mapped to `pointer.input` and `keyboard.type_text` mapped to `text.input` only.
- Exact argument schemas are enforced: click accepts bounded numeric `x/y`; text accepts bounded non-NUL `text`.
- Live normalized application/window identity is revalidated after permit consumption and immediately before dispatch. Drift denies and burns the permit.
- Parallel mutations in one control session are denied.
- Emergency stop/user takeover/cancellation mark the executor session cancelled and close the Cua peer, waking a blocking Hive JSON-RPC request and preventing later dispatch through that peer.
- Cua error results and failed post-action verification fail closed.
- `HCODER-WO-0005-CR-001` resolved stale policy test construction, broad argument forwarding, incomplete Windows executor coverage and non-interrupting RPC cancellation.
- Exact-head candidate `28e696f57882bbca9e3e3a47184ca3d35e19f058` passed Ubuntu broad regression 74/74 and Windows Server 2025 HIGH_ASSURANCE targeted tests 48/48 with ResourceWarning fatal.

## Product state
Hive Coder now has validated foundation pins, runtime bridge, permission/control plane and a first permit-gated Cua action executor contract. The executor is proven against deterministic/mock Cua peers on Ubuntu and Windows. No claim is made that CI physically mutated a Windows desktop with the pinned Cua Driver.

## Safety state
- Shell, filesystem mutation, clipboard, destructive, privileged and unmapped Cua tools remain blocked.
- Both approved mutation capabilities retain mandatory trusted approval.
- Model/task text cannot mint approvals or permits.
- Peer closure proves cancellation at the Hive RPC boundary but cannot roll back an OS input already accepted by Cua.
- Automatic foundation installation remains disabled and provenance pins remain unchanged.

## Next necessary increment
Build an opt-in real-Cua Windows integration harness for pinned Cua Driver `0.28.1`. Prove discovery-to-executor wiring, actual tool-name/argument mapping, live target resolver behavior, safe sandboxed pointer/text actions, emergency-stop behavior and post-action evidence without broadening the allowlist. Fail closed when the pinned binary or sandbox target is unavailable.
