# HCODER-WO-0022 — Governed Existing-File Replacement Capability

**Status:** IN PROGRESS — PREBUILT HARNESS  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Issue:** `#61`  
**Branch:** `feat/HCODER-WO-0022-existing-file-replacement`

## OBJECTIVE
Add the smallest next coding-enabling workspace mutation boundary: atomically replace one already-existing regular file inside the trusted workspace, with compare-and-swap style binding to the exact approved old target state and exact new content.

## NECESSITY
Canonical Requirements require coding plus terminal/files orchestration and Git-aware governed execution. CP-0021 proves only create-new/no-clobber. Existing-file replacement is the minimum next mutation needed for practical code editing and should be proven independently before Git mutation or generic terminal authority.

## PREBUILT IMPLEMENTATION HARNESS
Implementation-heavy execution must begin from prebuilt contracts rather than rediscovering architecture. This WO requires, before promotion:
1. Context Lock bound to exact canonical base and source hierarchy.
2. Exact allowed-file and symbol map.
3. Versioned replacement request/receipt contract.
4. Platform adapter skeletons with explicit signatures and invariants.
5. Acceptance/adversarial tests written around the intended contract.
6. Race, symlink/reparse, target-identity and stale-permit fixtures.
7. Evidence Bundle template and ADR candidate.
8. STOP conditions encoded in tests/review law where practical.

No vague TODO-only scaffold is acceptable. Prebuilt files must materially constrain implementation choices and reduce executor discovery work.

## PROPOSED CONTRACT
- capability: `FILESYSTEM_WRITE`;
- fixed action: `replace_file_v1`;
- target: normalized trusted-workspace-relative regular file;
- request binds canonical workspace identity, normalized path, parent identity, exact old target identity, old content SHA-256/length, new content SHA-256/length and contract version;
- raw old/new content is absent from approval/audit metadata;
- maximum new payload remains 1 MiB unless separately justified;
- permit is mandatory, request-bound, short-lived and single-use;
- live session/workspace/parent/target identity and old digest/length are revalidated before permit consumption/mutation;
- publication must not silently overwrite a concurrently replaced target;
- temporary cleanup may remove only a capability-created object whose identity is verified.

## PLATFORM LAW
POSIX and Windows implementations may use different OS primitives but must prove the same Hive contract. Do not claim portable atomic CAS semantics unless the exact platform primitive and adversarial tests prove them. If an OS cannot meet the contract, fail closed or stop the WO rather than weakening guarantees.

## OUT OF SCOPE
Append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, Git mutation, generic shell/terminal execution, outside-workspace mutation, Tauri/desktop write authority, provider/model credentials/execution expansion, Cua/computer-use expansion, remote control, billing/purchases and skill activation.

## ACCEPTANCE CRITERIA
- exact workspace/path/parent/old-target/old-content/new-content binding proven;
- non-existing target rejected for this action;
- directory/device/link/reparse/`.git`/unsafe path targets rejected;
- wrong/stale/replayed permit rejected;
- target replacement or content change after approval fails closed and preserves the concurrent owner;
- workspace or parent identity replacement fails closed;
- cancellation/emergency/takeover before commit prevents mutation;
- successful replacement yields exactly approved new bytes and bounded receipt metadata;
- publication/cleanup failure cannot delete or overwrite an unverified object;
- Ubuntu full suite and Windows HIGH_ASSURANCE suite green;
- exact-head HEDS unresolved HIGH/CRITICAL = 0 before promotion.

## STOP CONDITION
Do not weaken identity, no-follow/reparse, TOCTOU or compare-and-swap guarantees to obtain a passing implementation. Do not expand authority beyond `replace_file_v1`. Any need for Git, shell, append/delete/rename-existing, desktop write or outside-workspace mutation requires a later Work Order.