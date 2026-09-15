# Integration Contracts — Hive Coder

External foundations are dependencies, not the Hive-facing architecture.

## Shared runtime/process boundary
Hive owns child-process and wire-protocol lifecycle. Foundation processes launch without a shell, receive a least-privilege environment, have bounded request/shutdown behavior and fail closed on unknown/malformed state. Production constructors resolve expected versions from `foundations/foundations.lock.json` and perform exact-version preflight before protocol launch.

## Permission & Control Plane boundary
Every privileged adapter/executor call crosses the Hive-owned `PermissionControlPlane`. Policy is default-deny; explicit deny wins; capability/action/target scope is session-bound; mandatory-approval risk cannot be downgraded. Trusted approval creates request-bound authorization and a short-lived signed single-use execution permit. The executor consumes that permit against the exact request immediately before mutation and revalidates live target identity. Model/tool surfaces never receive the trusted approval operation.

Emergency stop, user takeover, cancellation, expiry and policy changes invalidate ephemeral authorization. Audit events redact sensitive fields and form a SHA-256 digest chain.

## Interpreter runtime boundary
Hive talks to `InterpreterAdapter`, never upstream internals directly. Approved pin: Open Interpreter `0.0.43`, tag `rust-v0.0.43`, commit `6e7c4bb78bb1c349b82f584f7e21a529ec39a74f`. Primary transport is ACP v1 / NDJSON JSON-RPC over stdio; exec JSONL is fallback. `session/prompt` is admitted only as model execution and creates no desktop authority.

## Computer-use boundary
Approved pin: Cua Driver `0.28.1`, tag `cua-driver-rs-v0.28.1`, commit `d8028a7943087ee258dc1b4d19dc12a7cd27669c`.

Modern MCP revision `2026-07-28` is per-request negotiated over stdio. `server/discover` proves protocol/capability envelope; canonical tool inventory comes from a separate `tools/list` request. Hive preserves each advertised `inputSchema`, capability tokens and annotations. Production does not infer executable tools from discovery names or model text.

`HCODER-WO-0005` approves only Hive semantic actions `pointer.click` and `keyboard.type_text`. `HCODER-WO-0006` resolves their concrete Cua tool names from the pinned driver's advertised capabilities and validates required input properties before wiring. Every `tools/call` carries modern MCP metadata plus a Hive request fingerprint and remains permit-gated.

The real Windows harness is opt-in (`HIVE_ENABLE_REAL_CUA=1`), requires an explicitly supplied pinned binary and sandbox application, and obtains foreground HWND/PID/process image through Win32 rather than model input. The application/window identity is revalidated before dispatch. No automatic binary installation occurs. Hosted CI contract success is not evidence of physical desktop mutation; physical E2E stays UNKNOWN until an explicitly provisioned safe runner proves it.

## Skills/resource boundary
MCP skills/resources are untrusted content by construction. Hive owns skill identity/version/provenance/digest, deterministic evaluation, activation and rollback. Promotion authority is host-injected, and skill activation cannot exceed the existing trusted capability authorization. A task runtime may request a skill only through a trusted host execution port; it never activates a skill or grants permissions itself.

## Provider boundary
`ProviderAdapter` separates Hive orchestration from model/provider APIs. OpenCode Go is an initial first-class provider identity but not a hard dependency and carries zero implied capability. Raw provider observations have no verification authority. Only a trusted host verifier may promote a capability to VERIFIED, and `ModelRouter` fails closed when no verified model satisfies required capabilities. Provider credentials live behind the explicit redacted credential boundary.

## Agent task runtime boundary
`AgentTaskRuntime` coordinates a deterministic sequential DAG of model-prompt and governed-skill nodes. Task plans are fingerprint-bound to atomic HMAC-authenticated checkpoints. The checkpoint integrity key belongs to the trusted host and is never stored in checkpoint payloads.

Checkpoint state is workflow state only. It must not contain or mint credentials, approvals, permits, capability grants, skill contents, raw prompts or model outputs. Persisted events use normalized codes and exclude exception messages. Model execution uses `ModelRouter`; skill execution uses a trusted `SkillExecutionPort`.

Per-node attempt ceilings and global execution/failure ceilings are bounded. Active global ceilings are part of the authenticated checkpoint. A restarted runtime must match them exactly. Increasing them requires an explicit trusted-host `extend_budget()` transition while paused; the transition is monotonic and recorded in task history. Prompt/skill ports never receive budget-extension authority.

Interrupted model computation may be reissued only inside its attempt budget. Interrupted skills are treated as potentially side-effecting and never auto-replay after crash; explicit trusted-host recovery disposition is required. Pause stops future scheduling. If requested while a call is already in flight, that call may settle while the task remains PAUSED unless a terminal failure occurs. Cancellation is the cooperative interruption signal provided to execution ports and remains terminal.

