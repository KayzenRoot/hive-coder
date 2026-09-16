# Evidence Bundle — HCODER-WO-0022

**Status:** OPEN / PREBUILT HARNESS  
**Canonical base:** `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Issue:** `#61`

## BASE PROOF
The CP-0021 source-of-truth reconciliation merge `9c2623f8b335cf29b63b5db5f43e694bfd77938e` passed exact-main push Governance #287 (`35044776040`) and Desktop Shell #123 (`35044775982`). This is the source base for WO-0022.

## PREBUILT ARTIFACTS
- Work Order: `.engineering/work-orders/HCODER-WO-0022.md`
- Context Lock: `.engineering/context-locks/HCODER-WO-0022.md`
- Implementation Pack: `.engineering/prebuilt/HCODER-WO-0022-IMPLEMENTATION-PACK.md`
- ADR candidate: `docs/project-brain/adrs/DEC-026-GOVERNED-EXISTING-FILE-REPLACEMENT.md`

## REQUIRED TECHNICAL EVIDENCE
Pending implementation. Record exact technical head and receipts for:
- compile/static/security gates;
- focused replacement contract tests;
- full Ubuntu unittest discovery;
- Windows HIGH_ASSURANCE replacement/control-plane suite;
- real POSIX late-race proof;
- real Windows NTFS reparse/junction + late-race proof;
- exact-head Governance and Desktop Shell;
- HEDS review and unresolved HIGH/CRITICAL counts.

## SECURITY CLAIMS TO PROVE
No claim below is accepted until objective tests/evidence exist:
1. approval binds exact old target and exact new bytes;
2. concurrent target substitution/content change fails closed;
3. no link/reparse/outside-root escape;
4. no in-place truncate fallback;
5. permit replay/staleness/wrong binding fails closed;
6. cancellation/takeover/emergency stop blocks pre-commit mutation;
7. cleanup cannot remove an unverified concurrent object;
8. `write_file_v1` create-only semantics remain unchanged.

## STOP
Do not mark COMPLETE, APPROVED or CANONICAL from scaffold presence. Promotion requires implementation evidence and exact-head audit.