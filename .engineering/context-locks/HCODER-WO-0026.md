# HCODER-WO-0026 — Context Lock

**Status:** LOCKED FOR PREBUILT IMPLEMENTATION  
**Issue:** `#85`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Slice:** `HCODER-DIST-001C` — signing, notarization, release provenance and protected release workflow  
**Canonical base:** `HCODER-CP-0025` / `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`  
**Risk:** HIGH_ASSURANCE (release authority, code-signing identity, notarization, supply-chain provenance, CI permissions)  
**Authority delta:** a closed release-provenance **contract**, an offline fail-closed **validator/admission gate**, and a **promotion-pipeline workflow definition** whose credential-bearing stages are structurally gated and whose publication stage is not executed. No signing identity, no credential, no release, no tag, no updater, no installation and no production-distributable claim is admitted.

> **Historical scope of the delta record.** This file is the canonical **append-only** authority and delta history for `HCODER-WO-0026`. Every delta records what was authorised, required or true **at its own stage**; any phase, PR, review, gate or merge wording inside a delta describes that stage and is not a current-state field. Current mutable state lives externally in the active Draft PR and Issues #30 and #85. Only the deltas' *law* (allowed files, prohibitions, predicates) carries forward. No terminal delta number or range is mirrored into any other file.

## Source check

Verified against the base revision itself, not against conversation memory. Each fingerprint is the git blob SHA of the named path at `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`, recomputable with `git rev-parse <base>:<path>`.

| Source | Path | Blob fingerprint |
| --- | --- | --- |
| checkpoint | `docs/project-brain/11-CHECKPOINT.md` | `7f26b7b80dedd8ca4c84982d83b0b8e81676d95e` |
| decisions | `docs/project-brain/10-DECISIONS-LEDGER.md` | `95742851df091a10a33cf7a32b841efa00471bbe` |
| scope | `docs/project-brain/03-SCOPE.md` | `330ce490cc29fc5f3ba4e612db8935dd982d745c` |
| requirements | `docs/project-brain/02-REQUIREMENTS.md` | `35cb36929580e215a8fa3cc04b199f5e20b76dce` |
| definition-of-done | `docs/project-brain/09-DEFINITION-OF-DONE.md` | `9770301f87703ec9a24b6c17525c6b55a23da317` |
| architecture | `docs/project-brain/04-ARCHITECTURE.md` | `446a0c47f9ac1be4ce4817c97cd258e7b749129e` |
| security | `docs/project-brain/05-SECURITY.md` | `1cede4091b2f27523eccca4e3febe1eb3c1bc248` |
| deployment | `docs/project-brain/07-DEPLOYMENT.md` | `db5e7a4ab23b9b5eb7e5bc1d9e48d801b67e78e4` |
| contract precedent | `docs/project-brain/contracts/RUNTIME-STATUS-IPC-V1.md` | `6a1b42b44bebd6a8333548f63ea634fc0d834962` |
| predecessor ADR | `docs/project-brain/adrs/DEC-029-NATIVE-PACKAGE-MATRIX-EVIDENCE-CONTRACT.md` | `f3bf1a1834ab3d901063b71cb901b2b76200bf74` |
| canonical config | `apps/desktop/src-tauri/tauri.conf.json` | `e371abe0eeec26f8c784433538ce556180e3af0f` |
| npm manifest | `apps/desktop/package.json` | `ce0c08075add0279bb5d5a3f27167e1d413fe35d` |
| inventory tool | `tools/desktop/package_inventory.py` | `b071f7ba238d6fdcd61196a99be61d5bb8418667` |
| version drift tool | `tools/desktop/version_drift.py` | `cb078deb81063d56db135940c01a3e7a729729cc` |
| channel contract | `apps/desktop/src/contracts/releaseChannel.ts` | `0e39f972db523bcf5bb0f531787870f02cd03968` |
| governance workflow | `.github/workflows/governance.yml` | `1f823d7672f95217ca144a4fe8c8d96f318b63d4` |
| desktop workflow | `.github/workflows/desktop-shell.yml` | `7eb76979345c554dacc1b3a5fac0a26a0019367e` |
| package workflow | `.github/workflows/native-package-matrix.yml` | `118bbbe8f453dd130852d97a40b2e0781ab71d92` |
| agent law | `AGENTS.md` | `1af0df9be7b88e680a5142ac75a39db925b7bf10` |
| python dependency lock | `foundations/python-dependencies.lock.json` | `236a7dd62089fd3723a46d76c75a091f490a2757` |

Repository facts established by the source check:

