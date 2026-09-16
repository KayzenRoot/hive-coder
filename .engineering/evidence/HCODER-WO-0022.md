# Evidence Bundle — HCODER-WO-0022

**Status:** CR-001 TECHNICAL EVIDENCE COMPLETE / PROMOTION AUDIT PENDING  
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
- Windows implementation: `hive_runtime/workspace_replace_windows.py`, `hive_runtime/workspace_files_windows.py`

## CR-001 CONTRACT
Strict expected-target CAS is not claimed portable. The selected candidate is bounded-race atomic replacement: exact approved old identity/content + exact new bytes, latest safe live revalidation, same-filesystem verified staging, atomic native namespace publication, identity-owned cleanup, and explicit residual external-process race after final revalidation where the OS exposes no expected-destination identity predicate.

A valid permit is not consumed merely to discover stale state, staging failure, or unavailable/unimplemented publication. The capability reaches backend staging + `mutation_ready` before permit consumption. Successful execution orders `mutation_ready -> consume_execution_permit -> publish_replace`.

## POSIX / LINUX TECHNICAL PROOF
Initial POSIX publication head `d9ab677b7c0d9a5cafd8ce9dc9bb831369aa26a2` exposed a real staging defect: `O_WRONLY` was incompatible with digest verification through `pread`. Tests were not weakened. Head `6644ceebfa54d5cfa8c68b1e6c547764ea97be83` corrected staging to `O_RDWR | O_CREAT | O_EXCL` while preserving no-follow, same-parent/same-filesystem and identity verification; Governance #292 and Desktop Shell #128 passed.

Subsequent hardening captures staging identity immediately after exclusive creation, reopens the live staging pathname no-follow, compares pinned/live identity and digest/length, repeats that proof at `mutation_ready` and immediately before atomic rename, and refuses cleanup when ownership of the live pathname cannot be proven.

Adversarial tests now prove target stale-content rejection, target pathname identity substitution rejection, symlink target/parent rejection, staging-pathname substitution rejection, staging-byte tamper rejection, attacker-swapped pathname preservation during cleanup, exact verified-byte publication, and pre-publication failure preserving destination.

Exact-head `0ef9c0458c88ed5e0701e63360f2131358870420`: Governance #317 SUCCESS; Desktop Shell #153 SUCCESS.

## PERMIT ORDERING PROOF
Exact-head `634749e282ba3bcd889f021aaac65fb808a8d397`: Governance #318 SUCCESS; Desktop Shell #154 SUCCESS.

Tests use the real `PermissionControlPlane`, real control session, approval challenge, trusted-UI approval, request-bound execution permit and audit events. They prove:
- stale state before mutation readiness does not consume the permit;
- staging failure does not consume the permit;
- `NotImplementedError`/unsupported publication discovered at mutation readiness does not consume the permit;
- successful replacement observes `mutation_ready -> permit consumed -> publish` ordering.

## WINDOWS NATIVE TECHNICAL PROOF
The Windows correction retained handle-pinned/no-follow traversal and added same-volume verified staging plus native atomic namespace replacement. Failed intermediate experiments were retained as engineering history rather than hidden: parent/target authority and Win32/native information-class mismatches produced objective runner failures until the publication primitive was corrected.

The accepted native primitive uses `NtSetInformationFile` with native `FileRenameInformationEx` class 65 and replacement/POSIX semantics flags. After successful namespace publication, obsolete target/staging handles are released only after publication verification so ordinary consumers can reopen the new pathname.

Exact-head `fc471accbde126407b094e66966b9864a8de8453`: Governance #315 SUCCESS, including `control-plane-windows`; Desktop Shell #151 SUCCESS. This closed the native Windows atomic publication blocker.

Later exact-head `7184e32c12d9001236c01063350111d10d0de4bc`: Governance #319 SUCCESS with `control-plane-windows` SUCCESS, confirming the Windows lane remained green after POSIX hardening, permit-ordering tests and macOS-lane addition.

## macOS / DARWIN NATIVE TECHNICAL PROOF
macOS support is no longer inferred from Linux/POSIX behavior. Governance now has a dedicated `workspace-replace-macos` job on `macos-latest` with exact-head checkout, runtime compilation, replacement contract tests and adversarial replacement-security tests.

Exact-head `7184e32c12d9001236c01063350111d10d0de4bc`:
- Governance #319 (`35088335237`): SUCCESS.
- Desktop Shell #155 (`35088335266`): SUCCESS.
- `workspace-replace-macos`: SUCCESS.
- exact checkout: `7184e32c12d9001236c01063350111d10d0de4bc`.
- runner: macOS 26.6.2 build 25G83, `macos-26-arm64` image, Python 3.14.7.
- native focused suite: 18 tests, all passed, 0 failures/errors.

This proves the selected POSIX backend and its dir-fd atomic publication path execute successfully on the tested native macOS runner, including the current adversarial and permit-ordering suite. It does not expand the contract beyond bounded-race atomic replacement.

## CURRENT CROSS-PLATFORM GATE
At exact-head `7184e32c12d9001236c01063350111d10d0de4bc`, Governance #319 reports all three jobs green:
- `source-pack`: SUCCESS;
- `control-plane-windows`: SUCCESS;
- `workspace-replace-macos`: SUCCESS.
Desktop Shell #155 is also SUCCESS.

The declared CR-001 technical behavior now has native CI evidence across Linux/POSIX, Windows and macOS. No strict CAS claim is made on any platform. The documented residual external-process race after the final observable revalidation remains part of the contract.

## SECURITY CLAIMS PROVEN BY CURRENT TECHNICAL EVIDENCE
- exact request binding to approved old identity/content and exact new digest/length;
- workspace-root and parent identity revalidation;
- no-follow/reparse-resistant governed traversal under tested platform implementations;
- stale target rejection before publication when observable;
- verified same-filesystem staging rather than truncate-in-place;
- live staging pathname identity/digest revalidation on POSIX/Darwin;
- identity-owned cleanup that refuses to delete a swapped attacker pathname;
- request-bound single-use permit consumed only after mutation readiness;
- native atomic namespace publication on tested Linux/POSIX, Windows and macOS runners;
- post-publication identity/byte verification without misrepresenting that verification as strict CAS;
- preservation of CP-0021 create-only behavior through regression gates.

## REMAINING PROMOTION EVIDENCE
Technical implementation evidence is complete for CR-001. The remaining gates are governance/promotion gates, not missing platform implementation:
1. exact-head Governance/Desktop Shell after this evidence consolidation commit;
2. HEDS review of the complete CR-001 diff with unresolved HIGH/CRITICAL = 0;
3. integrate the accepted same-WO correction into the product WO-0022 branch/PR without weakening evidence;
4. product exact-head gates and product HEDS;
5. product merge, post-merge validation, CP-0022 canonical closeout and only then promotion of DEC-026 from PROPOSED to canonical.

## STOP
Do not mark WO-0022 COMPLETE, APPROVED or CANONICAL yet. PR #64 remains the same-WO correction under promotion audit. Technical cross-platform proof is complete, but HEDS and product promotion/closeout have not occurred.