## Planner and Orchestrator intelligence boundary
`DeepPlanEngine` accepts powerful planner output only as proposal data. VERIFIED assumptions require an independent trusted-host verifier, and required Council reviewer identity is assigned by Hive rather than accepted from model output. The ELEVATED Council profile requires Architect, Security, QA and Reviewer assessments and blocks MEDIUM/HIGH/CRITICAL findings.

The approved `MasterPlan` is sealed with HMAC-SHA256 by a trusted-host `PlanApprovalAuthority`. Its fingerprint binds the objective, semantic step graph, constraints, assumptions/evidence references, Council findings, bounded Change Radius and the exact `ProjectDigitalTwin` fingerprint. `PlanGraphCompiler`, `AgentOrchestrator` and bounded self-correction reject forged/unsealed plans or a current Digital Twin that differs from the approved planning snapshot.

`EvidenceGraph` is plan-scoped. Evidence producers cannot mark their own records trusted; trust is decided by a host verifier. Evidence is bound to the exact MasterPlan fingerprint and separately linked to acceptance criteria, objective constraints and STOP conditions. `STOP Intelligence` cannot declare completion until trusted evidence covers those obligations, and the Orchestrator additionally requires all CP-0009 task nodes to have succeeded. Model prose, Council prose and planner assertions have no completion authority.

`SelfCorrectionLedger` is bounded globally/per-step and can only request changes inside the targets already approved for that step. In CP-0010 it is session-bounded; automatic cross-restart self-correction is disabled until a later trusted persistence contract exists.

## Expert Agent Mesh boundary
Expertise is descriptive competence, not execution authority. `ExpertiseCapsule` records role doctrine, anti-patterns, review lenses, descriptive tool kinds, required model capabilities and benchmark dimensions. A capsule cannot grant a capability, activate a skill, mint a permit or make evidence trusted.

`AgentProfile` binds one agent identity to one role/capsule/context budget/independence lineage and is HMAC-SHA256 sealed by a trusted-host `AgentProfileAuthority`. There is no self-declared competence level in the profile.

`ContextLens` labels selected content as either trusted context or untrusted data. Required authoritative tags must be satisfied by host-verified context. External/tool/web/repository content never becomes instruction authority merely because it contains imperative text, and insufficient trusted context/budget fails closed.

`CodeTruthMap` accepts fact claims but only host-verified provenance-backed facts enter its authoritative fingerprint. `ArchitecturalGenome` binds invariants to exact verified fact fingerprints plus the Project Digital Twin; drift is descriptive evidence that must be handled by higher-level planning/review before execution.

`ExperienceLedger` separates benchmark claim storage from trust. `ExperienceRouter` uses only host-verified results and confidence-adjusted role standards. The initial Distinguished standard requires per-dimension sample floors, multiple independent suites, Wilson lower confidence bounds and zero critical/policy/tamper incidents. Provider/model names are not routing evidence.

`AgentMesh` revalidates the CP-0010 MasterPlan seal and exact Digital Twin before assigning measured specialists. Oversight roles cannot reuse an implementation independence lineage in the same assignment flow. Assignment fingerprints bind the selected profile, capsule and competence report.

CounterPlan and Failure Oracle challengers are host-identified, independence-separated advisory/review surfaces. Their output can block according to policy but can never grant authority or weaken CP-0005/0007/0008/0009/0010 controls.

## Repository intelligence and elite-evaluation boundary
`RepoDNAIndexer` is a read-only discovery surface. It may hash/classify bounded UTF-8 repository files, but it must not import modules, invoke package managers, run hooks, execute manifests or follow repository symlinks. Root symlinks/noncanonical paths are rejected; file opens are root-contained, regular-file checked and bounded, with no-follow semantics where the platform exposes them. Known secret-like filenames and common binary artifacts are excluded by default; this is defense in depth rather than a universal secret scanner. Resource ceilings fail closed rather than silently truncating authoritative snapshots.

`TruthWeave` derives descriptive Code Truth facts from exact RepoDNA content and extraction-rule identity. Its verifier accepts only facts whose fingerprints exactly match the facts reproducible from the same snapshot. Repository text, comments and imperative strings remain data and cannot become Hive instruction authority.

`GenomePulse` combines verified Code Truth facts with explicit trusted canonical node/path bindings and the existing Project Digital Twin. It mines immutable evidence-bound repository-footprint invariants; it does not ask a model to invent authoritative architecture. Drift evidence cannot grant a permission or rewrite the Digital Twin by itself.

`ShadowBench` generates host-keyed hidden evaluation identities from verified repository facts. Generated cases are proposals until a trusted benchmark runner/grader creates CP-0011-compatible evidence. Oracle material is represented as host-bound digests, not model-visible answer text. Case verification recomputes lineage, hidden nonce, prompt digest, oracle digest and case identity. `BenchmarkNoveltyLedger` requires an injected trusted case verifier before admission and then rejects exact, semantic and source-lineage replay so cosmetic case IDs or epoch churn cannot fake evaluation diversity.

`CounterfactualForge` creates non-mutating structural probes that bind a hypothetical fact replacement to immutable GenomePulse fact/invariant relationships expected to drift. It never edits repository source.

