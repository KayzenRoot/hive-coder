# Decisions Ledger — Hive Coder

## DEC-001 — Separate repository/product
**Status:** APPROVED  
Hive Coder is developed in `KayzenRoot/hive-coder`, separate from `hive-code`.

## DEC-002 — Foundation direction
**Status:** APPROVED FOR ARCHITECTURE/ASSESSMENT  
Use Open Interpreter and Cua as preferred foundations behind Hive-owned adapters.

## DEC-003 — Visual direction
**Status:** APPROVED DIRECTION  
Premium desktop UX inspired by modern macOS qualities while using original Hive branding/assets.

## DEC-004 — Engineering workflow
**Status:** APPROVED  
Prompt mode `GEF_V1`; review mode `HEDS_DELTA`; exact-head evidence; same-WO Correction Delta.

## DEC-005 — First validated external foundations
**Status:** APPROVED  
Open Interpreter `0.0.43` and Cua Driver `0.28.1` are pinned behind Hive-owned boundaries. Automatic installation is disabled; optional OmniParser/Ultralytics remain excluded.

## DEC-006 — Hive-owned runtime bridge
**Status:** APPROVED  
`HCODER-WO-0003` establishes shell-free stdio/process and strict NDJSON JSON-RPC boundaries. Open Interpreter ACP v1 session lifecycle and Cua modern MCP `2026-07-28` discovery are proven under deterministic contracts.

## DEC-007 — Hive Permission & Control Plane authorization core
**Status:** APPROVED  
`HCODER-WO-0004` establishes default-deny capability/action/target policy, mandatory approval floors, signed request-bound single-use permits, emergency epochs, cancellation/takeover and redacted hash-chained audit.

## DEC-008 — First gated Cua mutation boundary
**Status:** APPROVED  
`HCODER-WO-0005` makes `GatedCuaActionExecutor` the only approved Hive Cua `tools/call` surface. Initial allowlist is only `pointer.click` and `keyboard.type_text`, both mandatory approval, with live target revalidation and emergency/takeover interruption.

## DEC-009 — Real Cua Windows harness contract
**Status:** APPROVED  
`HCODER-WO-0006` corrects the production modern MCP contract to `server/discover` followed by `tools/list`, with protocol metadata on every request. Hive resolves concrete Cua click/type tool names only from the pinned driver's advertised capability tokens and required input schema, never from model/task text. The real Windows harness is explicit opt-in, exact-version preflighted, requires a named sandbox application, obtains HWND/PID/process identity through typed Win32 APIs and wires the trusted discovered bindings into the existing permit-gated executor. No capability is added beyond CP-0005. Hosted CI proves contract and Windows logic but does not prove a physical Cua click/type; physical E2E remains UNKNOWN until a safe runner with the pinned binary is explicitly provisioned.

## DEC-010 — Advanced capability roadmap
**Status:** APPROVED DIRECTION  
Hive Coder will evolve toward model-aware capability negotiation, a Hive-owned versioned/provenance-aware Skills Engine with governed skill learning, long-running autonomous agent workflows and secure remote control from another authorized computer. Remote control is a zero-trust application control plane with encrypted authenticated device sessions, revocation, approvals, audit and emergency stop, not a publicly exposed raw desktop/Cua port.

## DEC-011 — Evidence-driven model capabilities and governed skills
**Status:** APPROVED  
`HCODER-WO-0007` makes explicit verified evidence the only authority for model capability negotiation. Model names, marketing labels, declarations and model-generated prose cannot enable capabilities. Hive skills are versioned/provenance-aware artifacts with separate ingest, deterministic evaluation, activation and rollback states. MCP skill resources are untrusted content regardless of transport trust. Skill activation is subordinate to the existing permission grant and can never mint or broaden authority.

## DEC-012 — Provider/model runtime and ACP prompt boundary
**Status:** APPROVED  
`HCODER-WO-0008` normalizes provider catalogs behind Hive-owned adapters. Raw provider observations have no verification authority: only a trusted host verifier may promote them into CP-0007 VERIFIED evidence. Routing considers only models satisfying verified requirements. OpenCode Go is the first-class provider identity but its name grants zero capabilities. Credentials are explicitly scoped/redacted. Open Interpreter ACP `session/prompt` is admitted as model execution only and does not mint desktop permits or expand CP-0005/0006 authority.

