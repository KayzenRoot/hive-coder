# DEC-026 — Governed Existing-File Replacement Capability

**Status:** CANONICAL  
**Work Order:** `HCODER-WO-0022`  
**Correction:** `HCODER-WO-0022-CR-001`  
**Source checkpoint:** `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Promoted by:** `HCODER-CP-0022` / closeout merge `795ed101eaf5d770f63a96db7f01a82369be34f1`

## Context
CP-0021 canonicalized safe creation of a previously absent regular workspace file. Practical code editing next requires changing an existing file. The original WO-0022 candidate required strict expected-target CAS at publication time.

CR-001 established that ordinary atomic replacement and strict expected-target CAS are different guarantees. The evaluated native replacement interfaces do not provide a portable publication predicate that takes the exact previously approved destination identity as a success condition across Windows, Linux and macOS. Pretending otherwise would create a stronger security claim than the platform evidence supports.

## Decision
Introduce a distinct Hive-owned `replace_file_v1` action under existing `FILESYSTEM_WRITE` authority using a **bounded-race atomic replacement contract**, not a strict CAS contract.

Approval and permit binding include the canonical workspace, normalized target, parent identity, exact observed old target identity, old content digest/length and exact new content digest/length. The executor revalidates live workspace, parent, target identity and old content as late as safely possible before publication. Every stale condition observed before publication fails closed.

The final publication operation must atomically replace the pathname with exactly the approved new bytes on a platform/filesystem combination whose native tests prove that property. Link/reparse traversal, `.git`, non-regular targets and outside-workspace paths fail closed. Capability-created temporary objects are cleaned up only after their identity/ownership is verified.

A valid single-use permit is consumed only at the final mutation-ready boundary. Reaching an unimplemented or unavailable publication backend must not consume a permit.

## Explicit residual external-process race
This decision does **not** claim strict expected-inode CAS. An uncooperative external process may change the destination pathname after Hive's final successful revalidation and before the OS atomic publication call. Where the native interface cannot predicate publication on the previously approved identity, that final interval cannot honestly be described as eliminated.

This residual is an explicit product/security assumption of ordinary interoperable workspace files. Hive-controlled actors remain governed by the Permission & Control Plane, and all observable stale state before publication remains fail-closed. A future content-addressed/versioned workspace architecture may revisit the assumption under a separate ADR.

## Platform support law
Windows, Linux and macOS are first-class targets, but support is evidence-based per platform/filesystem. Native tests must prove atomic publication, no-follow/reparse/root safety, stale-state rejection before publication, cleanup ownership, permit ordering and adversarial race behavior. Unsupported combinations expose capability unavailability and fail closed. Darwin evidence is independent from Linux evidence and is tracked by HCODER-PLATFORM-001 / Issue #63.

## Non-decision
This ADR does not approve append, truncate-in-place, delete, arbitrary rename/move, Git mutation, terminal/shell execution, desktop/Tauri mutation, outside-workspace mutation, Cua mutation expansion, or any broader capability. It also does not canonicalize a content-addressed workspace architecture.

## Promotion evidence
The corrected implementation and adversarial tests passed native Linux/POSIX, Windows HIGH_ASSURANCE and dedicated macOS validation. CR-001 exact head `12e38e98bb690e29494bab5e7a1c597a64b49765` passed Governance #322 and Desktop Shell #158 with HEDS H/C `0/0`. Product exact head `35745aa56e203fa819751aee4b70cce57a9600e7` passed Governance #323 and Desktop Shell #159 with final product HEDS H/C `0/0`, then merged as `06c68611a42e07b85ae765145d94bb613110ac14`, whose post-merge Governance #324 and Desktop Shell #160 passed. CP-0022 closeout exact head `a777ac207b42059a33ce9d73d8287122ff43c0a9` passed Governance #325 and Desktop Shell #161 with closeout HEDS review `5222180870`, H/C `0/0`, then merged as `795ed101eaf5d770f63a96db7f01a82369be34f1`. Post-closeout main validation passed Governance #326 and Desktop Shell #162.

## Canonical law
Future work may depend on `replace_file_v1` only within the exact bounded-race contract above. Any stronger publication guarantee, broader mutation authority, Git mutation, generic shell authority, append/delete/rename-existing behavior, desktop write authority or outside-workspace mutation requires a separate governed decision and Work Order.