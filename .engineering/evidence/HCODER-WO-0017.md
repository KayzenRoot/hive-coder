# Evidence Bundle — HCODER-WO-0017

**Work Order:** `HCODER-WO-0017`  
**Issue:** `#41`  
**PR:** `#42`  
**Canonical base:** `442733aeae6bd2f615dc0bc4c76dda024455c212` (`HCODER-CP-0016`)  
**Technical reviewed head:** `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef`  
**Promotion reviewed head:** `e2ae69e1be2f152eb9ce37b9b05f674dd072f5b5`  
**Status:** APPROVED FOR SQUASH MERGE — FINAL EXACT-HEAD GATES PENDING

## Objective evidence
WO-0017 establishes the first Hive-owned versioned runtime observability contract above the existing Python engines without creating a new authority path. `RuntimeStatusSnapshot v1` carries bounded presentation-only runtime, provider/catalog, task-progress and permission state with explicit canonical provenance and truthful `READY`, `UNKNOWN`, `DISCONNECTED` or `DEGRADED` semantics.

The status layer cannot mint permits, approve requests, start providers, execute models, mutate tasks, inspect provider credentials, spawn desktop runtime processes, execute shell commands, mutate files/Git or control desktop input.

## Canonical status contract
- schema: `hive-runtime-status-v1`;
- total serialized/input ceiling: **32,768 bytes**;
- maximum providers: **16**;
- maximum models per provider: **64**;
- maximum task nodes represented: **256**;
- bounded text and integer counters;
- booleans are rejected as integer counters;
- exact object shapes and duplicate JSON object keys fail closed;
- in-memory operational state requires the governed `StatusState` enum;
- subsystem provenance is canonical, not caller-defined free text.

Canonical provenance identities:
- runtime: `hive-runtime-status`;
- provider catalog: `hive-provider-catalog`;
- task runtime: `hive-agent-task-runtime`;
- permission/control plane: `hive-permission-control-plane`.

## Truthfulness boundary
Provider `READY` means only that the Hive-owned catalog has a concrete bounded model observation. It does **not** mean the provider is reachable, healthy or authenticated and does not create VERIFIED model-capability evidence. Existing `ModelCapabilityRegistry` negotiation remains denied without separately trusted verification evidence.

The Permission & Control Plane currently has no safe public presentation observer for active-session/pending-approval counts. WO-0017 therefore does not serialize private internals. Permission status remains `UNKNOWN`/`DISCONNECTED` with null counters until a separately governed safe observer exists.

## Decoder / fail-closed evidence
`RuntimeStatusSnapshot.from_json()` enforces UTF-8, input byte ceilings, duplicate-key rejection, exact root/nested keys, typed state parsing, canonical provenance, collection ceilings and semantic invariants. Unknown/malformed/fake-ready data is rejected.

`encode_status_fail_closed()` and `decode_status_fail_closed()` convert rejected data to one fixed generic `DEGRADED` snapshot. Exception strings and rejected input values are not reflected into fallback status.

The CLI `tools/runtime/status_snapshot.py` intentionally emits one deterministic DISCONNECTED snapshot until a future governed trusted live observer/IPC host is connected. It performs no provider/model/process/mutation operation.

## Correction evidence
### HCODER-WO-0017-CR-001 — MEDIUM — RESOLVED IN CANDIDATE
Semantic HEDS pre-review found that the mechanically green initial replay lacked a strict decoder, allowed Python booleans through integer checks, had incomplete provenance, allowed caller-defined provenance labels and relied on type hints for in-memory enum enforcement. The correction adds strict decoder/encoder semantics, canonical provenance, typed-state enforcement, boolean rejection, fixed DEGRADED fallback and adversarial tests without adding authority.

The initial replay gates on `3053d6ee83483a41a5809f9fa52be40f2e28a04b` are historical only and do not count as final approval evidence after CR-001.

## Exact-head technical evidence
Governance run `35015244682` (#225) on exact technical head `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef`: **SUCCESS**.
- Ubuntu source-pack: **273/273 PASS**.
- Windows Server 2025 HIGH_ASSURANCE: **56/56 PASS**.

Desktop Shell run `35015244727` (#61) on the same exact head: **SUCCESS**.

Security gate:
- `DESKTOP_SECURITY_GATE=PASS`;
- `TAURI_COMMANDS=choose_workspace,get_desktop_snapshot`;
- `FRONTEND_INVOKES=2`;
- `WINDOW_SCOPE=main`;
- `CAPABILITY_PERMISSIONS=0`;
- `WORKSPACE_SELECTION_ARGS=0`;
- `FILESYSTEM_MUTATION_PRIMITIVES=0`;
- `GENERIC_PROCESS_EXECUTION=0`;
- `APPLE_SPECIFIC_FONT_REFERENCES=0`;
- committed lockfiles verified.

Frontend/native regression:
- TypeScript typecheck PASS;
- Vitest **12/12 PASS**;
- Vite production build PASS;
- npm audit: **0 vulnerabilities**;
- RustSec scanned **432** locked crates, found no blocking vulnerability and reports **7 allowed warning-class advisories** as existing dependency debt;
- Windows Rust unit tests: **11/11 PASS**;
- `cargo check --locked`: PASS with warnings denied;
- Tauri Windows release build: PASS;
- `DESKTOP_LAUNCH_SMOKE=PASS`.

HEDS technical review `5215028501`, anchored to exact head `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef`: **APPROVED FOR PROMOTION CANDIDATE**. Unresolved HIGH/CRITICAL findings: **0**.

## Promotion-head evidence
Promotion head `e2ae69e1be2f152eb9ce37b9b05f674dd072f5b5` is documentation/evidence/governance-only relative to the HEDS-approved technical head. No runtime implementation, CLI, test, Tauri command, capability, dependency or authority-bearing path changed.

- Governance run `35016227601` (#234): **SUCCESS** on exact promotion SHA.
- Desktop Shell run `35016227612` (#70): **SUCCESS** on exact promotion SHA.
- HEDS promotion review `5215216401`: **APPROVED FOR FINAL APPROVAL MUTATION**; unresolved HIGH/CRITICAL **0**.

The promotion review reconfirmed that status remains non-authoritative, provider catalog observation remains distinct from VERIFIED model capability evidence, permission private internals remain unobserved, and desktop process/IPC lifecycle remains deferred.

## Explicit residual boundaries
- WO-0017 proves the status schema/adapter reductions and safe disconnected exporter, not live cross-runtime desktop IPC.
- No desktop runtime child process is launched in this Work Order.
- No provider network-health or credential validation is performed.
- No safe public Permission & Control Plane live counter observer exists yet; private state is intentionally not serialized.
- The status snapshot is non-authoritative and cannot be used as permission evidence.
- Desktop subprocess identity/authenticity, status transport framing and lifecycle are deferred to a separately governed increment.
- Existing seven RustSec warning-class advisories remain dependency debt.
- No installer/signing/updater or full native interaction/visual E2E is claimed.

## STOP status
Technical implementation and promotion documentation are HEDS-approved. This final approval mutation may mark DEC-021 / CP-0017 approved for squash merge, but its resulting exact head must still pass fresh Governance + Desktop Shell and final HEDS with no unresolved HIGH/CRITICAL. Only then may PR #42 be squash-merged. CP-0017 remains **NOT CANONICAL** until post-merge Governance + Desktop Shell validation succeeds on the exact resulting `main` SHA and canonical closeout is recorded.