## DEC-013 — Resumable agent task runtime
**Status:** APPROVED  
`HCODER-WO-0009` establishes a deterministic sequential task DAG/state machine with bounded per-node attempts and HMAC-authenticated atomic checkpoints bound to a plan fingerprint. Active execution/failure ceilings are themselves checkpoint-authenticated; restart configuration must match them exactly. Increasing them requires an explicit trusted-host `extend_budget()` transition while paused; the transition is monotonic and recorded in task history. CP-0008 model routing and trusted host prompt/skill ports remain the only execution paths. Checkpoint state is non-authoritative and persists no credentials, approvals, permits, capability grants, skill content, raw prompts or model output. Interrupted skills never auto-replay after crash. Pause stops future scheduling while allowing an already in-flight call to settle without silently unpausing the task.

## DEC-014 — Master Planner and evidence-gated orchestration core
**Status:** APPROVED  
`HCODER-WO-0010` establishes the first Hive intelligence shell above CP-0009: DeepPlan, host-bound independent Hive Council, Confidence Matrix, Project Digital Twin/Change Radius, sealed PlanGraph compilation, EvidenceGraph, STOP Intelligence, bounded self-correction and specialist-agent roles. Planner/Council/model output is proposal data only. VERIFIED assumptions require trusted-host verification, Council role identity is host-assigned, and MEDIUM/HIGH/CRITICAL findings block the ELEVATED profile. Approved MasterPlans are HMAC-SHA256 sealed and bound to the objective plus the exact Project Digital Twin fingerprint. Every acceptance criterion and objective constraint must be represented in the plan. Evidence trust is host-verified and evidence is bound to the current MasterPlan fingerprint. STOP requires both 100% runtime step success and trusted evidence for every acceptance criterion, objective constraint and required STOP evidence kind. Self-correction cannot broaden approved change targets and remains session-bounded until a later trusted persistence contract.

## DEC-015 — Measured expert-agent mesh and context intelligence
**Status:** APPROVED  
`HCODER-WO-0011` establishes a measurable specialist layer above CP-0010. Versioned Expertise Capsules encode role doctrine, anti-patterns, review lenses, model/tool requirements and evaluation dimensions but grant no authority. Trusted-host sealed Agent Profiles bind the exact role, capsule fingerprint, context ceiling, independence lineage, required model capabilities and execution-stack digest, so competence evidence cannot silently migrate to a materially changed model/tool configuration. ContextLens separates trusted context from untrusted data and fails closed when authoritative required context cannot fit its deterministic budget. Code Truth Map facts require provenance and host verification; Architectural Genome invariants bind to exact verified facts and the Project Digital Twin and expose drift. Experience Routing considers only trusted benchmark evidence bound to the exact profile, rejects trusted sample-set replay, measures independent benchmark-family diversity and uses Wilson 95% lower confidence bounds. Competence levels have irreducible floors; the production AgentMesh and CounterPlan/Failure Oracle challenge paths require `DISTINGUISHED` standards and cannot be downgraded by caller configuration. Oversight and challenge identities are host-bound, measured and lineage-separated. Model/provider names and agent self-description have zero scoring or promotion authority. This decision proves the certification/routing machinery only; no real provider-backed agent is claimed `DISTINGUISHED` until its exact stack earns that status through trusted evaluations.

