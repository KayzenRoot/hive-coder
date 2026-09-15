# HCODER-WO-0017 — Runtime Observability Contract & Safe Status Export

**Status:** APPROVED FOR EXECUTION  
**Risk:** ELEVATED  
**Task class:** T3  
**Context radius:** C4  
**Stacked base:** `HCODER-WO-0016` promotion head `50c280004b0d869e32fda8f20806082654e63255`  
**Canonical dependency:** CP-0016 must become canonical before this Work Order may be promoted.

## OBJECTIVE
Create a Hive-owned, bounded, read-only runtime observability contract that truthfully exports runtime/provider/task/permission presentation state from the already-existing Python engines without exposing credentials, prompts, model output, permits, approval tokens or mutation authority. This establishes the trusted data source required before the desktop may claim live runtime/provider/permission readiness.

## CONTEXT
CP-0015 is canonical. WO-0016 has an exact-head promotion candidate that adds trusted workspace/Git/evidence reads. The canonical backlog says the next NECESSARY product work is truthful live runtime/provider/permission read state and explicitly forbids rebuilding the existing Python runtime/provider/task/control-plane engines.

Existing reusable surfaces include `ProviderCatalog`, `ModelCapabilityRegistry`, `AgentTaskRuntime`, the Permission & Control Plane, `ManagedStdioProcess`, JSON-RPC and Hive-owned provider/interpreter adapters.

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
- existing full Python Governance suite.

## DELIVERABLES
- `hive_runtime/runtime_status.py`;
- `tools/runtime/status_snapshot.py` or equivalent bounded CLI;
- `tests/runtime/test_runtime_status.py`;
- evidence bundle and canonical docs only after objective proof.

## REVIEW FORMAT
HEDS_DELTA exact-head. Treat secret disclosure, fake readiness, authority-bearing serialization, unbounded output or hidden provider/model execution as HIGH/CRITICAL.

## STOP CONDITION
Exact-head Governance green; runtime status tests green; HEDS APPROVED with no unresolved HIGH/CRITICAL. Promotion is BLOCKED until CP-0016 is canonical. No desktop process spawn/provider call/model execution/permission mutation may be promoted under WO-0017.