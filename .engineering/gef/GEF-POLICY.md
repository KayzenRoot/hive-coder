# GEF V1 Local Policy — Hive Coder

## Authority
GEF governs execution/review only when compatible with canonical Hive Coder sources. Conflict => `SOURCE_CONFLICT`; canonical truth wins.

## Rules
- Think once, compile once, execute narrowly, prove incrementally, review only the delta.
- Deterministic tools before LLM calls.
- Smallest safe context radius first.
- Exact-head proof is required for governed approval.
- `UNKNOWN` never becomes PASS/ALLOW/zero.
- Git is canonical source history; derived evidence never replaces canonical docs.

## Task classes
`T0` mechanical; `T1` bounded patch; `T2` semantic correction inside frozen architecture; `T3` governed architecture work.

## Context radii
`C0` symbol+test; `C1` direct dependencies; `C2` module/interfaces; `C3` cross-module contracts; `C4` broad architecture.

## Risk
`LOW`, `STANDARD`, `ELEVATED`, `HIGH_ASSURANCE`. Desktop control, credential handling, privileged actions, signing, money, or irreversible actions default to `HIGH_ASSURANCE` when materially involved.

## Forbidden shortcuts
No fabricated evidence; no old-head proof as exact-head proof; no silent scope growth; no unrestricted repository exploration by default; no merge with HIGH/CRITICAL known defect; no destructive computer action without explicit authorization and recovery strategy.
