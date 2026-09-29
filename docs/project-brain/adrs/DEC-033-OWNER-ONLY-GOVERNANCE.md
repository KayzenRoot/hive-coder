# DEC-033 — Owner-only GitHub governance without mandatory collaborators

**Status:** PROPOSED, pending HCODER-OPS-0001 / Issue #95 / PR #96 owner-recorded exact-head audit, required CI, guarded squash merge and exact-main postvalidation.  
**Requested by:** `KayzenRoot`, 2026-09-29.  
**Affected:** prospective PR review identity, Work Order/Context Lock acceptance, HEDS review evidence and merge eligibility.  
**Unchanged:** historical accepted CP predicates, product security/permission/release boundaries, objective CI and code-owner attribution.

## Context and evidence

The owner explicitly wants the `KayzenRoot` account to handle its own repository planning, PR corrections, risk acceptance and merge without needing collaborator accounts. The active Hive Coder repository ruleset `hive-main-governed` (#23768014) already requires **zero** approving GitHub reviews, has no named mandatory reviewers and does not require CODEOWNERS approval. It still requires a pull request, a current target/base, squash merge, resolution of blocking review threads, and 13 exact-head GitHub Actions status checks belonging to four workflows: Governance, Desktop Shell, Native Package Matrix and Protected Release. These objective barriers must remain active. The same-account PR author must never claim a self-authored GitHub `APPROVE` review as independent review. Paid/credit-limited bot services and other collaborators must not become project prerequisites.

## Decision

1. **Sole mandatory GitHub actor:** the `KayzenRoot` owner may author a Work Order, implement through authorized tools, perform review, record an owner risk/merge decision, squash-merge under existing rules and close out using fresh exact-main evidence. A collaborator, invited reviewer, another GitHub identity or paid review service is **not required**.
2. **Separation of duties, not fabricated people:** planning, execution and security review remain separate, individually recorded *activities*. If all are completed by the owner or owner-controlled agents, the semantic review MUST be described as `OWNER_SELF_AUDIT / NOT_INDEPENDENT`. It may incorporate separately run challenge agents, static analyzers or outside review as optional, explicitly provenance-labeled inputs; those cannot mint a human-independent verdict or substitute for required tests.
3. **Owner semantic review contract:** the exact candidate SHA/base, authoritative source fingerprints, closed allowed-file list, all changed code/behavior, threat model and negative/adversarial test coverage, dependency/security findings, exact-head GitHub check IDs and conclusions, open findings by severity, blocking review threads, recovery and proposed checkpoint delta must be documented. A new head resets the owner audit and required CI evidence. A `PASS` for mechanical tests never proves unchecked claims.
4. **Merge admission:** applicable exact-head required status checks must be SUCCESS and the GitHub protection/ruleset must genuinely allow merging, with zero unresolved CRITICAL/HIGH, no unresolved blocking review thread or scope breach, and owner semantic acceptance recorded in the PR. Missing credentials, signing/notarization, release publication, real hardware/browser E2E and other unproven tests remain SKIPPED/UNKNOWN rather than PASS. Use expected-head-protected squash; post-merge validate the new exact `main` before declaring the Work Order complete.
5. **HIGH_ASSURANCE:** additionally require explicit owner-recorded threat/risk review, adversarial/fail-closed/negative-test evidence and confirmation that no permissions, credentials, trust roots, installation or publication were silently broadened. If the critical evidence is absent or any HIGH/CRITICAL defect remains, STOP regardless of available GitHub merge privileges. An owner cannot self-grant a runtime end-user permission, bypass user consent or assert an external publisher signature just by owning GitHub.
6. **Prospective only:** previously recorded `independent HEDS` results and completed CP-0020..CP-0026 effectiveness receipts remain immutable historical facts. Future accepted Work Orders may satisfy the semantic review gate with documented owner self-audit and unchanged objective checks instead of a second GitHub account. HCODER-WO-0027 receives a forward-only Context Lock Delta 004 under this operational change; product bytes stay frozen until the no-external-HIVE migration is postvalidated.
7. **Other repos/future projects:** this ADR governs Hive Coder once merged, not the contents or security settings of every other KayzenRoot repository. Reuse the approach through each repository's own governed change and use GEF Bootstrap as a prospective template; do not silently bypass existing local branch protections.

## Rejected alternatives

- **Mandatory `kayzenweb3` or another reviewer:** rejected by owner choice. An invitation by itself is not security evidence.
- **Call owner self-review independent:** rejected as misleading and damaging to audit provenance.
- **Disable required CI or create owner branch-protection bypass:** rejected; existing objective barriers preserve the ability to stop unsafe merges.
- **Require a credit-limited PR-review bot:** rejected as a mandatory dependency. Treat valid bot findings as untrusted claims, verify against current source and close them through code/test evidence or documented reason.

## Acceptance

This decision stays PROPOSED until the operational migration and this governance delta are reviewed on the same exact PR HEAD, all required workflows are green on that SHA, the owner records `OWNER_SELF_AUDIT / NOT_INDEPENDENT` with HIGH/CRITICAL 0/0 and no blocking threads, GitHub allows a rules-compliant squash merge from `KayzenRoot`, and the resulting main receives fresh exact-main validation. Thereafter no future Hive Coder increment may demand a second human GitHub account solely for procedural approval unless the owner adopts a new prospective decision.