- `origin/main` equals the expected canonical base and the working tree is clean; the predecessor `HCODER-WO-0025` remains objectively accepted, so `HCODER-WO-0026` is the next necessary increment.
- All eleven published check jobs on the base head report `success`, including `Governance`, the four `Desktop Shell` lanes and the three `Native Package Matrix` lanes.
- `docs/project-brain/contracts/` contains exactly one file today; `hive-package-inventory-v1` has **no** contract document and no JSON Schema anywhere in the repository. Hive's closed-schema law is enforced in Python by ordered key tuples plus a single exception type. The new contract therefore follows that convention rather than introducing a schema language.
- Python tests are `unittest`, discovered by `python -m unittest discover -s tests -p "test_*.py"` under `PYTHONWARNINGS: error::ResourceWarning`; there is no pytest and no third-party YAML or schema library in the governed dependency lock, whose only entry is `dulwich`.
- The repository is public, which is the precondition for GitHub artifact attestations on the public-good Sigstore instance at no additional plan cost.
- The three existing workflows declare no `concurrency`, no `environment`, no `tags`, no `release` and no `workflow_dispatch`; only `native-package-matrix.yml` declares `permissions: { contents: read }`; `Governance` and `Desktop Shell` declare no `permissions` block at all; nothing uses `pull_request_target`; the six targets are produced by three hand-written per-OS jobs, not a `strategy.matrix`; exactly one third-party action is SHA-pinned.
- Hosted protection state observed at source-check time: `0` environments, `0` repository Actions secrets, `0` repository variables; `GET .../environments/production` returns `404`. The environments collection endpoint is readable **without authentication** on this public repository, which is what makes an in-workflow protection probe objectively possible. This is mutable external state and is re-proved before any credentialed claim.
- Verified current-toolchain facts that constrain `DEC-030`: `altool` notarization has been refused by Apple since 2023-11-01, so `xcrun notarytool` is the notarization path; Microsoft renamed "Azure Trusted Signing" to **Azure Artifact Signing** and the `trusign` CLI no longer resolves; `actions/attest` v4 requires `artifact-metadata: write` in addition to `id-token: write`, `attestations: write` and `contents: read`, and v4 has no in-repo verify action, so verification is `gh attestation verify`; **a workflow that references a non-existent environment creates it with no protection rules rather than failing**; and `EV` no longer bypasses SmartScreen reputation.

## Selected first slice

One closed contract (`hive-release-provenance-v1`), one stdlib-only offline validator and admission gate, one focused adversarial test module, one promotion-pipeline workflow with a secret-free exact-head preflight lane, and the governed documents plus `DEC-030` at PROPOSED. Publication is structurally present and deliberately not executed.

## Authority boundary law

1. This Work Order authorises **contract, validation and workflow-definition** work only. It authorises no credential to be read, requested, written, decoded, imported or configured.
2. It grants no signing, notarization, stapling, release, tag, GitHub Release, artifact-publication, updater, download, install, restart or rollback authority, and no publisher-authenticity claim.
3. It expands no Hive runtime capability. CI release authority and product runtime authority are different domains: `Capability.GIT_WRITE`, `Capability.FILESYSTEM_WRITE`, permission gates, the control plane and the desktop security gate surface are untouched.
4. It creates no GitHub environment, secret, variable, protection rule, branch rule, ruleset or immutable-release setting. Such shared-state provisioning is external, is reported as a blocker with its credential class and verification condition, and is never performed from an executor prompt.
5. A missing credential or absent protected environment fails closed. It is never a reason to publish unsigned, to report `PASS`, or to reduce the six-target matrix.

## Security law

1. **Never leak.** No secret value may be printed, echoed, persisted, committed, uploaded as an ordinary artifact, cached, placed in a test fixture, exposed in a command trace or process argument where avoidable, written into a provenance manifest, or stored in HIVE, a PR body or an Issue body.
2. **No untrusted-code credential path.** `pull_request_target` and any equivalent that would expose release credentials to pull-request code are prohibited.
3. **Least privilege at workflow and job level.** A job that does not need write, OIDC or release authority must not receive it. The top-level `permissions` of the new workflow is `contents: read`, which is stricter than `Governance`/`Desktop Shell` defaults because those lanes predate this Work Order and are not modified.
4. **Short-lived identity first.** Where the selected signing service supports OIDC, a long-lived cloud credential must not be introduced merely because it is easier.
5. **Protection must be proven.** A named environment and its actual protection semantics must be objectively proven before any job claims to be protected. `protection_rules` entries and `can_admins_bypass` are inspected, because an admin-bypassable gate is not a gate.
6. **Only public, independently verifiable identity metadata.** Certificate fingerprint/subject and timestamp-authority identity may be recorded; private key material may not.
7. **Attestation is provenance, not publisher trust.** A SLSA/GitHub attestation binds an artifact to a build identity; it does not sign the artifact for an operating system and must never satisfy a signing requirement.
8. **Deterministic over timely.** The contract carries no wall-clock field, so a receipt cannot silently age into a different claim.
9. **Non-vacuity.** Every refusal listed in the acceptance map must be demonstrated by a test that fails when the guard is removed.
10. **Reporting without values.** If external setup is required, report the credential class, provider/mechanism, documented secret or environment slot name, and the exact verification condition — never a value, and never a request for one.

