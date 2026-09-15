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

## Elite Specialist Forge & Arena security boundary
WO-0014 treats specialist composition, arena evidence and routing as security-sensitive competence metadata, never as execution authority.

- `SpecializationPack`, `SkillGenome`, specialist labels, model/provider names and self-description contain zero permission or rank authority.
- ForgeSeal must verify the sealed AgentProfile and bind the exact StackGenome, repository snapshot, Semantic Repository Twin, trusted SpecializationPack, exact SkillGenome and trusted certification evidence. Unknown/tampered/transplanted context fails closed.
- SkillGenome must fingerprint-match the StackGenome skillset digest before a specialist blueprint can exist. Caller-controlled skill labels cannot transplant competence to another stack.
- ChallengeMorph may vary a trusted ShadowBench challenge only under sealed SuiteLineage. Challenge variants do not create independent mastery when they share one sealed base source lineage.
- Anti-Overfit Horizon protections are enforced again when evidence enters Mastery Lattice. Bypassing the helper cannot manufacture diversity.
- ArenaEvidence is admitted only when GradeProof, challenge/blueprint identity, repository/twin bindings and telemetry verification all match.
- Arena telemetry is non-authoritative until a trusted host-injected verifier accepts it. Cost/latency observations can never relax security, quality or reliability floors.
- Reliability Shadow is negative-only. Operational regressions may block/demote/force recertification but positive observations cannot mint benchmark evidence or rank.
- Pareto Crown directly revalidates AgentProfile authority and exact certification context at final routing time. Critical, policy and tamper incidents block selection before optimization.
- Competence artifacts cannot create CP-0005 permits, activate skills, grant credentials, authorize purchases/billing, expose remote control or bypass emergency/takeover controls.
- Hosted CI remains mock/deterministic. It proves contracts and adversarial invariants only, not the security or elite quality of any real provider stack.

Production attestation for real provider billing/latency/reliability telemetry and durable cross-restart mastery/reputation are not approved in WO-0014. Any future `TelemetrySeal` or `MasteryVault` must receive a separate HIGH_ASSURANCE threat model, rollback protection, adversarial tests and governed promotion before use.
