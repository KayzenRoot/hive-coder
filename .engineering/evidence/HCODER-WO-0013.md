# Evidence Bundle — HCODER-WO-0013

**Risk:** HIGH_ASSURANCE  
**Base:** `3dee30634f48420f7c7ffa1b2c2186066dad97d0`

## Required invariants
- provider/model cannot grade or certify itself;
- runner/grader identities are host-sealed, role-bound and independence-separated;
- exact trial identity binds sealed Agent Profile/stack plus provider/model/repository/semantic twin/case/protocol;
- trial replay for the same profile/case lineage is rejected durably;
- chronology is HMAC-authenticated and rollback below an external monotonic floor fails closed;
- model-visible material contains no plaintext oracle secret;
- benchmark evidence derives only from sealed trial receipts;
- semantic repository extraction is static/no-exec and deterministic;
- contamination suspicion is downgrade/block-only;
- no CP-0005..CP-0012 authority expansion.

## Deterministic evidence target
Semantic symbols/imports/calls/routes/schema/dataflow; no-exec fixture; twin drift; bounded Dependency Cortex; journal restart/rollback/tamper; actor lineage collapse; exact-stack drift; trial replay; contamination block; benchmark evidence tamper; broad Linux regression; unchanged Windows HIGH_ASSURANCE regression.

## HEDS target
Attempt provider self-grading, actor identity spoofing, trial/stack replay, suite-family gaming, signed journal rollback, oracle leakage, fabricated benchmark evidence, stack portability, semantic extractor execution, contamination score inflation, and any path that converts repository/evaluation evidence into permission authority. UNKNOWN is not PASS.
