# Evidence Bundle — HCODER-WO-0022

**Status:** OPEN / PREBUILT HARNESS VALIDATED — MUTATION NOT PROVEN  
**Canonical base:** `9c2623f8b335cf29b63b5db5f43e694bfd77938e`  
**Issue:** `#61`

## BASE PROOF
The CP-0021 source-of-truth reconciliation merge `9c2623f8b335cf29b63b5db5f43e694bfd77938e` passed exact-main push Governance #287 (`35044776040`) and Desktop Shell #123 (`35044775982`). This is the source base for WO-0022.

## PREBUILT ARTIFACTS
- Work Order: `.engineering/work-orders/HCODER-WO-0022.md`
- Context Lock: `.engineering/context-locks/HCODER-WO-0022.md`
- Implementation Pack: `.engineering/prebuilt/HCODER-WO-0022-IMPLEMENTATION-PACK.md`
- Executor Brief: `.engineering/prebuilt/HCODER-WO-0022-EXECUTOR-BRIEF.md`
- ADR candidate: `docs/project-brain/adrs/DEC-026-GOVERNED-EXISTING-FILE-REPLACEMENT.md`
- Contract: `hive_runtime/workspace_replace_contract.py`
- Cross-platform backend protocol: `hive_runtime/workspace_replace_backend.py`
- POSIX/Windows replacement seams and focused contract/security/platform tests.

## PREBUILT EXACT-HEAD VALIDATION
### Head `c820ee0808c8424efbca58d69725c3bbac72c1ef`
- Governance #288 (`35046378950`): SUCCESS.
- Desktop Shell #124 (`35046379006`): SUCCESS.
- This validates the prebuilt/read-only seams only. It is not replacement-mutation evidence.

### Native CAS feasibility gate head `0e5a88d61160080088d1b088d6cabc77239c879d`
- Governance #289 (`35047294778`): SUCCESS.
- Desktop Shell #125 (`35047294785`): SUCCESS.
- Desktop web: SUCCESS.
- Desktop Windows: SUCCESS, including exact-head checkout, Rust dependency audit, locked Rust tests/check, Tauri Windows build and launch smoke as defined by the workflow.
- The implementation pack now explicitly rejects validation-followed-by-ordinary-rename/replace as proof of expected-target CAS semantics.
- This validates the guardrail and existing surfaces. It does not prove `replace_file_v1` publication.

## NATIVE CAS FEASIBILITY FINDING
The required contract is stronger than ordinary atomic rename: publication must not silently clobber a target that changed after approval/revalidation. Current prebuilt POSIX and Windows publication seams therefore remain fail-closed until a native or cooperatively governed mechanism can prove expected-target semantics under a real late race.

A same-WO Correction Delta is required if the strict expected-target publication law cannot be implemented with an objectively testable native primitive. No fallback to `os.replace`, ordinary `rename`, `MoveFileEx`, `ReplaceFile`, truncate-and-rewrite, or path-only validation is authorized merely to make tests green.

## REQUIRED TECHNICAL EVIDENCE
Pending mutation implementation/correction design. Record exact technical head and receipts for:
- compile/static/security gates;
- focused replacement contract tests;
- full Ubuntu unittest discovery;
- Windows HIGH_ASSURANCE replacement/control-plane suite;
- real POSIX late-race proof;
- real Windows NTFS reparse/junction + late-race proof;
- exact-head Governance and Desktop Shell;
- HEDS review and unresolved HIGH/CRITICAL counts.

## SECURITY CLAIMS TO PROVE
No claim below is accepted until objective mutation tests/evidence exist:
1. approval binds exact old target and exact new bytes;
2. concurrent target substitution/content change fails closed;
3. no link/reparse/outside-root escape;
4. no in-place truncate fallback;
5. permit replay/staleness/wrong binding fails closed;
6. cancellation/takeover/emergency stop blocks pre-commit mutation;
7. cleanup cannot remove an unverified concurrent object;
8. `write_file_v1` create-only semantics remain unchanged.

## STOP
Do not mark COMPLETE, APPROVED or CANONICAL from scaffold presence or green prebuilt gates. Promotion requires proven mutation semantics, adversarial native race evidence and exact-head audit.