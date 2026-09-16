# HCODER-WO-0022 — Governed Existing-File Replacement Capability

**Status:** COMPLETE — CANONICALIZED BY `HCODER-CP-0022`  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Canonical result:** `HCODER-CP-0022` / `795ed101eaf5d770f63a96db7f01a82369be34f1`  
**Decision:** `DEC-026` CANONICAL  
**Issue:** `#61`  
**Correction:** `HCODER-WO-0022-CR-001`

## OBJECTIVE
Add the smallest coding-enabling workspace mutation boundary after create-only: atomically publish replacement bytes for one already-existing regular file inside the trusted workspace while binding approval to the exact observed old target state and exact new content and failing closed on every observable stale-state condition before publication.

## COMPLETED CONTRACT
- capability: `FILESYSTEM_WRITE`;
- fixed action: `replace_file_v1`;
- target: normalized trusted-workspace-relative regular file;
- request binds canonical workspace identity, normalized path, parent identity, exact observed old target identity, old content SHA-256/length, new content SHA-256/length and contract version;
- raw old/new content is absent from approval/audit metadata;
- maximum new payload remains 1 MiB unless separately justified;
- permit is mandatory, request-bound, short-lived and single-use;
- live session/workspace/parent/target identity and old digest/length are revalidated as late as the platform safely permits before publication;
- publication uses platform-proven atomic namespace replacement on supported local filesystems;
- every stale condition observable before publication fails closed;
- temporary cleanup removes only capability-created objects whose identity/ownership is verified;
- permit consumption occurs at the final mutation-ready boundary and is not burned merely to reach an unimplemented/unavailable publication seam;
- canonical guarantee is **bounded-race atomic replacement**, not strict expected-target/inode CAS.

## EXPLICIT RESIDUAL-RACE LAW
An uncooperative external actor may change the destination pathname after Hive's final successful observable revalidation and before the native atomic publication call where the OS interface has no expected-target predicate. This interval is explicit, bounded by the selected contract and MUST NOT be represented as strict CAS.

## OBJECTIVE COMPLETION EVIDENCE
CR-001 exact head `12e38e98bb690e29494bab5e7a1c597a64b49765` passed Governance #322 and Desktop Shell #158 with native Windows/macOS proof and HEDS H/C `0/0`. Product exact head `35745aa56e203fa819751aee4b70cce57a9600e7` passed Governance #323 and Desktop Shell #159 with final HEDS H/C `0/0`, then merged as `06c68611a42e07b85ae765145d94bb613110ac14`; post-merge Governance #324 and Desktop Shell #160 passed. CP-0022 closeout exact head `a777ac207b42059a33ce9d73d8287122ff43c0a9` passed Governance #325 and Desktop Shell #161 with HEDS closeout review `5222180870`, H/C `0/0`, then merged as `795ed101eaf5d770f63a96db7f01a82369be34f1`. Post-closeout Governance #326 and Desktop Shell #162 passed.

## PRESERVED EXCLUSIONS
Append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, Git mutation, generic shell/terminal execution, outside-workspace mutation, Tauri/desktop write authority, provider/model credentials/execution expansion, Cua/computer-use expansion, remote control, billing/purchases and automatic skill activation remain outside this Work Order.

## FINAL STOP CONDITION
WO-0022 is closed. Future work MUST NOT silently broaden `replace_file_v1` or rewrite its bounded-race guarantee as strict CAS. Any stronger publication guarantee or broader authority requires a new governed Work Order and decision.