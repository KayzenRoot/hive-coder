# GEF V1 Universal Policy — Hive Coder

## Adoption mode
Hive Coder is a BROWNFIELD project. GEF V1.0.0 wraps the existing project additively; it does not rewrite historical work into fake GEF history.

## Authority
Canonical project truth wins over GEF support files. Use this order unless a later approved decision changes it:
1. current accepted checkpoint / production state;
2. approved Decisions / ADRs;
3. approved scope and requirements;
4. Definition of Done / acceptance criteria;
5. architecture contracts;
6. security/policy constraints;
7. active Work Order / Context Lock;
8. supporting documentation;
9. informal notes.

Material contradictions are recorded, never silently resolved.

## Universal lifecycle
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> EXACT-HEAD AUDIT -> CHECKPOINT DELTA -> MERGE -> NEXT`.

For substantial work, do not jump directly from idea to mutation. Every implementation increment needs a stable Work Order or equivalent governed execution contract.

## Brownfield preservation law
- Preserve user code, history, architecture, tests, CI, release semantics and naming unless a governed migration explicitly changes them.
- Prefer mappings and compatibility layers over destructive normalization.
- Do not mass-format unrelated code or rename modules for GEF aesthetics.
- Do not fabricate historical Work Orders, checkpoints, decisions, tests, releases or evidence.
- Historical evidence may be mapped only when repository facts support it.

## Evidence law
- `UNKNOWN` is never PASS/ALLOW/zero.
- Missing evidence is not completion.
- Exact-head means the reviewed/tested SHA equals the candidate SHA.
- Hash integrity is not signing.
- No production progress is awarded without evidence-bound acceptance.
- No HIGH/CRITICAL unresolved finding may be silently accepted for promotion.

## Git/GitHub law
Substantial work uses branches/PRs and exact-head gates according to repository policy. No force-push or destructive history rewrite without explicit governed authorization. Single-owner operation does not require ceremonial human approval, but technical exact-head audit remains mandatory.

## Security baseline
Tailor controls to the actual surface: secrets, traversal/symlink escape, untrusted config, dependencies, permission/authority boundaries, shell/process execution, generated artifact integrity, partial-mutation recovery, logging/redaction and GitHub permission scope.

## Review -> next prompt PDF law
Every completed review must already produce the next executable Codex prompt as a generated PDF. `CORRECTION_REQUIRED` stays in the same Work Order. `BLOCKED` receives a bounded unblock prompt when an executable next action exists. No new increment begins before the predecessor is objectively accepted.

## Forbidden shortcuts
No fabricated evidence; no stale-head proof as exact-head proof; no silent scope growth; no test/security/governance weakening to get green; no destructive normalization; no fake package/release/install claims; no secret disclosure; no optional adapter silently becoming a release blocker.
