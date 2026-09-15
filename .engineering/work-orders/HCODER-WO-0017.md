# HCODER-WO-0017 — Runtime Observability Contract & Safe Status Export

**Status:** COMPLETE / CANONICAL  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C4  
**Canonical base:** `HCODER-CP-0016` on `main` at `442733aeae6bd2f615dc0bc4c76dda024455c212`  
**Issue:** `#41`

## OBJECTIVE
Create a Hive-owned, bounded, read-only runtime observability contract that truthfully exports runtime/provider/task/permission presentation state from the already-existing Python engines without exposing credentials, prompts, model output, permits, approval tokens or mutation authority. This establishes the trusted data source required before the desktop may claim live runtime/provider/permission readiness.

## CONTEXT
HCODER-CP-0016 is canonical. The trusted workspace/Git/evidence read surface is merged and post-merge validated. The canonical backlog says the next NECESSARY product work is truthful live runtime/provider/permission read state and explicitly forbids rebuilding the existing Python runtime/provider/task/control-plane engines.

Existing reusable surfaces include `ProviderCatalog`, `ModelCapabilityRegistry`, `AgentTaskRuntime`, the Permission & Control Plane, `ManagedStdioProcess`, JSON-RPC and Hive-owned provider/interpreter adapters.

A prior stacked technical candidate of this same Work Order was validated before CP-0016 canonicalization. This canonical execution branch replays only the five-file WO-0017 delta over the canonical CP-0016 base; no pre-squash WO-0016 history is carried forward.

## SCOPE
- Add a versioned `RuntimeStatusSnapshot` presentation contract in Python.
- Add bounded status builders/adapters for runtime, provider/model catalog, task runtime and permission/control-plane state.
- Export only non-secret presentation metadata with explicit provenance and READY/UNKNOWN/DISCONNECTED/DEGRADED semantics.
- Add a deterministic JSON encoder/decoder validation boundary with hard size/count/string ceilings.
- Add a read-only CLI entrypoint suitable for later trusted desktop IPC tests; the CLI must not start providers, call models, mint permits, approve requests or mutate task state.
- Add tests proving redaction, bounded output, malformed-state fail-closed behavior and zero authority expansion.

## OUT OF SCOPE
- Desktop subprocess launch or IPC transport.
- Provider network calls or credential loading.
- Model prompt execution.
- Runtime process spawning from the desktop.
- Task pause/resume/cancel mutation.
- Approval/permit mutation.
- File/Git mutation, terminal execution or computer-use mutation.
- Remote control, billing/purchases or automatic skill activation.

## FILES / SOURCES TO READ
- `hive_runtime/providers.py`
- `hive_runtime/agent_tasks.py`
- `hive_runtime/control_plane.py`
- `hive_runtime/control_types.py`
- `hive_runtime/process.py`
- `hive_runtime/jsonrpc.py`
- `docs/project-brain/04-ARCHITECTURE.md`
- `docs/project-brain/05-SECURITY.md`
- `docs/project-brain/08-BACKLOG.md`
- `docs/project-brain/13-INTEGRATION-CONTRACTS.md`

## REQUIREMENTS
1. Status output is presentation data only and cannot be consumed as authorization.
2. Unknown/unconnected subsystems are never reported READY.
3. Provider observations cannot imply VERIFIED capability without existing trusted registry evidence.
4. Credential values, raw prompts/model output, permits, approval secrets and audit secret material are excluded.
5. All strings/collections/output bytes are bounded deterministically.
6. Serialization failure or invalid data maps to explicit degraded/fail-closed status.
7. The CLI performs no subprocess/provider/model/network/mutation operation.
8. CP-0005 through CP-0016 authority boundaries remain unchanged.

## ARCHITECTURE RULES
`Existing Python engines -> Hive RuntimeStatusAdapter -> RuntimeStatusSnapshot v1 -> later trusted IPC -> desktop presentation`.

The snapshot is not an authority root. Status adapters may inspect public state only and must not reach into secret-bearing private members when a safe public observation cannot be made. If a subsystem has no safe observation API, report UNKNOWN and add a narrow read-only observation method under this Work Order rather than serializing internals wholesale.

## CONSTRAINTS
- Python stdlib only unless a dependency is objectively necessary.
- No ambient credential enumeration.
- No arbitrary module/class reflection over runtime internals.
- No generic command execution.
- No unbounded dict/list passthrough from providers/tasks.
- Preserve backward compatibility for existing runtime APIs/tests.

