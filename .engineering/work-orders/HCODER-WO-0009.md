# HCODER-WO-0009 — Resumable Agent Task Runtime

**Classification:** NECESSARY · T3 · C4 · ELEVATED  
**Base checkpoint:** HCODER-CP-0008  
**Base SHA:** `21b11482015ff2704a56af7ea71921e74e11c61a`

## OBJECTIVE
Create a Hive-owned resumable task runtime for long-running autonomous coding workflows without turning workflow state into authorization.

## CONTEXT
CP-0008 proves provider/model routing and ACP prompt execution. The next required layer is durable orchestration across prompts and governed skills with bounded budgets, restart recovery and observable state.

## SCOPE
Task DAG/state machine; authenticated atomic checkpoints; plan fingerprint binding; sequential resumable execution; model routing; trusted prompt/skill ports; retry/failure/execution budgets; cancellation; pause/continue; interrupted-action recovery; structured secret-safe event history; tests/docs/evidence.

## OUT OF SCOPE
Direct shell/browser/Cua authority, remote control server, automatic skill install/self-promotion, parallel/distributed scheduling, committed provider credentials.

## FILES/SOURCES TO READ
CP-0008; Decisions Ledger; Architecture; Security; Test Plan; Integration Contracts; `providers.py`; governed skills boundary; Permission Control Plane contracts.

## REQUIREMENTS
Checkpoint state cannot contain or mint credentials, approvals, permits, capability grants, skill content or model output. Required model capabilities flow through CP-0008 ModelRouter. Skill actions execute only through a trusted host port. Interrupted side-effect-capable skill calls never auto-replay after crash. All resource/retry budgets are bounded.

## ARCHITECTURE RULES
Deterministic scheduling; fail closed on malformed/tampered/mismatched checkpoints; external execution ports remain the authority boundary; workflow persistence is subordinate to CP-0005/0007/0008.

## CONSTRAINTS
No live credentials, network listener or new desktop mutation capability.

## ACCEPTANCE CRITERIA
Crash/restart, HMAC tamper, plan mismatch, budgets, retries, cancellation, dependency ordering, unverified model capability, malicious result/error data and interrupted-skill recovery tests pass with broad regression green.

## TESTS
Unit tests + exact-head Governance; Windows HIGH_ASSURANCE regression unchanged; ResourceWarning fatal.

## DELIVERABLES
`hive_runtime/agent_tasks.py`, deterministic tests, runtime docs, DEC-013, integration contract update, evidence bundle and CP-0009.

## REVIEW FORMAT
HEDS Delta exact-head. UNKNOWN is never PASS.

## STOP CONDITION
Governance green, HEDS APPROVED, no unresolved HIGH/CRITICAL, CP-0009 promoted, squash merge to main.