## Allowed-file set

This Work Order may change only:

- `.engineering/work-orders/HCODER-WO-0026.md`
- `.engineering/context-locks/HCODER-WO-0026.md`
- `.engineering/prebuilt/HCODER-WO-0026-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0026-EXECUTOR-BRIEF.md`
- `.engineering/prebuilt/HCODER-WO-0026-ACCEPTANCE-SECURITY-MAP.md`
- `.engineering/evidence/HCODER-WO-0026.md`
- `docs/project-brain/adrs/DEC-030-SIGNING-NOTARIZATION-RELEASE-PROVENANCE.md`
- `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md`
- `.github/workflows/protected-release.yml`
- `tools/desktop/release_provenance.py`
- `tests/desktop/test_release_provenance.py`
- `AGENTS.md` — bounded source-accuracy reconciliation of the stale current-execution-state and next-action material only
- `docs/project-brain/07-DEPLOYMENT.md` — bounded source-truth correction where packaging status would otherwise be misstated as unplanned

## Forbidden files

`docs/project-brain/11-CHECKPOINT.md` and any Checkpoint Delta, because `CP-0026` may not be claimed before governed promotion; `docs/project-brain/10-DECISIONS-LEDGER.md` until the Delta 001 expansion below; every historical ADR, Work Order, Context Lock, Evidence Bundle, closeout file and correction record, because Decisions and Context Locks are append-only history; `docs/project-brain/02-REQUIREMENTS.md`, `03-SCOPE.md`, `04-ARCHITECTURE.md`, `05-SECURITY.md`, `09-DEFINITION-OF-DONE.md`; `apps/desktop/src-tauri/tauri.conf.json` and every manifest, lockfile and product source; `.github/workflows/governance.yml`, `desktop-shell.yml` and `native-package-matrix.yml`, whose triggers, permissions and steps are preserved byte-for-byte; `hive_runtime/**`, `apps/desktop/src/**` and any control-plane, permission, capability or runtime file; `foundations/**`; any dependency, plugin, permission or capability addition; and any updater, endpoint, installer or packaging configuration.

## Exact-head evidence law

- Evidence proves only the exact SHA it names; a new head invalidates the old head's receipts.
- Post-change evidence must be re-run for `Governance`, `Desktop Shell`, `Native Package Matrix` and the new `Protected Release` lane on the final candidate head.
- Independent HEDS must return unresolved HIGH/CRITICAL `0/0` on that exact head before any promotion is even discussed, and the executor may not issue it.
- Credentialed native execution that cannot occur for want of external provisioning is recorded `UNKNOWN`/`BLOCKED`. `UNKNOWN` must never be converted into `PASS`.

## STOP CONDITION

STOP before credential-backed execution while `DEC-030`, this Work Order or this Context Lock is not materialized and internally consistent. STOP if any secret, private key, certificate, notarization credential, token or password would need to be printed, committed, stored in HIVE, uploaded as a normal artifact or passed through an unsafe channel. STOP if release protection cannot be objectively proven, and never claim a protected release from YAML intent alone. STOP if Windows or macOS signing requires an external account, certificate or service that is not already provisioned: finish the secret-independent substrate and report the exact provisioning blocker without values. STOP if a platform target can only succeed by reducing the CP-0025 six-target matrix or weakening an existing gate. STOP if the implementation requires updater, download, install, restart or rollback authority, generic Hive credential authority, or unrelated product runtime capability. STOP if any HIGH or CRITICAL remains unresolved, any required exact-head gate is red, or the candidate head changes after evidence was collected. STOP before merge.

---

# Context Lock Delta 001

**Status:** ALLOWED-FILE-SET EXPANSION AUTHORISED — same Work Order  
**Authority granted:** exactly one additional path, `docs/project-brain/10-DECISIONS-LEDGER.md`, and within it exactly one appended `DEC-030` entry marked PROPOSED / NOT CANONICAL. No other path, no existing entry, no historical Decision, and no terminal delta range anywhere else.  
**Trigger:** source check established that the repository's Decision law is index-plus-ADR: `DEC-022` … `DEC-029` each carry a ledger entry, and `DEC-029`'s ADR is read together with its ledger entry. An ADR for `DEC-030` with no ledger entry would leave the canonical Decision index silently incomplete, which is a source-truth defect the prompt's own §11 anticipates by requiring such expansion to be recorded here **before** the edit rather than smuggled in afterwards.

