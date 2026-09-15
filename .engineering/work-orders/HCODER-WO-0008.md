# HCODER-WO-0008 — Provider & Model Runtime Integration

**Classification:** NECESSARY · T3 · C3 · ELEVATED  
**Base checkpoint:** HCODER-CP-0007  
**Base SHA:** `5af12a77106467bd6838eb545ef2b94ac4265fc5`

## OBJECTIVE
Create the Hive-owned provider/model runtime boundary and first capability-aware routing path, with OpenCode Go as the first-class provider identity.

## CONTEXT
CP-0007 proves verified-only model capabilities and governed skills. The runtime now needs deterministic provider catalogs, probes, routing and ACP prompt lifecycle without weakening desktop authorization.

## SCOPE
Provider contracts; catalog normalization; capability probes into CP-0007; deterministic model router; explicit credential scope/redaction; OpenCode Go provider identity; ACP session/prompt lifecycle; cancellation/error normalization; tests/docs/evidence.

## OUT OF SCOPE
Real credentials in repo/CI, billing, purchases, remote control, automatic skills, new Cua capabilities.

## FILES/SOURCES TO READ
CP-0007, Decisions, Scope, Architecture, Security, Test Plan, Integration Contracts, Interpreter ACP bridge and capability registry.

## REQUIREMENTS
Unknown capability fails closed. Provider/model names cannot grant capability. Credentials are explicit and redacted. Prompt execution cannot grant desktop authority.

## ARCHITECTURE RULES
Hive-owned adapters and routing. Provider metadata is normalized before use. CP-0005/0006 remain authoritative for desktop mutation.

## CONSTRAINTS
No real provider secret committed or printed. No automatic install. No new desktop mutation.

## ACCEPTANCE CRITERIA
Deterministic fake-provider catalog/probe/router tests and fake-ACP prompt lifecycle pass; broad regression green.

## TESTS
Unit tests + exact-head Governance, ResourceWarning fatal.

## DELIVERABLES
Provider runtime module, Interpreter prompt extension, tests, docs, decision/checkpoint/evidence.

## REVIEW FORMAT
HEDS Delta exact-head. UNKNOWN is never PASS.

## STOP CONDITION
Governance green, HEDS APPROVED, no unresolved HIGH/CRITICAL, CP-0008 promoted, squash merge.
