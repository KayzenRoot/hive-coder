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
`HCODER-WO-0006` corrects the production modern MCP contract to `server/discover` followed by `tools/list`, with protocol metadata on every request. Hive resolves concrete Cua click/type tool names only from the pinned driver's advertised capabilities and required input schema. The real Windows harness is explicit opt-in, exact-version preflighted, requires a named sandbox application and obtains trusted target identity through Win32. Hosted CI does not prove physical desktop mutation; physical E2E remains UNKNOWN until a safe runner proves it.

## DEC-010 — Advanced capability roadmap
**Status:** APPROVED DIRECTION  
Hive Coder will evolve toward model-aware capability negotiation, a Hive-owned versioned/provenance-aware Skills Engine, long-running autonomous agent workflows and secure remote control from another authorized computer. Remote control is a zero-trust application control plane, never a publicly exposed raw desktop/Cua port.

## DEC-011 — Evidence-driven model capabilities and governed skills
**Status:** APPROVED  
`HCODER-WO-0007` makes explicit verified evidence the only authority for model capability negotiation. Model names, marketing labels, declarations and model-generated prose cannot enable capabilities. Hive skills are versioned/provenance-aware artifacts with separate ingest, deterministic evaluation, activation and rollback states. MCP skill resources are untrusted content regardless of transport trust. Skill activation is subordinate to existing capability authorization and can never mint or broaden authority.

## DEC-012 — Provider/model runtime and ACP prompt boundary
**Status:** APPROVED  
`HCODER-WO-0008` normalizes provider catalogs behind Hive-owned adapters. Raw provider observations have no verification authority: only a trusted host verifier may promote them into CP-0007 VERIFIED evidence. Routing considers only models satisfying verified requirements. OpenCode Go is a first-class provider identity but its name grants zero capabilities. Credentials are explicitly scoped/redacted. Open Interpreter ACP `session/prompt` is admitted as model execution only and does not mint desktop permits or expand CP-0005/0006 authority.

## DEC-013 — Resumable agent task runtime
**Status:** APPROVED  
`HCODER-WO-0009` establishes a deterministic sequential task DAG/state machine with bounded per-node attempts and HMAC-authenticated atomic checkpoints bound to a plan fingerprint. Active execution/failure ceilings are checkpoint-authenticated; restart configuration must match them exactly. Increasing them requires explicit trusted-host `extend_budget()` while paused. Checkpoints persist workflow state only and contain no credentials, approvals, permits, capability grants, skill content, raw prompts or model output. Interrupted skills never auto-replay after crash.

## DEC-014 — Master Planner and evidence-gated orchestration core
**Status:** APPROVED  
`HCODER-WO-0010` establishes DeepPlan, host-bound independent Hive Council, Confidence Matrix, Project Digital Twin/Change Radius, sealed PlanGraph compilation, EvidenceGraph, STOP Intelligence, bounded self-correction and specialist-agent roles. Planner/Council/model output is proposal data only. VERIFIED assumptions require trusted-host verification. Approved MasterPlans are HMAC-SHA256 sealed and bound to the exact objective/Digital Twin. Evidence trust is host-verified and STOP requires trusted coverage plus successful runtime execution. Self-correction cannot broaden approved change targets.

## DEC-015 — Measured expert-agent mesh and context intelligence
**Status:** APPROVED  
`HCODER-WO-0011` establishes a measurable specialist layer above CP-0010. Versioned Expertise Capsules encode doctrine but grant no authority. Trusted-host sealed Agent Profiles bind exact role, capsule, context ceiling, independence lineage, required model capabilities and execution-stack digest. ContextLens separates trusted context from untrusted data. Code Truth facts require provenance and host verification; Architectural Genome binds exact facts and the Digital Twin. Experience Routing considers only trusted exact-profile benchmark evidence, rejects trusted sample-set replay, measures benchmark-family diversity and uses Wilson 95% lower bounds. Competence levels have irreducible floors; production AgentMesh and challenge paths require `DISTINGUISHED`. Model/provider names and agent self-description have zero promotion authority. No real provider-backed agent is claimed `DISTINGUISHED` until its exact stack earns it through trusted evaluations.

## DEC-016 — Repository intelligence and continuous elite recertification
**Status:** CANDIDATE  
`HCODER-WO-0012` proposes a repository-aware evaluation layer above CP-0011. **RepoDNA** creates bounded deterministic UTF-8 snapshots without importing or executing repository code, rejects unsafe/noncanonical roots/paths and uses bounded regular-file reads with no-follow semantics where supported; known secret-like filenames, symlinks and common binary artifacts are excluded by default. **TruthWeave** derives reproducible Code Truth facts bound to exact snapshot/file/rule identity. **GenomePulse** mines immutable evidence-bound repository-footprint invariants from verified facts plus explicit trusted Digital Twin node/path bindings rather than model inference. **ShadowBench** creates host-keyed hidden evaluation identities from verified facts; verification recomputes lineage, nonce, prompt/oracle digests and case identity. **Benchmark Novelty** requires trusted case verification before admission and rejects exact, semantic and source-lineage replay. **Counterfactual Forge** creates non-mutating what-if probes tied to expected invariant drift. **ChronoSeal** supplies trusted-host monotonic logical epochs so callers cannot fabricate certification freshness. HMAC-SHA256 **Certification Authority** issues evidence only for passing `DISTINGUISHED` reports bound to the exact sealed Agent Profile, exact Competence Standard, exact competence-report fingerprint, exact repository snapshot and ChronoSeal epoch, with benchmark families derived from measured report scores. Competence Half-Life and Recertification Clock may classify signed evidence `CURRENT`, `DUE` or `EXPIRED` but cannot promote rank. **Outcome Echo** is trusted-host sealed and advisory-only: negative outcomes may accelerate recertification, positive outcomes cannot mint benchmark evidence. Language/framework Expertise Capsule extensions remain descriptive and non-authoritative. ChronoSeal and novelty state are session-bounded in CP-0012; durable cross-restart attestation is deferred. Existing CP-0005/0007/0008/0009/0010/0011 authority boundaries remain unchanged. Promotion requires exact-head Governance and HEDS.