**Recorded before the edit.** The base `AGENTS.md` instruction "Never silently rewrite historical Decisions or Context Locks" is honored by construction: this delta only **appends** a new entry, and the new entry's status wording states its own non-canonical condition explicitly so no later reader can mistake an ADR proposal for a promoted Decision.

**Allowed paths, exactly:** `docs/project-brain/10-DECISIONS-LEDGER.md` (one appended `## DEC-030 — …` entry, status PROPOSED / NOT CANONICAL).  
**Forbidden:** every other ledger entry, all pre-existing bytes of the file, `11-CHECKPOINT.md`, and every `.engineering/checkpoint-deltas/` file.  
**Preserved:** the `## Forbidden files` clause above remains in force for all other paths and is not widened.

**Anti-self-staling test applied.** Before merge: this delta is the only authority for the ledger edit, and the ledger entry must be findable from the ADR. After merge: a reader who has only the ledger sees a PROPOSED Decision and is pointed at this Work Order, so the delta cannot be used to imply promotion. If the ledger edit had instead been folded silently into the original allowed set, the same edit would be unattributable — which is the failure mode this delta exists to prevent.

## STOP CONDITION (Delta 001)

STOP if the appended entry would read as canonical, or if any pre-existing ledger byte changes. This delta grants index-completeness, never promotion.

---

# Context Lock Delta 002

**Status:** ALLOWED-FILE-SET EXPANSION AUTHORISED — same Work Order  
**Authority granted:** exactly one additional path, `tests/desktop/test_protected_release_workflow.py`, a new standard-library `unittest` file that statically audits `.github/workflows/protected-release.yml`. No other path.  
**Trigger:** Work Order acceptance requires that the protected-release workflow *"exists with least-privilege permissions, no secret exposure on pull requests, exact-SHA preflight, isolated per-OS signing stages, provenance generation **and** verification, an objective environment-protection probe, and a separately gated publication stage."* A YAML file cannot satisfy that clause by assertion: a job that quietly drops an `environment:`, widens `permissions:` or interpolates a secret into a pull-request-reachable command leaves the repository green and the claim false. The repository's own law — *"Every guard must be demonstrated non-vacuous by a failing test when removed"* — therefore requires a machine check of the workflow text, and no such check exists anywhere in `tests/` today. Recording the need here, before writing the file, is the governed route; folding the path into the original list after the fact would leave the edit unattributable.

**Recorded before the edit.** The base `AGENTS.md` instruction "Never silently rewrite historical Decisions or Context Locks" is honored by construction: this delta appends, and the file it authorizes reads the workflow under test rather than altering it.

**Allowed paths, exactly:** `tests/desktop/test_protected_release_workflow.py` (new file).  
**Constraints on the authorized file:** standard library only, matching `tools/desktop/release_provenance.py` and `tests/desktop/test_package_inventory.py`; no new dependency and no `PyYAML`, so the governed Python lockfile stays untouched; offline, no network, no subprocess, no credential read; must remain green under `PYTHONWARNINGS=error::ResourceWarning`, since `Governance` runs the discovered suite on every promotion head. It may read `.github/workflows/*.yml` as text; it may not write to any workflow.  
**Forbidden:** modifying `.github/workflows/protected-release.yml` *through* the test, and reading any file outside `.github/workflows/` plus this Work Order's own governance artifacts. `governance.yml`, `desktop-shell.yml` and `native-package-matrix.yml` remain byte-for-byte immutable, so the test may assert facts about them but can never move them.  
**Preserved:** the `## Forbidden files` clause above remains in force for all other paths and is not widened. Delta 001's grant is unchanged and this delta does not reach the Decisions ledger.

**Non-vacuity requirement carried by this delta.** Each assertion in the authorized file must be paired with a documented mutation that would flip it, and the test must be shown to fail when the workflow's corresponding safety line is removed. An assertion that passes against every possible workflow is not evidence of anything and must be deleted rather than kept as decoration.

## STOP CONDITION (Delta 002)

STOP if the authorized test would need to relax an assertion to stay green, or if it requires a YAML parser dependency, network access, or any write into `.github/`. STOP if proving a policy claim would require executing a credentialed job — the test is a static audit of text, and the objective protection evidence belongs to the in-workflow probe, not to the test suite.

---

# Context Lock Delta 003

