# Correction Delta — HCODER-WO-0011-CR-001

## Findings
1. **HIGH · competence portability:** early specialist evidence was not sufficiently explicit about the exact execution stack, risking reputation surviving a material model/tool configuration change.
2. **HIGH · benchmark replay/double count:** trusted sample sets needed an explicit replay guard so the same evaluated tasks could not inflate competence under multiple result records.
3. **HIGH · configurable rank downgrade:** a caller could attempt to label a weak threshold set as `DISTINGUISHED`, or feed a lower competence level into production AgentMesh/challenge paths.
4. **HIGH · reviewer/challenger independence:** separation needed to be checked across the complete assignment set, independent of plan ordering; adversarial challengers also needed measured competence and host-registered identity.
5. **MEDIUM · suite diversity gaming:** multiple versions of one benchmark family could otherwise appear as independent evaluation diversity.
6. **MEDIUM · challenge plan trust:** CounterPlan/Failure Oracle must reject forged plans and stale Digital Twin state rather than analyze unauthenticated plan objects.
7. **MEDIUM · module auditability:** the first implementation concentrated identity, context, evaluation and mesh concerns in one large module, increasing review/change risk.
8. **LOW · hardening fixtures:** tests written before the irreducible rank floor still constructed intentionally weak `DISTINGUISHED` standards and failed once the security invariant became stricter.

## Corrections
- `AgentProfile` now binds an `execution_stack_digest`; benchmark records bind the exact sealed profile fingerprint.
- `ExperienceLedger` rejects replay of a trusted sample-set digest for the same profile/dimension.
- Competence levels have irreducible sample/confidence/diversity floors; `DISTINGUISHED` cannot be weakened by caller configuration.
- Production `AgentMesh` and `AdversarialChallengeEngine` reject any competence standard below `DISTINGUISHED`.
- Oversight lineage separation is evaluated across all routed steps, independent of step ordering.
- Challenge identities must be host-sealed, registered, role-eligible, independently measured and lineage-separated.
- Suite diversity is counted by benchmark family, not merely suite/version strings.
- CounterPlan/Failure Oracle require a valid CP-0010 MasterPlan seal and the current Digital Twin fingerprint.
- The implementation was split into identity, context/truth, evaluation, doctrine and mesh modules behind a compatibility facade.
- Test fixtures were upgraded to the real irreducible `DISTINGUISHED` floor instead of weakening production rules for test convenience.

## Evidence
Exact correction head `5c1020ca56fd8efec6ac7b302b446c99ffab8453`, Governance run `34924937295`:
- Ubuntu 24.04 broad regression: **195/195 PASS** with exact-head verification and `ResourceWarning` fatal.
- Windows Server 2025 HIGH_ASSURANCE regression: **56/56 PASS** with exact-head verification.

## Residual boundary
This work proves the certification/routing machinery, not that a real provider-backed agent has already earned `DISTINGUISHED`. Real certification requires trusted benchmark executions against the exact future provider/model/tool stack. Benchmark decay, hidden-corpus generation and provider-backed certification remain later governed increments.
