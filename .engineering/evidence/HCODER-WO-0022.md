# Evidence Bundle — HCODER-WO-0022

**Status:** OPEN / CR-001 POSIX PUBLICATION PROVEN — WINDOWS MUTATION NOT YET PROVEN  
**Canonical base:** `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Issue:** `#61`

## BASE PROOF
The CP-0021 source-of-truth reconciliation merge `9c2623f8b335cf29b63b5db5f43e694bfd77938e` passed exact-main push Governance #287 (`35044776040`) and Desktop Shell #123 (`35044775982`). This is the source base for WO-0022.

## PREBUILT / CORRECTION ARTIFACTS
- Work Order: `.engineering/work-orders/HCODER-WO-0022.md`
- Context Lock: `.engineering/context-locks/HCODER-WO-0022.md`
- Correction Delta: `.engineering/corrections/HCODER-WO-0022-CR-001.md`
- CAS feasibility record: `.engineering/evidence/HCODER-WO-0022-CAS-FEASIBILITY.md`
- Implementation Pack: `.engineering/prebuilt/HCODER-WO-0022-IMPLEMENTATION-PACK.md`
- Executor Brief: `.engineering/prebuilt/HCODER-WO-0022-EXECUTOR-BRIEF.md`
- ADR candidate: `docs/project-brain/adrs/DEC-026-GOVERNED-EXISTING-FILE-REPLACEMENT.md`
- Contract/protocol: `hive_runtime/workspace_replace_contract.py`, `hive_runtime/workspace_replace_backend.py`
- POSIX implementation: `hive_runtime/workspace_replace_posix.py`
- Windows corrected fail-closed seam: `hive_runtime/workspace_replace_windows.py`

## HISTORICAL PREBUILT EXACT-HEAD VALIDATION
- `c820ee0808c8424efbca58d69725c3bbac72c1ef`: Governance #288 SUCCESS; Desktop Shell #124 SUCCESS.
- `0e5a88d61160080088d1b088d6cabc77239c879d`: Governance #289 SUCCESS; Desktop Shell #125 SUCCESS.
- `3de2f66196c2b10457b0674e3bc78a37e803c321`: Governance #290 SUCCESS; Desktop Shell #126 SUCCESS.
These heads validated guardrails/prebuilt surfaces only, not mutation.

## CR-001 CONTRACT
Strict expected-target CAS is not claimed portable. The selected candidate is bounded-race atomic replacement: exact approved old identity/content + exact new bytes, latest safe live revalidation, same-filesystem verified staging, atomic native namespace publication, identity-owned cleanup, and explicit residual external-process race after final revalidation where the OS exposes no expected-destination identity predicate.

A valid permit must not be consumed merely to discover unavailable/unimplemented publication. The capability now reaches backend staging + `mutation_ready` before permit consumption.

## POSIX TECHNICAL PROOF
Initial POSIX publication head `d9ab677b7c0d9a5cafd8ce9dc9bb831369aa26a2` exposed a real test defect: staging used `O_WRONLY` while digest verification used `pread`, producing `EBADF`. Tests were not weakened.

Correction head `6644ceebfa54d5cfa8c68b1e6c547764ea97be83` changed staging to `O_RDWR | O_CREAT | O_EXCL` while preserving no-follow, same-parent/same-filesystem and identity verification.

Exact-head results for `6644ceebfa54d5cfa8c68b1e6c547764ea97be83`:
- Governance #292 (`35050491086`): SUCCESS.
- Desktop Shell #128 (`35050491123`): SUCCESS.
- POSIX focused tests prove unchanged-state revalidation, in-place content-change rejection, pathname inode substitution rejection, symlink rejection, staging without destination mutation, identity-owned temp cleanup, stale owner rejection after staging, successful atomic publication of verified bytes, and pre-publication failure preserving the destination.

This evidence proves the declared CR-001 POSIX behavior under the tested native surface. It does not convert POSIX rename into strict CAS and does not claim elimination of the documented final external-writer interval.

## WINDOWS CURRENT GATE
The prior Windows skeleton still described strict CAS and no longer matched CR-001. It has been corrected to the same staged protocol: `revalidate_expected`, `stage_replace`, `mutation_ready`, `publish_replace`, `close`. Until the native implementation exists, every mutation-reaching method deliberately raises `NotImplementedError`.

`tests/runtime/test_workspace_file_replace_windows_contract.py` freezes that fail-closed law and the corrected protocol. The Governance Windows HIGH_ASSURANCE lane now explicitly executes this test. Therefore Windows cannot silently inherit POSIX support or accidentally reach mutation through the old skeleton.

Current Windows native mutation status: **NOT PROVEN / FAIL-CLOSED**.

## REMAINING REQUIRED TECHNICAL EVIDENCE
- Windows handle-pinned target digest/identity observation and latest live revalidation;
- Windows same-volume exclusive staging, flush, exact digest/length and identity proof;
- Windows native atomic publication selected under CR-001, with real NTFS substitution/reparse/junction/publication-failure tests;
- permit-not-burned failure-path tests and exactly-once successful consumption proof;
- macOS/Darwin native lane/evidence under Issue #63 before macOS support is claimed;
- full regression, exact-head Governance/Desktop Shell after final implementation;
- HEDS review with unresolved HIGH/CRITICAL = 0.

## SECURITY CLAIMS
Currently proven for the tested POSIX implementation: exact request old/new binding, observable stale target rejection, no-follow path/target protection, staged atomic publication rather than truncate-in-place, identity-owned staging cleanup, and preservation of CP-0021 create-only behavior through regression gates.

Still pending cross-platform/native evidence: Windows reparse/junction/race behavior, final permit ordering receipts, macOS native behavior, and full promotion audit.

## STOP
Do not mark COMPLETE, APPROVED or CANONICAL. PR #64 remains a same-WO draft correction. Windows mutation and macOS evidence are not yet complete, and HEDS/promotion have not occurred.