**Status:** CORRECTION-SCOPE AUTHORIZATION — same Work Order, same Draft PR, no authority expansion  
**Trigger:** Independent review `5261683447` of candidate head `374e642fb901ce21e1b8886fb80addccbfe89add` returned `CORRECTION_REQUIRED` with counts CRITICAL `0` / HIGH `1` / MEDIUM `2` / LOW `0`. The findings are `H-43-01` (the signing jobs bound external signing material through `${{ secrets.* }}` and tested presence with `printenv`, so a real credential value would be resolved before the unconditional barrier and `VALUES_READ=NO` was not structurally true), `M-43-02` (the attestation named only `hive-package-inventory.json` as its subject, so provenance bound the manifest rather than the native package identities), and `M-43-03` (the external provisioning map was incomplete and partly invented: an Apple App Store Connect API-key flow was recorded without its issuer identity and with `APPLE_TEAM_ID` standing in for it, and the OIDC-federated Azure path was recorded as three identifiers without the Entra application, federated trust, role assignment or service instances that make it exist).  
**Authority granted:** the smallest edits that close exactly those three findings, within paths this Work Order already governs, plus one reauthorization (below). It grants no new capability, credential, environment, permission scope, product surface or checkpoint claim, and it does not reopen any property the review accepted.

**Reauthorization, stated explicitly because it is the only real change in law.** `tests/desktop/test_protected_release_workflow.py` was authorized by Delta 002 as a file to be *created*. Closing `H-43-01` requires it to be *modified*, so this delta reauthorizes it as a live audit surface: assertions may be added and strengthened, and an assertion whose mechanism has been deleted by `H-43-01` may be replaced only by an equal-or-stronger check over the new mechanism. No pre-existing test method may be deleted, no expectation relaxed, and no case skipped or commented out. An existing anchor string may disappear only when the workflow line it anchored is itself removed under `H-43-01`, and the removal must be named in this Work Order's evidence file.

**Allowed paths, exactly:**

| Path | Why this finding requires it |
| --- | --- |
| `.engineering/context-locks/HCODER-WO-0026.md` | This record. |
| `.github/workflows/protected-release.yml` | `H-43-01` deletes the secret bindings and value probes from the two signing jobs; `M-43-02` re-derives the attestation subject set from the already validated inventory. |
| `tests/desktop/test_protected_release_workflow.py` | The audit must kill reintroduction of an external-signing-secret expression, a value probe, a certificate/key import, a cloud login or a real signing command, and must assert the exact subject set. |
| `tools/desktop/release_provenance.py` | Only to make the attestation-subject chain determinable and checkable offline; not for prose. |
| `tests/desktop/test_release_provenance.py` | Only where validator subject semantics change. |
| `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md` | The contract must state truthfully what the attestation subjects are. |
| `docs/project-brain/adrs/DEC-030-SIGNING-NOTARIZATION-RELEASE-PROVENANCE.md` | `M-43-03` corrects the Apple and Azure external-identity material; `M-43-02` corrects the subject-model material. |
| `.engineering/prebuilt/HCODER-WO-0026-EXECUTOR-BRIEF.md` | The external provisioning table is the source of truth for `M-43-03`. |
| `.engineering/prebuilt/HCODER-WO-0026-ACCEPTANCE-SECURITY-MAP.md` | Rows describing slot reporting and attestation subject scope must match the corrected source. |
| `.engineering/prebuilt/HCODER-WO-0026-IMPLEMENTATION-PACK.md` | Only where it describes the changed mechanism. |
| `.engineering/evidence/HCODER-WO-0026.md` | Correction evidence. |
| `.engineering/work-orders/HCODER-WO-0026.md` | Only where its text would otherwise contradict the corrected source. |

**Not authorized, and why.** `docs/project-brain/10-DECISIONS-LEDGER.md` is **not** used by this delta: the Delta 001 `DEC-030` ledger entry names no Apple or Azure slot and makes no manifest-subject claim, so no finding requires an edit there, and the append-only grant of Delta 001 remains the only ledger authority. `AGENTS.md` and `docs/project-brain/07-DEPLOYMENT.md` stay byte-identical: their accepted source-truth corrections are not reopened by any of the three findings. `docs/project-brain/11-CHECKPOINT.md` and every `.engineering/checkpoint-deltas/` file remain forbidden, `tools/desktop/package_inventory.py` and the six-target packaging matrix remain out of reach, and `governance.yml`, `desktop-shell.yml`, `native-package-matrix.yml`, `apps/desktop/**`, `hive_runtime/**`, `foundations/**`, every manifest and every lockfile remain immutable. No new repository path is created by this correction: the attestation-subject input is a runner-temporary file derived at run time from the validated inventory, so no second inventory model and no new tracked file is introduced.

**Law carried by this delta.**

