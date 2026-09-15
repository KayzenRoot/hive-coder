# Hive Intelligence Core

HCODER-WO-0010 starts the proprietary intelligence layer that sits above CP-0009 execution. The goal is not to trust an LLM more. The goal is to use more intelligence while making truth, scope and completion harder to fake.

## Implemented in this increment

### Hive DeepPlan Engine
Receives an objective and a planner proposal, then applies deterministic coverage, dependency, confidence, council and change-radius gates before a MasterPlan exists.

### Hive Council
Independent architect, security, QA and reviewer perspectives are mandatory in the first council profile. HIGH or CRITICAL findings block promotion. Council text cannot mint authority.

### Confidence Matrix
Assumptions are VERIFIED, INFERRED or UNKNOWN. VERIFIED requires evidence references. Critical UNKNOWN blocks all plans; HIGH_ASSURANCE critical assumptions must be VERIFIED.

### Project Digital Twin foundation
A Hive-owned descriptive dependency graph represents system components and relationships. It is context, never permission. The Change Radius Engine walks reverse dependencies with explicit depth/node bounds and fails closed if the approved planning radius would truncate.

### PlanGraph
Approved planning steps are dependency-validated and compile only into the two CP-0009 node kinds: model prompt or governed skill.

### EvidenceGraph
Trusted evidence is linked to acceptance criteria and STOP conditions by identity and SHA-256 digest. Untrusted agent/model claims remain visible data but cannot satisfy completion.

### STOP Intelligence
A task is complete only when every acceptance criterion has trusted evidence and every STOP condition has all required evidence kinds. A model saying “done” has zero completion authority.

### Bounded Self-Correction
Corrections are counted globally and per step and may touch only the step's already-approved change targets. A correction cannot silently increase scope.

## Specialist agent roles
Planner, Architect, Backend, Frontend, Data, Security, QA, Performance, DevOps, Reviewer and Documentation are explicit roles. Future Expert Capsules will attach tools, context slices, evaluation suites and measured competence to these roles.

## Technology roadmap built on this foundation
- Architectural Genome: compact architectural invariants and boundary signatures.
- Code Truth Map: evidence-backed map of repository/runtime facts.
- Failure Oracle: bounded pre-mortem and failure-scenario generation followed by deterministic checks.
- CounterPlan: alternative plan generation and adversarial challenge.
- AgentMesh: specialist scheduling and conflict/duplication control.
- ContextLens: minimum sufficient context selection per specialist.
- Expertise Capsules: versioned specialist knowledge/evaluation packs.
- Experience Routing: measured task/model/skill effectiveness routing.
- SkillForge and Skill Evolution: successful repeated workflows become governed skill candidates, never automatic production authority.
- Autonomy Governor: risk-adaptive intelligence depth and action freedom.

These roadmap names are product architecture directions, not claims of completed functionality. Each becomes canonical only through its own governed Work Order and evidence.
