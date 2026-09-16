# DEC-026 — Governed Existing-File Replacement Capability

**Status:** PROPOSED / NOT CANONICAL  
**Work Order:** `HCODER-WO-0022`  
**Source checkpoint:** `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`

## Context
CP-0021 canonicalized safe creation of a previously absent regular workspace file. Practical code editing next requires changing an existing file, but ordinary overwrite/rename APIs do not by themselves prove that the object approved by the user is still the object replaced at commit time.

## Proposed decision
Introduce a distinct Hive-owned `replace_file_v1` action under existing `FILESYSTEM_WRITE` authority. Approval and permit binding must include the canonical workspace, normalized target, parent identity, exact old target identity, old content digest/length and new content digest/length. The executor revalidates live state and consumes the single-use permit immediately before mutation.

Replacement must provide platform-proven expected-target semantics. A concurrent actor replacing/changing the approved target causes failure rather than silent clobber. Link/reparse traversal, `.git`, non-regular targets and outside-workspace paths fail closed.

## Non-decision
This ADR does not approve append, truncate-in-place, delete, arbitrary rename/move, Git mutation, terminal/shell execution, desktop/Tauri mutation, outside-workspace mutation or any broader capability.

## Promotion condition
Remain NOT CANONICAL until implementation, native race/reparse tests, exact-head Governance/Desktop gates as applicable, HEDS with unresolved HIGH/CRITICAL 0, product merge, post-merge exact-SHA validation and canonical closeout all succeed.