1. `H-43-01` is closed by construction, not by today's having zero secrets: the signing jobs resolve no external signing or notarization expression of any kind, contain no presence test, indirect expansion or parameter inspection of a named credential, and report required slot names, credential classes and verification conditions as static literals that a `workflow_dispatch` run prints without evaluating them.
2. This delta grants no credential-read, import, login or signing-execution authority. `id-token: write` is **not** added to `sign-windows` or `sign-and-notarize-macos`, cloud login steps, certificate or keychain import, `signtool`, `codesign`, `notarytool` and signing action execution all remain absent, and the signing jobs still end in an unconditional refusal that does not depend on provisioning state.
3. `M-43-02` preserves `hive-package-inventory-v1` as the single packaging model: the subject set is derived from the validated canonical inventory, never rediscovered from the repository, never broadened by a glob, and never silently narrowed. Attestation over the manifest bytes remains a separate integrity/upstream-evidence guarantee and must not be relabelled as package provenance. If an expected package identity cannot be represented truthfully as a GitHub attestation subject under the pinned official action's documented input model, `H-43-01`-grade honesty requires returning `BLOCKED_ATTESTATION_SUBJECT_MODEL` with the exact official-tool evidence rather than omitting the subject, substituting another artifact, or claiming a directory-tree digest as a file digest.
4. `M-43-03` is documentation and guard accuracy. Nothing is provisioned, no credential value or request appears, and every recorded name is a configuration identity or a slot name verified against current official Apple, Azure and pinned-Tauri documentation at execution time.
5. The four-guarantee separation (integrity ≠ provenance ≠ publisher signing ≠ platform trust) and publication as a fifth act survive the correction unchanged.
6. Evidence discipline: a new head invalidates run receipts `35533966793`, `35533966836`, `35533966792` and `35533966857` as current evidence, which are retained only as historical Prompt 43 receipts. `SKIPPED` and `UNKNOWN` are never reported as `PASS`.

## STOP CONDITION (Delta 003)

STOP if closing a finding would require reading or provisioning a real signing or notarization credential, weakening the six-target package matrix, weakening environment protection, reducing attestation subject coverage, changing canonical Tauri configuration, adding a product dependency, plugin, permission or capability, introducing updater, install, restart or rollback authority, publishing anything, or touching any historical canonical Decision or Checkpoint. STOP on any unresolved HIGH or CRITICAL, any red required exact-head gate, any stale-head mismatch, or any inability to represent a package attestation subject truthfully. `DEC-030` remains PROPOSED, no `HCODER-CP-0026` may be claimed from this delta, and the PR remains Draft: this delta authorizes correction, never promotion.

---

# Context Lock Delta 004

**Status:** PROMOTION-CANDIDATE PREPARATION AUTHORISED — same Work Order, same Draft PR, governance and state wording only, no technical authority  
**Trigger:** Independent review `5262493714` of technical head `0a1b8375e5c950d321f898b6d455eb874583c9a4` returned `APPROVED FOR GOVERNED PROMOTION-CANDIDATE PREPARATION` with counts CRITICAL `0` / HIGH `0` / MEDIUM `0` / LOW `0`, and its first executable next step is that this same Work Order, in this same Draft PR, append a bounded Context Lock delta authorising promotion-candidate governance artifacts before any of them is written. Prompt 45 is that request; this record is the authority it requires. The technical head was re-proved against `origin` before this delta was written and had not moved; PR `#86` was re-proved Draft, OPEN and unmerged; `origin/main` was re-proved to still be `1a56224eeb9bc07f032df1ede23bdda9d74f8d12`.

**What this delta authorises, exactly.**

1. Creation of `.engineering/checkpoint-deltas/HCODER-WO-0026.md` as a **PROPOSED / REVIEW PENDING** `HCODER-CP-0026` delta: the slice and Work Order it belongs to, its predecessor `HCODER-CP-0025`, the independently reviewed technical head and HEDS receipt with severity counts, the exact authority such a checkpoint would admit and the exact authority it withholds, the `HCODER_CP_0026_EFFECTIVE` predicate, the rule that a branch copy is a candidate and never a canonical claim, the evidence carry-forward semantics, the truthful rollback/roll-forward position, and the statement that the executor cannot self-promote or self-approve it.
2. Update of the **branch copy** of `docs/project-brain/11-CHECKPOINT.md` to carry the conditional `HCODER-CP-0026` candidate declaration. The existing checkpoint pattern requires this rather than merely permitting it: that file selects the authoritative checkpoint **by predicate** and states that *no edit here is required to flip any status*. A candidate that added no predicate line would make a later rewrite of the ladder necessary to express a fact the ladder already has to compute, which is the failure mode the pattern exists to prevent. `HCODER-CP-0025`, its record and its predicate remain in force and byte-preserved as history; the ladder is extended by one conditional rung, never edited backwards.
3. Reconciliation of status wording so the governance documents describe the reviewed state truthfully instead of the pre-review state: the Work Order, the `DEC-030` ADR header, the `DEC-030` ledger entry (the entry Delta 001 appended for this Work Order and no other ledger byte), this Work Order's Evidence Bundle, and bounded source-accuracy corrections to `AGENTS.md` and `docs/project-brain/07-DEPLOYMENT.md` **only** where the promotion-candidate wording would otherwise make one of them objectively false. `07-DEPLOYMENT.md` line 13 currently labels `DEC-030` as merely "Proposed, not canonical", and `AGENTS.md` currently repeats that label; after this round both statements would be false by omission, which is the whole of their authorisation. Neither file is opened for aesthetics.

