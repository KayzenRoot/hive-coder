# HEDS Delta Review Prompt — Hive Coder

Audit `<WORK_ORDER_ID>` independently against canonical source hierarchy, acceptance criteria and DoD.

Start with exact base/head and the delta. Identify invalidated proofs before reusing evidence. Check regressions, security, desktop-control permissions, data integrity, contracts, error handling, tests, complexity and checkpoint proposal. Do not treat executor claims as proof.

Output in Brazilian Portuguese using `.engineering/templates/REVIEW-TEMPLATE.md` and exactly one verdict: `APPROVED`, `CORRECTION REQUIRED`, or `BLOCKED`. If correction is required, specify only the bounded Correction Delta. Do not generate the next increment.

Review deliverable law (`.engineering/gef/GEF-REVIEW-PROTOCOL.md`): every completed review must already deliver the next executable executor prompt as a generated PDF in the same response as its verdict. `APPROVED` delivers the next increment prompt; `CORRECTION REQUIRED` delivers the bounded same-Work-Order Correction Delta prompt; `BLOCKED` delivers a bounded unblock prompt when one can be stated objectively. No new increment before predecessor acceptance. A review without its PDF is incomplete.
