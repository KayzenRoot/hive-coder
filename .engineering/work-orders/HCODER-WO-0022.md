# HCODER-WO-0022 — Governed Existing-File Replacement Capability

**Status:** IN PROGRESS — CR-001 BOUNDED-RACE CONTRACT SELECTED / MUTATION NOT YET PROVEN  
**Risk:** HIGH_ASSURANCE  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0021` / `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Issue:** `#61`  
**Implementation branch:** `feat/HCODER-WO-0022-existing-file-replacement`  
**Correction:** `HCODER-WO-0022-CR-001`

## OBJECTIVE
Add the smallest next coding-enabling workspace mutation boundary: atomically publish replacement bytes for one already-existing regular file inside the trusted workspace, while binding approval to the exact observed old target state and exact new content and failing closed on every observable stale-state condition before publication.

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

## CORRECTED CONTRACT — CR-001
- capability: `FILESYSTEM_WRITE`;
- fixed action: `replace_file_v1`;
- target: normalized trusted-workspace-relative regular file;
- request binds canonical workspace identity, normalized path, parent identity, exact observed old target identity, old content SHA-256/length, new content SHA-256/length and contract version;
- raw old/new content is absent from approval/audit metadata;
- maximum new payload remains 1 MiB unless separately justified;
- permit is mandatory, request-bound, short-lived and single-use;
- live session/workspace/parent/target identity and old digest/length are revalidated as late as the platform safely permits before publication;
- publication of the replacement bytes must be an atomic namespace replacement on supported local filesystems;
- every target substitution/content change observable before publication fails closed and preserves the concurrent owner;
- the system MUST NOT claim that ordinary workspace-file replacement provides strict expected-inode CAS against an uncooperative external process in the final interval between the last successful revalidation and the OS atomic publication operation;
- this residual external-process interval is an explicit bounded platform assumption, not hidden or described as CAS;
- temporary cleanup may remove only a capability-created object whose identity is verified;
- permit consumption occurs only at the last safe mutation-ready boundary and MUST NOT be burned merely to reach an unimplemented publication seam.

## PLATFORM LAW
Windows, Linux and macOS may use different OS primitives but must prove the corrected Hive contract on their supported filesystems. Atomic replacement and strict expected-target CAS are distinct properties. A platform may be marked supported only when native tests prove root/link/reparse safety, atomic publication, prepublication stale-state rejection, cleanup ownership and permit ordering. Unsupported platform/filesystem combinations fail closed and surface capability unavailability.

Issue #63 / HCODER-PLATFORM-001 owns the first-class Windows/Linux/macOS validation matrix. Darwin guarantees must not be inferred from Linux tests.

## EXPLICIT RESIDUAL-RACE LAW
Hive can bind approval to exact observed target identity/content and revalidate immediately before publication. The documented native replacement interfaces evaluated by CR-001 do not expose a portable predicate requiring the destination at publication time to still be that exact approved identity. Therefore an uncooperative external actor that changes the pathname after the final successful revalidation but before the atomic OS publication may race the operation. WO-0022 does not conceal this interval and does not represent the result as strict CAS.

Within Hive-controlled execution, cancellation/session/permit/state checks remain mandatory through the final safe boundary. A future versioned/content-addressed workspace architecture may eliminate or relocate this assumption under a separate architectural decision.

## OUT OF SCOPE
Append, truncate-in-place, delete, arbitrary rename/move, recursive mutation, chmod/chown, Git mutation, generic shell/terminal execution, outside-workspace mutation, Tauri/desktop write authority, provider/model credentials/execution expansion, Cua/computer-use expansion, remote control, billing/purchases and skill activation.

## ACCEPTANCE CRITERIA
- exact workspace/path/parent/observed-old-target/old-content/new-content approval binding proven;
- non-existing target rejected for this action;
- directory/device/link/reparse/`.git`/unsafe path targets rejected;
- wrong/stale/replayed permit rejected;
- target replacement or content change observable before publication fails closed and preserves the concurrent owner;
- workspace or parent identity replacement fails closed;
- cancellation/emergency/takeover before the last safe mutation boundary prevents mutation;
- successful replacement yields exactly approved new bytes via platform-proven atomic namespace publication;
- publication/cleanup failure cannot delete or overwrite an unverified capability-created temporary object;
- no test, code, receipt, ADR or UI calls the corrected operation strict CAS;
- Ubuntu/Linux, Windows HIGH_ASSURANCE and dedicated macOS/Darwin evidence are required before each platform is declared supported;
- exact-head HEDS unresolved HIGH/CRITICAL = 0 before promotion.

## STOP CONDITION
Do not hide or broaden the CR-001 residual-race assumption. Do not weaken identity, no-follow/reparse, root-boundary, permit or atomic-publication guarantees to obtain a passing implementation. Do not expand authority beyond `replace_file_v1`. Any need for Git, shell, append/delete/rename-existing, desktop write or outside-workspace mutation requires a later Work Order.