**Allowed paths, exactly:**

| Path | Why the reviewed state requires it |
| --- | --- |
| `.engineering/context-locks/HCODER-WO-0026.md` | This record. Append-only; Delta 001–003 are preserved verbatim, and no earlier word of this file changes. |
| `.engineering/checkpoint-deltas/HCODER-WO-0026.md` | New file. The durable `HCODER-CP-0026` candidate declaration and its predicate. |
| `docs/project-brain/11-CHECKPOINT.md` | Branch copy only, and only the ladder/predicate lines plus the in-flight-increments text that must point at the candidate. The `HCODER-CP-0025` record is not rewritten. |
| `.engineering/work-orders/HCODER-WO-0026.md` | Status lines that still describe a pre-review candidate. |
| `docs/project-brain/adrs/DEC-030-SIGNING-NOTARIZATION-RELEASE-PROVENANCE.md` | Header status only. The Decision's substance was reviewed at `0a1b8375` and does not move. |
| `docs/project-brain/10-DECISIONS-LEDGER.md` | The `DEC-030` entry's status field and its promotion-gate paragraph, reconciled to the checkpoint delta's predicate. No entry from `DEC-001` to `DEC-029` may change by one byte. |
| `.engineering/evidence/HCODER-WO-0026.md` | The immutable review history and the promotion-candidate state. |
| `AGENTS.md` | Bounded source accuracy in the in-flight-increment and next-action wording only. |
| `docs/project-brain/07-DEPLOYMENT.md` | Bounded source accuracy at the one line labelling `DEC-030`'s status. |
| `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md` | One line only: the `**Governed by:**` header field carries `DEC-030 (PROPOSED / NOT CANONICAL)` as a **live status field**, and after this round the `PROPOSED` half is false. Discovered by the consistency sweep this round ran before committing, not by inspection of the prompt's list — the contract is contract law, so only its status label is authorized and every sentence describing the schema, the ladders, the admission rules or the verifier's authority is frozen here exactly as reviewed. |

**Override this delta is the only route to.** The base `## Forbidden files` clause forbids `docs/project-brain/11-CHECKPOINT.md` and any Checkpoint Delta, and Delta 001 bounds the ledger to one appended entry. Items 2 and 3 above are the governed expansion of exactly those two clauses, recorded before the edits, and nothing else in that clause is widened: every other historical Work Order, Context Lock, Evidence Bundle, closeout, correction record, ADR, `02-REQUIREMENTS.md`, `03-SCOPE.md`, `04-ARCHITECTURE.md`, `05-SECURITY.md`, `09-DEFINITION-OF-DONE.md` and every other file under `docs/project-brain/contracts/` remains forbidden.

**A correction to this delta's own first draft, recorded rather than quietly rewritten.** This record was written asserting that no sentence of `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md` would become false, and that the contract was therefore frozen whole. That assertion was wrong: the consistency sweep run before committing found its `**Governed by:**` header carrying `DEC-030 (PROPOSED / NOT CANONICAL)`, which is a live status field and not stage history, so the `PROPOSED` half became false the moment the Decision's label moved. The grant above names that one line and the freeze below keeps every other word of the contract byte-identical. The mistake is worth its own record because of how it was made: a status label was being classified as law by its file location rather than by what it asserts, and no reading of the prompt's freeze list would have caught it — only comparing the labels across files would.

**Required state vocabulary.** The reconciliation must say, and may say no more than:

- technical implementation: `IMPLEMENTED + independently reviewed at 0a1b8375e5c950d321f898b6d455eb874583c9a4; behavior frozen for promotion prep`;
- `DEC-030`: `APPROVED FOR PROMOTION CANDIDATE / NOT CANONICAL ON MAIN until HCODER_CP_0026_EFFECTIVE`;
- checkpoint delta: `PROPOSED / REVIEW PENDING`;
- PR `#86`: `OPEN / DRAFT / UNMERGED; not Ready until the new exact promotion head receives another independent review`;
- canonical checkpoint: `CP-0025 remains authoritative on main until CP-0026 effectiveness is objectively proven`.