## DEC-016 — Repository intelligence and continuous elite recertification
**Status:** APPROVED  
`HCODER-WO-0012` establishes a repository-aware evaluation layer above CP-0011. **RepoDNA** creates bounded deterministic UTF-8 snapshots without importing or executing repository code, rejects unsafe/noncanonical roots/paths and uses bounded regular-file reads with no-follow semantics where supported; known secret-like filenames, symlinks and common binary artifacts are excluded by default. **TruthWeave** derives reproducible Code Truth facts bound to exact snapshot/file/rule identity. **GenomePulse** mines immutable evidence-bound repository-footprint invariants from verified facts plus explicit trusted Digital Twin node/path bindings rather than model inference. **ShadowBench** creates host-keyed hidden evaluation identities from verified facts; verification recomputes lineage, nonce, prompt/oracle digests and case identity. **Benchmark Novelty** requires trusted case verification before admission and rejects exact, semantic and source-lineage replay. **Counterfactual Forge** creates non-mutating what-if probes tied to expected invariant drift. **ChronoSeal** supplies trusted-host monotonic logical epochs so callers cannot fabricate certification freshness. HMAC-SHA256 **Certification Authority** issues evidence only for passing `DISTINGUISHED` reports bound to the exact sealed Agent Profile, exact Competence Standard, exact competence-report fingerprint, exact repository snapshot and ChronoSeal epoch, with benchmark families derived from the measured report scores. Competence Half-Life and Recertification Clock may classify signed evidence `CURRENT`, `DUE` or `EXPIRED` but cannot promote rank. **Outcome Echo** is trusted-host sealed and advisory-only: negative outcomes may accelerate recertification, positive outcomes cannot mint benchmark evidence. Language/framework Expertise Capsule extensions remain descriptive and non-authoritative. ChronoSeal and novelty state are session-bounded in CP-0012; durable cross-restart attestation is deferred. Existing CP-0005/0007/0008/0009/0010/0011 authority boundaries remain unchanged. Promotion evidence: exact head `fb90d330fab05df0d5b6cb8ef1dabee09c168f7f`, Governance run `34927005524`, Ubuntu **224/224 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**, HEDS APPROVED, CR-001 resolved with no remaining HIGH/CRITICAL finding in scope.

## DEC-017 — Provider Certification Lab and Semantic Repository Twin
**Status:** APPROVED  
`HCODER-WO-0013` establishes the first HIGH_ASSURANCE exact-stack certification laboratory above CP-0012 plus a static **Semantic Repository Twin**. **SchemaSense**, **APIVein**, **Dataflow Echo**, **Dependency Cortex** and deterministic twin drift compile conservative semantic structure from RepoDNA without executing repository code; semantic observations remain descriptive evidence only. **StackGenome** canonically describes provider/model revision/toolset/capsule/skillset/runtime and must fingerprint-match the sealed Agent Profile execution stack. HMAC-sealed **SuiteLineage Authority** derives benchmark-family diversity from independence roots so cosmetic suite/family names cannot manufacture diversity. Runner/grader `LabActor` identities bind role, independence lineage and **EndpointSeal** digest; lineage or endpoint collapse is rejected. **StackSeal** binds the complete trial context: profile, StackGenome, provider/model, repository snapshot, Semantic Twin, SuiteLineage, ShadowBench case, independent actors and protocol. **TrialForge** exposes no oracle material to the provider runner. **One-Shot Trial Law** atomically reserves a hidden case lineage before provider execution so failures cannot be rerolled. **GradeProof** requires a rationale/evidence digest before a TrialReceipt can exist. **Contamination Radar** is block/down-rank only. `DurableAttestationJournal` HMAC/hash-chains chronology and uses a host-injected external monotonic sequence floor to detect rollback of an otherwise correctly signed older journal; `DurableChronoSealClock` persists logical epochs through it. **EvidenceDNA** HMAC-binds laboratory benchmark evidence to the complete CP-0011 BenchmarkResult plus exact StackGenome, repository snapshot, Semantic Twin and SuiteLineage; certification rejects transplanted evidence from another repository/twin/stack. Auditable certification reports bind exact EvidenceDNA envelopes and CP-0012 certification evidence. `HCODER-WO-0013-CR-001` and `HCODER-WO-0013-CR-002` are resolved. Hosted CI uses mock provider/grader ports and no real provider credentials, so no real stack is claimed `DISTINGUISHED`. Cross-process/distributed trial reservation and a production MonotonicAnchor implementation remain outside CP-0013. Promotion evidence: exact head `91fec0821f8cececed2cfeb44a18ce508aa03e42`, Governance run `34953929007`, Ubuntu **241/241 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**, HEDS APPROVED, open HIGH/CRITICAL findings **0**.

