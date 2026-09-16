# Executor Brief — HCODER-WO-0022 / CR-001

This is the minimal handoff for the implementation executor.

## READ FIRST
1. `.engineering/context-locks/HCODER-WO-0022.md`
2. `.engineering/work-orders/HCODER-WO-0022.md`
3. `.engineering/corrections/HCODER-WO-0022-CR-001.md`
4. `.engineering/evidence/HCODER-WO-0022-CAS-FEASIBILITY.md`
5. `.engineering/prebuilt/HCODER-WO-0022-IMPLEMENTATION-PACK.md`
6. `docs/project-brain/adrs/DEC-025-TRUSTED-WORKSPACE-FILE-CAPABILITY.md`
7. `docs/project-brain/adrs/DEC-026-GOVERNED-EXISTING-FILE-REPLACEMENT.md`
8. `hive_runtime/workspace_replace_contract.py`
9. current `hive_runtime/workspace_files*.py` and `workspace_replace*.py`
10. focused replacement tests.

## JOB
Complete only `replace_file_v1` under the CR-001 **bounded-race atomic replacement** contract. Preserve `write_file_v1` exactly. Do not redesign adjacent authority surfaces.

## EXPECTED SYMBOLS
`WorkspaceFileCapability.prepare_replace_request(...)`
`WorkspaceFileCapability.replace_bytes(...)`
Backend `prepare_replace(...)` plus a prepared-target object that exposes observed state, exact prepublication revalidation, mutation-ready staging/publication and identity-owned cleanup.

## NON-NEGOTIABLES
Approval binds observed old identity+digest+length and exact new digest+length. Raw bytes never enter request/audit metadata. Workspace, parent and target are revalidated as late as safely possible. `.git`, traversal, symlink/reparse and non-regular targets fail closed. Staging is same-filesystem and identity-owned. Final publication is atomic on declared-supported platform/filesystem combinations. No truncate-in-place, cross-filesystem copy fallback, generic rename/delete surface, shell or Git authority.

**Do not call the operation strict CAS.** CR-001 explicitly documents the residual race from an uncooperative external process acting after the final successful revalidation and before a native publication call that lacks an expected-destination identity predicate.

## PERMIT LAW
Do not consume a valid permit merely to discover `NotImplemented`, unsupported platform/filesystem, staging failure or stale prepublication state. Reach a real mutation-ready path first, then consume the request-bound single-use permit at the last safe point immediately associated with publication. Preserve cancellation/session checks through that boundary. Add objective tests for permit-not-burned failure paths and single consumption on success.

## IMPLEMENTATION SEQUENCE
1. Minimal protocol refinement for staging/mutation readiness if needed.
2. POSIX staging + exact final revalidation + atomic same-filesystem publication + owned cleanup.
3. Fix capability-level permit ordering.
4. Focused POSIX contract/security/race tests plus existing create-only regression.
5. Windows handle/reparse-resistant revalidation + staging + publication + native race tests.
6. macOS/Darwin native lane/evidence under Issue #63 before macOS support is claimed.
7. Full Python discovery, Windows HIGH_ASSURANCE, exact-head Governance/Desktop Shell, evidence/HEDS.

## REQUIRED ASSERTION LANGUAGE
Tests and evidence may assert:
- stale state observed before publication fails closed;
- successful publication yields exactly approved bytes atomically under the selected native primitive;
- cleanup is identity-owned;
- permit ordering/replay/cancellation behavior is proven.

Tests and evidence MUST NOT assert:
- strict expected-inode CAS across the final external-process race interval;
- that advisory/cooperative locking prevents arbitrary external writers;
- cross-platform equivalence without native evidence.

## STOP
If a platform/filesystem cannot prove atomic publication plus the root/link/reparse/cleanup/permit guarantees of CR-001, fail closed and mark that capability combination unavailable. Do not substitute weaker mutation semantics merely to make the suite green.