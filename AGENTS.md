# Hive Coder agent guidance

## Source of truth
Canonical truth lives in `docs/project-brain/` with precedence: latest approved checkpoint > Decisions Ledger/ADRs > Scope > Definition of Done > Architecture > Requirements > remaining sources.

## Chat continuation handoff
For cross-chat continuation, GitHub Issue `#30` (`[CONTINUATION] Hive Coder — CURRENT CHAT CHECKPOINT · READ FIRST`) is the mutable operational handoff pointer.

When the user says `continue do chat anterior`, `continue`, or equivalent continuation language for Hive Coder:
- read Issue `#30` before reconstructing work from memory;
- then reconcile it against the canonical Project Brain, the active Work Order/PR, and fresh exact-head GitHub evidence;
- GitHub/canonical truth wins if the handoff is stale;
- update Issue `#30` at every approved checkpoint, merge, major correction, or intentional stop point so the next chat resumes from the exact current position;
- never ask the user to repeat context already recoverable from the handoff and canonical sources.

Issue `#30` is a resume pointer only. It does not override approved checkpoints, Decisions, Work Orders, security boundaries, or evidence requirements.

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
