# Hive Intelligence Core

HCODER-WO-0010 establishes the first proprietary intelligence layer above CP-0009 execution. The principle is simple: use as much model intelligence as useful while making truth, scope, approval and completion difficult for any model to fake.

## Implemented in this increment

### Hive DeepPlan Engine
Receives an objective plus planner proposal and applies deterministic acceptance/constraint coverage, dependency, confidence, Council and Change Radius gates before a MasterPlan can exist.

### Hive Council
Architect, Security, QA and Reviewer identities are assigned by the trusted host, not by model output. The ELEVATED profile requires every role to produce an assessment and blocks MEDIUM/HIGH/CRITICAL findings. Council prose cannot mint authority.

### Confidence Matrix
Assumptions are VERIFIED, INFERRED or UNKNOWN. VERIFIED is accepted only after a trusted-host verifier validates its evidence references. Critical UNKNOWN blocks planning; HIGH_ASSURANCE critical assumptions must be VERIFIED.

### Project Digital Twin foundation
A Hive-owned structural dependency snapshot represents project components and relationships. It is descriptive context, never permission. The Twin has a deterministic SHA-256 fingerprint. Change Radius walks reverse dependencies with explicit depth/node ceilings and reports truncation; DeepPlan fails closed if the approved planning radius is incomplete.

### Sealed MasterPlan + PlanGraph
DeepPlan-approved MasterPlans are HMAC-SHA256 sealed by a trusted-host `PlanApprovalAuthority` using a key of at least 256 bits. The seal covers objective identity, semantic plan structure, assumptions, Council findings, Change Radius and exact Digital Twin fingerprint. A forged plan or plan created for an older/different Twin cannot compile.

Approved planning steps compile only into CP-0009 model-prompt or governed-skill nodes. Planner output never introduces a third privileged execution path.

### EvidenceGraph
Evidence is linked to the exact MasterPlan fingerprint and separately mapped to acceptance criteria, objective constraints and STOP conditions. Evidence producers do not provide their own trust flag; a trusted-host verifier decides whether evidence is authoritative. Stale evidence from another plan is rejected.

### STOP Intelligence
Completion requires trusted evidence for every acceptance criterion, every objective constraint and every evidence kind required by each STOP condition. The Orchestrator additionally requires every CP-0009 task node to have succeeded. A model saying `done` has zero completion authority.

### Bounded Self-Correction
Corrections are counted globally and per step and may touch only the already-approved change targets for that step. They cannot silently increase scope. CP-0010 keeps the correction ledger session-bounded; cross-restart automatic self-correction remains disabled until trusted persistence exists.

### Specialist agent roles
Planner, Architect, Backend, Frontend, Data, Security, QA, Performance, DevOps, Reviewer and Documentation are explicit roles. Future Expertise Capsules will attach tools, ContextLens slices, evaluation suites and measured competence to these roles rather than treating them as prompt labels.

## Technology roadmap built on this foundation
- **Architectural Genome:** compact architectural invariants and boundary signatures.
- **Code Truth Map:** provenance-backed map of repository/runtime facts feeding future Digital Twin refresh.
- **Failure Oracle:** bounded pre-mortem and failure-scenario generation followed by deterministic checks.
- **CounterPlan:** alternative-plan generation and adversarial challenge before expensive execution.
- **AgentMesh:** specialist scheduling, dependency/conflict control and non-duplicative work allocation.
- **ContextLens:** minimum-sufficient, evidence-ranked context selection per specialist/task.
- **Expertise Capsules:** versioned specialist knowledge, tools, constraints and evaluation packs.
- **Experience Routing:** measured task/model/skill/agent effectiveness routing rather than self-reported competence.
- **SkillForge + Skill Evolution:** successful repeated workflows become governed skill candidates, never automatic production authority.
- **Autonomy Governor:** risk-adaptive intelligence depth and action freedom under existing permission controls.

These roadmap names are product architecture directions, not claims of completed functionality. Each becomes canonical only through its own governed Work Order and evidence.
