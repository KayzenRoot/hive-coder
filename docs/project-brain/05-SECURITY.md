# Security — Hive Coder

Computer control is a primary threat boundary.

Security baseline: least privilege; workspace scoping; application/action allowlists where feasible; emergency stop/user takeover; explicit confirmation for materially destructive/privileged actions; secrets redaction; sensitive screenshot/trace minimization; command and action audit; dependency/license review; secure provider-key storage; no plaintext secrets in repo/logs.

High-risk capabilities require `HIGH_ASSURANCE`, strong tests, independent review, and rollback/roll-forward obligations. Unknown permission state must fail closed.