## DEC-018 — Elite Specialist Forge & Autonomous Engineering Arena
**Status:** APPROVED  
`HCODER-WO-0014` establishes a governed specialist-forging and arena-selection layer above CP-0013. Trusted-host `SpecializationPack` provenance and exact `SkillGenome` composition feed **ForgeSeal**, which binds the sealed AgentProfile, exact StackGenome, repository snapshot, Semantic Repository Twin, specialization pack, SkillGenome and trusted certification evidence. **ChallengeMorph** derives bounded challenge variants from trusted ShadowBench cases and sealed SuiteLineage, while **Anti-Overfit Horizon** rejects replay and source-lineage inflation; the sealed base-lineage root is enforced again at Mastery Lattice admission. Sealed **ArenaEvidence** binds GradeProof and host-verified telemetry to the exact blueprint/challenge/repository/twin context. **Mastery Lattice** admits only unique blueprint/challenge evidence and applies irreducible quality, reliability and diversity floors. **Reliability Shadow** is negative-only regression memory. **Pareto Crown** revalidates the sealed AgentProfile and exact certification context at routing time, filters security/quality/reliability floors before optimization, and uses cost/latency only among already-qualified candidates. Competence remains separate from execution authority and CP-0005 through CP-0013 authority boundaries remain unchanged. `HCODER-WO-0014-CR-001` through `CR-004` are resolved. Hosted CI uses deterministic/mock evaluation surfaces and does not prove any real provider/model stack is elite or `DISTINGUISHED`; production telemetry attestation and durable cross-restart mastery/reputation remain future governed work. Promotion candidate `ef34acc493a10f16ba79459c5d7d9d4b39005e4a` passed Governance run `34973660965` on exact head; HEDS promotion review `5210423743` found the delta from technical head `54d19f3acbac6e20f34287d5fe12cc2316d89e23` documentation/governance-only with no unresolved HIGH/CRITICAL finding.

## DEC-019 — Desktop Shell Foundation & Read-Only Application Boundary
**Status:** APPROVED  
**Work Order:** `HCODER-WO-0015`

The first Hive Coder desktop foundation is Tauri 2 with React/TypeScript/Vite behind a Hive-owned application boundary. `DesktopSnapshot v1` is bounded presentation state only. The first shell exposes exactly one application command, `get_desktop_snapshot`, which accepts no execution payload, revalidates the invoking WebView window as `main`, and grants no execution authority.

The Tauri capability is restricted to the `main` window and grants zero plugin permissions. Shell, filesystem and process plugins are not part of WO-0015. Future privileged desktop/runtime operations remain behind `Hive Application/Orchestrator -> Permission & Control Plane -> Capability Adapters`; the desktop UI cannot mint CP permits, activate skills, obtain provider credentials, mutate arbitrary files, inject desktop input, expose remote control or authorize billing/purchases.

The dependency graph is committed through npm/Cargo lockfiles and validated by dedicated Desktop Shell CI. Windows release build + launch smoke prove the native shell starts, not that installer/signing/full interaction E2E or visual pixel fidelity is complete. RustSec warning-class transitive advisories remain explicit dependency debt and the project license remains undecided.

