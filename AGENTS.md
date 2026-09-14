# Hive Coder agent guidance

## Source of truth
Canonical truth lives in `docs/project-brain/` with precedence: latest approved checkpoint > Decisions Ledger/ADRs > Scope > Definition of Done > Architecture > Requirements > remaining sources.

## Execution
- Inspect Git and canonical sources before any change.
- Work only under an approved Work Order ID.
- Bind execution to a Context Lock and exact base/head when available.
- Prefer deterministic tools before LLM reasoning.
- Executor claims are staged until tests/evidence prove them.
- Never expand scope silently or weaken security/governance.
- Never commit secrets, credentials, user-owned data, screenshots containing secrets, or unrestricted desktop-control traces.
- Final executor review/report is in Brazilian Portuguese.
- Do not advance when verdict is `CORRECTION REQUIRED` or `BLOCKED`.

## Flow
`ANALYZE -> SOURCE CHECK -> NEXT NECESSARY INCREMENT -> WORK ORDER -> CONTEXT LOCK -> PREFLIGHT -> EXECUTOR -> TESTS/EVIDENCE -> PR -> HEDS DELTA AUDIT -> VERDICT -> CHECKPOINT DELTA -> MERGE -> NEXT`.
