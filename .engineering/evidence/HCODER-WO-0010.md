# Evidence Bundle — HCODER-WO-0010

**Risk:** ELEVATED  
**Base:** `f6f85b4825b739cdc7aae1a4ec3f2eeafea67147`

## Intelligence invariants
- Planner/model output is proposal data only.
- Critical UNKNOWN assumptions block approval; HIGH_ASSURANCE critical assumptions require VERIFIED evidence references.
- Independent Architect, Security, QA and Reviewer council participation is mandatory.
- HIGH/CRITICAL council findings block MasterPlan creation.
- Every acceptance criterion must be mapped to at least one plan step.
- Change targets must exist in the Project Digital Twin and bounded Change Radius must not truncate.
- MasterPlan compiles only to CP-0009 model-prompt/governed-skill nodes.
- Untrusted evidence cannot satisfy acceptance or STOP conditions.
- STOP requires every required trusted evidence kind.
- Self-correction cannot broaden step scope and has global/per-step budgets.
- Orchestrator telemetry validates TaskSnapshot identity against MasterPlan steps.

## Deterministic evidence target
Planning confidence/council/DAG/coverage/change-radius tests; PlanGraph compilation; EvidenceGraph/STOP tests; correction scope/budget tests; telemetry mismatch tests; broad Linux regression and unchanged Windows HIGH_ASSURANCE gates.

## HEDS target
Search for planner/council authority leaks, false completion, scope expansion, graph truncation hidden as success, correction-budget bypass, historical canonical mutation and mismatch with CP-0009 contracts. UNKNOWN is not PASS.
