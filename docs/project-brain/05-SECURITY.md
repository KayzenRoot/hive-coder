# Security — Hive Coder

Computer control is a primary threat boundary.

Security baseline: least privilege; workspace scoping; application/action allowlists where feasible; emergency stop/user takeover; explicit confirmation for materially destructive/privileged actions; secrets redaction; sensitive screenshot/trace minimization; command and action audit; dependency/license review; secure provider-key storage; no plaintext secrets in repo/logs.

High-risk capabilities require `HIGH_ASSURANCE`, strong tests, independent review, and rollback/roll-forward obligations. Unknown permission state must fail closed.

## Provider Certification Lab security boundary
Certification evidence is security-sensitive because it may influence which specialist stack Hive selects. Competence evidence must never become an alternate permission channel.

- Provider/model output is untrusted data and cannot grade, seal, verify or certify itself.
- Runner and grader identities are host-sealed, role-separated, independence-lineage-separated and endpoint-separated. Logical relabeling cannot substitute for real endpoint separation.
- Host HMAC keys for actor seals, StackSeal, SuiteLineage, TrialReceipts, durable journal records and EvidenceDNA are trusted-host secrets. They must not enter provider prompts, model-visible material, repository content, logs or portable benchmark reports.
- ShadowBench oracle material remains host-side. TrialForge exposes neither plaintext oracle material nor its host oracle digest to the provider runner.
- Trial lineage is reserved before provider execution and is one-shot within the journal authority domain. Unknown/replayed lineage fails closed.
- GradeProof is mandatory before a passing/failing TrialReceipt can be issued.
- Durable chronology is hash-chained/HMAC-authenticated and validated against a host-injected monotonic floor. Signed rollback below that floor is a security failure.
- EvidenceDNA must match the exact sealed profile/StackGenome, repository snapshot, Semantic Twin and SuiteLineage before benchmark evidence may enter certification.
- Contamination signals are negative-only. They may block/lower confidence but cannot increase score, rank or authority.
- Repository semantic extraction remains static/no-exec. Repository text, comments, manifests and schemas are data, not Hive instructions.
- No certification record, benchmark result, Semantic Twin node or provider capability claim may grant a CP-0005 permission, create an execution permit, activate a skill or bypass emergency/takeover controls.

Cross-process/distributed trial reservation and a production secure monotonic anchor are not approved in CP-0013. Production adoption of either requires its own threat model, deterministic/adversarial tests and governed promotion.