## ACCEPTANCE CRITERIA
- `RuntimeStatusSnapshot v1` validates bounded runtime/provider/task/permission state.
- A deterministic CLI can emit one bounded JSON snapshot using safe fixture/default observers without invoking external providers.
- Secret-like values injected into source objects do not appear in serialized status.
- Provider/model counts and identifiers are bounded and capability truth remains evidence-driven.
- Task/permission summaries expose state/count/epoch-like presentation values only, never permit material.
- Existing Governance tests remain green and new status tests pass.
- HEDS finds no unresolved HIGH/CRITICAL issue.

## TESTS
- runtime status schema and byte ceiling;
- secret redaction/non-observation;
- provider catalog bounded summary;
- task summary bounded state;
- permission summary without permit/approval material;
- UNKNOWN/DISCONNECTED truthfulness;
- CLI deterministic JSON and no external calls;
- existing full Python Governance suite;
- Desktop Shell regression suite to prove no desktop authority drift.

## DELIVERABLES
- `hive_runtime/runtime_status.py`;
- `tools/runtime/status_snapshot.py`;
- `tests/runtime/test_runtime_status.py`;
- evidence bundle and canonical docs only after objective proof.

## REVIEW FORMAT
HEDS_DELTA exact-head. Treat secret disclosure, fake readiness, authority-bearing serialization, unbounded output or hidden provider/model execution as HIGH/CRITICAL.

## STOP CONDITION
Exact-head Governance and Desktop Shell regressions green; runtime status tests green; HEDS APPROVED with no unresolved HIGH/CRITICAL. No desktop process spawn/provider call/model execution/permission mutation may be promoted under WO-0017. Squash merge only after all gates pass; post-merge validation required before CP-0017 becomes canonical.

## PROMOTION RECORD
Technical head `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef` passed Governance #225 (`35015244682`) and Desktop Shell #61 (`35015244727`) on the exact SHA. Ubuntu Python was **273/273 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**, frontend **12/12 PASS**, npm audit reported **0 vulnerabilities**, Windows Rust was **11/11 PASS**, `cargo check --locked`, Tauri release build and `DESKTOP_LAUNCH_SMOKE` all passed. HEDS technical review `5215028501` returned **APPROVED FOR PROMOTION CANDIDATE** with unresolved HIGH/CRITICAL findings **0**.

Promotion head `e2ae69e1be2f152eb9ce37b9b05f674dd072f5b5` was verified as documentation/evidence/governance-only relative to the technical head. Governance #234 (`35016227601`) and Desktop Shell #70 (`35016227612`) both completed **SUCCESS** on that exact SHA. HEDS promotion review `5215216401` returned **APPROVED FOR FINAL APPROVAL MUTATION** with unresolved HIGH/CRITICAL findings **0**.

`HCODER-WO-0017-CR-001` MEDIUM is resolved in the reviewed technical head. This final approval mutation remains documentation/governance-only and does not expand authority. WO-0017 is approved for squash merge only after the resulting exact head passes fresh Governance + Desktop Shell and final HEDS with no unresolved HIGH/CRITICAL. It does **not** become complete/canonical until squash merge succeeds and post-merge validation succeeds on `main`.

## CANONICAL CLOSEOUT
**Result:** STOP CONDITION SATISFIED.  
**Checkpoint:** `HCODER-CP-0017` APPROVED / CANONICAL.  
**Decision:** `DEC-021` APPROVED / CANONICAL.  
**Product PR:** #42 squash-merged.  
**Final reviewed product head:** `51a61a8ebdf8b50efcada02ba73c9ef406f27605`.  
**Canonical product merge SHA:** `00bcb87251772cba0eb385d9628448374e9dd612`.  
**Final product HEDS:** `5215281964`, unresolved HIGH/CRITICAL 0.  
**Post-merge Governance:** `35018459649` (#236) SUCCESS.  
**Post-merge Desktop Shell:** `35018459732` (#72) SUCCESS, including Windows release build and `DESKTOP_LAUNCH_SMOKE=PASS`.

The original Work Order specification above is preserved as the immutable audit contract. This appendix records completion only; it does not alter its historical scope, requirements, constraints, acceptance criteria or authority boundary. The canonical closeout itself remains subject to its documentation-only PR exact-head gates/HEDS and final push validation.
