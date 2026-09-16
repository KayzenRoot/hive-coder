# DEC-026 — Governed Existing-File Replacement Capability

**Status:** PROPOSED / NOT CANONICAL — CR-001 REVISED CANDIDATE  
**Work Order:** `HCODER-WO-0022`  
**Correction:** `HCODER-WO-0022-CR-001`  
**Source checkpoint:** `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`

## Context
CP-0021 canonicalized safe creation of a previously absent regular workspace file. Practical code editing next requires changing an existing file. The original WO-0022 candidate required strict expected-target CAS at publication time.

CR-001 established that ordinary atomic replacement and strict expected-target CAS are different guarantees. The evaluated native replacement interfaces do not provide a portable publication predicate that takes the exact previously approved destination identity as a success condition across Windows, Linux and macOS. Pretending otherwise would create a stronger security claim than the platform evidence supports.

## Revised proposed decision
Introduce a distinct Hive-owned `replace_file_v1` action under existing `FILESYSTEM_WRITE` authority using a **bounded-race atomic replacement contract**, not a strict CAS contract.

Approval and permit binding include the canonical workspace, normalized target, parent identity, exact observed old target identity, old content digest/length and exact new content digest/length. The executor revalidates live workspace, parent, target identity and old content as late as safely possible before publication. Every stale condition observed before publication fails closed.

The final publication operation must atomically replace the pathname with exactly the approved new bytes on a platform/filesystem combination whose native tests prove that property. Link/reparse traversal, `.git`, non-regular targets and outside-workspace paths fail closed. Capability-created temporary objects are cleaned up only after their identity/ownership is verified.

A valid single-use permit is consumed only at the final mutation-ready boundary. Reaching an unimplemented or unavailable publication backend must not consume a permit.

## Explicit residual external-process race
This candidate does **not** claim strict expected-inode CAS. An uncooperative external process may change the destination pathname after Hive's final successful revalidation and before the OS atomic publication call. Where the native interface cannot predicate publication on the previously approved identity, that final interval cannot honestly be described as eliminated.

This residual is an explicit product/security assumption of ordinary interoperable workspace files. Hive-controlled actors remain governed by the Permission & Control Plane, and all observable stale state before publication remains fail-closed. A future content-addressed/versioned workspace architecture may revisit the assumption under a separate ADR.

## Platform support law
Windows, Linux and macOS are first-class targets, but support is evidence-based per platform/filesystem. Native tests must prove atomic publication, no-follow/reparse/root safety, stale-state rejection before publication, cleanup ownership, permit ordering and adversarial race behavior. Unsupported combinations expose capability unavailability and fail closed. Darwin evidence is independent from Linux evidence and is tracked by HCODER-PLATFORM-001 / Issue #63.

## Non-decision
This ADR does not approve append, truncate-in-place, delete, arbitrary rename/move, Git mutation, terminal/shell execution, desktop/Tauri mutation, outside-workspace mutation, Cua mutation expansion, or any broader capability. It also does not canonicalize a content-addressed workspace architecture.

## Promotion condition
Remain NOT CANONICAL until the corrected implementation, native adversarial race/reparse tests for every declared-supported platform, permit-ordering tests, full regressions, exact-head Governance/Desktop gates, HEDS with unresolved HIGH/CRITICAL 0, product merge, post-merge exact-SHA validation and canonical closeout all succeed.