`ChronoSealClock` is a trusted-host monotonic logical epoch. Certification/outcome code reads its epoch rather than accepting caller-provided current time. CP-0012 ChronoSeal state is session-bounded; durable cross-restart time attestation is intentionally deferred.

`CertificationAuthority` HMAC-seals production certification evidence issued for a passing `DISTINGUISHED` CompetenceReport. The evidence binds the exact sealed Agent Profile, exact Competence Standard, exact report fingerprint, exact repository snapshot, ChronoSeal epoch and benchmark families derived from the measured report. The authority object belongs only to the trusted host and is never a model/tool surface.

`RecertificationClock` is negative/expiry authority only. It verifies the Certification Authority seal and may classify existing certification as `CURRENT`, `DUE` or `EXPIRED` according to exact profile/standard/repository binding and Competence Half-Life. It cannot promote an agent. A changed execution-stack digest changes the sealed Agent Profile fingerprint and prevents silent reuse of older certification evidence.

`OutcomeEchoLedger` accepts only trusted-host sealed operational outcomes whose observation epoch also comes from ChronoSeal. Its signal is advisory-only. Regressions/rollbacks may force earlier recertification; positive outcomes cannot mint benchmark evidence, change a Competence Standard or promote rank.

`ExpertiseCapsuleExtension` is descriptive language/framework doctrine bound to a base capsule fingerprint and provenance digest. It contains no permission or rank and has no automatic activation path.

Benchmark Novelty state is also session-bounded in CP-0012. This is acceptable because WO-0012 does not contain a provider-backed trusted runner/grader that can convert generated cases into competence evidence. Durable novelty/ChronoSeal attestation is a prerequisite of the future Provider Certification Lab.

## Provider Certification Lab & Semantic Repository Twin boundary
`SemanticRepositoryTwin` is compiled only from bounded RepoDNA content using static extractors. SchemaSense, APIVein, Dataflow Echo and Dependency Cortex produce descriptive structure and bounded traversal; none of these surfaces may execute indexed repository code, grant permission, activate a skill, mint trusted evidence or rewrite the Project Digital Twin by themselves.

`StackGenome` is the canonical exact-stack descriptor for certification trials. Its fingerprint must match the sealed Agent Profile execution-stack digest. Provider/model names alone have no competence authority.

`SuiteLineageAuthority` HMAC-seals suite identity and independence root. CP-0011 benchmark-family diversity for lab evidence is derived from this trusted lineage rather than caller-controlled family labels.

Runner and grader are represented by host-sealed `LabActor` identities. A valid lab trial requires distinct roles, distinct independence lineages and distinct EndpointSeal digests. Runner/grader identity is not accepted from model output.

`StackSealAuthority` binds the sealed Agent Profile, StackGenome, provider/model identity, exact repository snapshot, Semantic Twin fingerprint, SuiteLineage, ShadowBench case, independent actors and evaluation protocol into one trial contract. Any mismatch fails closed.

`TrialForge` materializes bounded provider-visible work without exposing host oracle material. The trial lineage is atomically reserved through `DurableAttestationJournal.reserve_once()` before provider execution. This One-Shot Trial Law prevents failure-driven rerolls inside the journal authority domain.

A grader decision requires GradeProof before Hive may create a `TrialReceipt`. Provider responses are bounded in the certification path. Contamination Radar is negative-only and cannot increase score or rank.

`DurableAttestationJournal` HMAC/hash-chains records and validates them against a host-injected external monotonic sequence floor. `DurableChronoSealClock` persists logical epochs through that journal. A valid older journal below the trusted floor is rollback and fails closed. Cross-process/distributed reservation and a production secure MonotonicAnchor implementation are not approved by CP-0013.

`BenchmarkAttestationAuthority` may aggregate only compatible sealed TrialReceipts. The resulting **EvidenceDNA Envelope** HMAC-binds the complete CP-0011 BenchmarkResult to exact StackGenome, repository snapshot, Semantic Twin and SuiteLineage. `ProviderCertificationLab.evaluate_and_certify()` accepts verified EvidenceDNA envelopes, not portable naked benchmark results, and rejects evidence transplant across repository/twin/stack contexts.

Auditable certification reports bind the exact EvidenceDNA set plus CP-0012 certification evidence. Certification remains competence evidence only. It never creates a CP-0005 permission, execution permit, credential, remote-control authority or skill activation.

## Remote-control boundary
Remote Hive control will be a separate HIGH_ASSURANCE subsystem. It must use authenticated encrypted device/session semantics, least privilege, revocation, audit and emergency stop. A raw Cua/RDP/VNC endpoint must never be exposed directly to the public internet by Hive.

## Contract rules
Version capabilities; fail closed on unknown privileged capability/version/schema; normalize errors without hiding diagnostics; preserve cancellation/emergency stop; redact secrets; record runtime identity; integration upgrades require regression evidence; no automatic dependency installation without a later approved design.