Promotion candidate `e3b24420f7057272fbe15a4ddae88ce65a190e50` passed Governance run `34985024390` (#189): Ubuntu **256/256 PASS**, Windows Server 2025 HIGH_ASSURANCE **56/56 PASS**; Desktop Shell run `34985024599` (#25): security gate PASS, Vitest **8/8 PASS**, npm audit **0 vulnerabilities**, Rust **3/3 PASS**, `cargo check --locked` PASS, Tauri release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`. HEDS promotion review `5211785907` verified the promotion delta as documentation/governance-only and reported unresolved HIGH/CRITICAL findings **0**.

This APPROVED decision does not expand privilege. The approval mutation itself must pass exact-head Governance + Desktop Shell and final HEDS before merge.

## DEC-020 — Trusted Workspace & Git Read Boundary
**Status:** APPROVED  
**Work Order:** `HCODER-WO-0016`

Hive Coder admits its first user-mediated live workspace boundary as bounded read-only presentation state. Native `choose_workspace` accepts no caller-controlled target/path payload; the trusted Rust application layer canonicalizes/validates the selected directory and retains application-owned session identity. `DesktopSnapshot v2` reports bounded workspace, Git HEAD/branch and Hive checkpoint/evidence observations with explicit provenance and READY/UNKNOWN/DISCONNECTED/DEGRADED semantics.

Git observation reads bounded `.git` metadata directly and never executes an external `git` command or repository hooks. The Tauri capability remains `desktop-read-only`, scoped to `main`, with zero plugin permissions. No terminal/shell, filesystem mutation, provider credential/model execution, runtime spawn, computer-use mutation, remote control, automatic skill activation, billing/purchase authority or Permission & Control Plane expansion is approved by this decision.

`HCODER-WO-0016-CR-001` HIGH and `HCODER-WO-0016-CR-002` MEDIUM are resolved. Technical head `07dda00f7371bcb02158f0c26258b03fa0dec88d` passed Governance `34996930586`, Desktop Shell `34996930809` and HEDS technical review `5213079423`. Promotion head `50c280004b0d869e32fda8f20806082654e63255` passed Governance `34997849021`, Desktop Shell `34997849241` and HEDS promotion review `5213131975`, with unresolved HIGH/CRITICAL findings 0. This decision is approved for the merge candidate but becomes canonical only after the final approval head passes exact-head gates/HEDS, squash merge, and post-merge validation on `main`.

## DEC-021 — Runtime Observability Presentation Contract
**Status:** CANDIDATE — APPROVAL PENDING  
**Work Order:** `HCODER-WO-0017`

Hive Coder standardizes runtime/provider/task/permission **presentation truth** through the versioned `RuntimeStatusSnapshot v1` contract. The contract is explicitly non-authoritative: it cannot grant permission, mint or substitute for execution permits, activate skills, authorize provider/model execution, mutate task state or enable computer-use/file/Git actions.

The contract uses bounded `READY`, `UNKNOWN`, `DISCONNECTED` and `DEGRADED` state with canonical Hive provenance per subsystem. JSON is accepted only through a strict byte-bounded UTF-8 decoder with exact object shapes, duplicate-key rejection, bounded strings/collections/counters and semantic validation. Python boolean values are rejected as integer counters, in-memory state requires the governed `StatusState` enum, and caller-defined provenance cannot impersonate trusted Hive subsystem provenance. Invalid encode/decode input reduces only to a fixed non-secret DEGRADED presentation snapshot.

Provider `READY` is deliberately narrow: it proves only a concrete bounded local provider-catalog observation. It does not prove provider reachability, authentication or model capability, and cannot promote CP-0007 capability evidence to VERIFIED. Task presentation consumes only bounded public `TaskSnapshot` state and excludes prompts, outputs, plan fingerprints, attempts and event payloads. Permission presentation does not inspect private Permission & Control Plane internals; when no safe public observer exists, state remains UNKNOWN/DISCONNECTED without authoritative-looking counters.

The WO-0017 safe CLI is a disconnected diagnostic exporter, not a runtime host. Desktop subprocess launch, helper identity, transport framing, cross-runtime IPC and lifecycle supervision remain outside this decision and require a later governed increment after CP-0017 becomes canonical.

`HCODER-WO-0017-CR-001` MEDIUM is resolved. Technical head `63abc6349421ed4c83c52c5f03d305cbb0f1f3ef` passed Governance #225 (`35015244682`): Ubuntu **273/273 PASS**, Windows HIGH_ASSURANCE **56/56 PASS**; Desktop Shell #61 (`35015244727`): security gate PASS, frontend **12/12 PASS**, npm audit **0 vulnerabilities**, Rust **11/11 PASS**, RustSec scan completed with seven warning-class advisories and no blocking vulnerability, `cargo check --locked` PASS, Tauri release build PASS and `DESKTOP_LAUNCH_SMOKE=PASS`. HEDS technical review `5215028501` approved the implementation for promotion with unresolved HIGH/CRITICAL findings **0**.

This decision remains CANDIDATE until the documentation/evidence promotion head itself passes exact-head Governance + Desktop Shell and promotion HEDS. A later approval mutation may mark it APPROVED FOR SQUASH MERGE, but canonical authority begins only after merge and post-merge validation on `main`.