**`HCODER_CP_0026_EFFECTIVE` (durable law, stated here so the delta file and the ledger cannot drift from it).** The predicate holds if and only if all three conditions hold **for one and the same promotion/closeout revision**:

- (A) that exact revision was independently reviewed at that exact head with unresolved CRITICAL `0` / HIGH `0` and no unresolved scope, preservation or evidence mismatch;
- (B) that exact reviewed revision was governed-merged into `main` under expected-head protection, and the resulting merge preserved the reviewed tree;
- (C) the resulting exact `main` SHA passed fresh `Governance`, `Desktop Shell`, `Native Package Matrix` **and** `Protected Release` launched from that `main` SHA, where no PR-head, adjacent-SHA or earlier-head receipt may satisfy the condition.

The predicate depends on properties only. It must never name a future merge SHA, a future run ID, a review ID, a PR state, an Issue state or a guessed "current main" value, because a law that encodes its own evidence cannot fail. Immutable reviewed-head facts may be recorded as historical evidence — they prove a technical stage and nothing else — but future success is never pre-written, and no text in this repository asserts that the predicate currently holds.

**Evidence carry-forward law this delta imposes.** Review `5262493714` proves the technical bytes at `0a1b8375` only. It carries forward to a later head **solely while the technical freeze below remains exact and the later head's added content is governance text**; it does not carry forward to the promotion decision itself, which requires fresh exact-hosted gates and a fresh independent review of the new head. Superseded evidence stays recorded, including the `CORRECTION_REQUIRED` review of `374e642fb901ce21e1b8886fb80addccbfe89add`, which is history rather than an embarrassment.

**Technical freeze (hard preservation).** From `0a1b8375e5c950d321f898b6d455eb874583c9a4` to the promotion head produced under this delta, the following must be byte-identical, proven by git blob/object hashes or an exact path-set comparison rather than by recollection: `.github/workflows/protected-release.yml`, `tools/desktop/release_provenance.py`, `tests/desktop/test_release_provenance.py`, `tests/desktop/test_protected_release_workflow.py`, `tools/desktop/package_inventory.py`, `tools/desktop/version_drift.py`, `.github/workflows/governance.yml`, `.github/workflows/desktop-shell.yml`, `.github/workflows/native-package-matrix.yml`, `apps/desktop/**`, the canonical Tauri configuration, package manifests and dependency lockfiles, generated-icon sources, every word of `docs/project-brain/contracts/RELEASE-PROVENANCE-V1.md` **except** the single `**Governed by:**` status field authorized above, and every Hive runtime, control-plane, capability and permission file. No formatter may run across technical files; comments, tests and workflow layout are not cleanup targets in this round. If a genuine correctness defect turns out to require a technical edit, this delta does not cover it: STOP and return `CORRECTION_REQUIRED` or `BLOCKED` rather than widening the freeze.

**Authority this delta withholds, in full.** No technical mutation of any kind. No credential read, request, decode, import or provisioning. No GitHub environment, secret, variable, protection rule, ruleset or branch-protection change. No permission scope expansion, and specifically no `id-token: write` reaching a signing job. No signing, notarization, stapling or signature-verification execution. No tag, GitHub Release, asset upload or publication. No `workflow_dispatch` of the promotion path and no job execution undertaken to manufacture additional green boxes. No updater, endpoint, download, install, restart or rollback work, and no `HCODER-DIST-001D` queueing or start. No new product or runtime capability, permission or control-plane path. No merge, and no marking of PR `#86` as Ready. No claim that `HCODER-CP-0026` or `DEC-030` is canonical.

## STOP CONDITION (Delta 004)

STOP if the technical head has moved from `0a1b8375e5c950d321f898b6d455eb874583c9a4`, if PR `#86` was merged, if the reviewed head no longer matches the PR head, if `origin/main` changed in a way that materially intersects this Work Order, or if any HIGH or CRITICAL finding exists against the reviewed head — and never rebase or force-push to hide such drift. STOP before merge, before Ready, before any external provisioning or OIDC grant, before any signing/notarization/publish action, and before any canonical claim for `CP-0026`/`DEC-030`. STOP if the technical freeze cannot be proven, if a required hosted gate is red on the new head, if the candidate head changes after evidence collection, or if any check would need a weakened test or gate to pass. This delta authorizes the **preparation** of a promotion candidate. Approval, promotion and canonical standing remain outside it: they are minted only by an independent exact-head review of the head this round produces, followed by a governed merge and post-validation under `HCODER_CP_0026_EFFECTIVE`.
