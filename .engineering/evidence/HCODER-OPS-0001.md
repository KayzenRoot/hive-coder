# HCODER-OPS-0001 — Evidence Bundle (governance candidate)

**Status:** CANDIDATE / exact-head DEC-033 owner semantic self-audit (NOT_INDEPENDENT) and same-head CI required; no canonical promotion until governed merge/postvalidation.  
**Issue:** #95; **PR:** #96 (Ready for review); **base:** `a9b48bce43fcc2c1a14b70036ed4555f52ba3537`.  
**Pre-evidence source candidate:** `6c117af5027efc53629d125d6ce643925d8aae8b`; this evidence-file addition changes the branch HEAD and invalidates promotion based only on pre-evidence workflow runs. Exact-final-head run IDs must be linked in PR #96/Issue #95 after this file is committed.  
**Risk:** ELEVATED; **Checkpoint Delta:** NONE until acceptance.  
**Decisions:** DEC-032 and DEC-033 PROPOSED; **accepted checkpoint:** HCODER-CP-0026.

## Exact-source investigation and boundary

At the captured canonical base, the separate `KayzenRoot/hive` context service was not an executable runtime/build or CI prerequisite found in the inspected product repository. The unmerged PR #94 would have added mandatory HIVE-v1.0.3-context/MCP preflight; it was closed unmerged as obsolete. Separate HIVE Issue #166/PR #167, which would have mounted the local Hive Coder checkout and registered/indexed it in HIVE, were also closed unmerged on user instruction. HIVE WO-032/Issue #163 was not modified, canceled or merged; a non-invasive comment records that its local CD14 work must not be used to unblock Hive Coder.

Evidence search using GitHub code search against **base main**:
- `HIVE_PROJECTS_ROOT` and `/workspace/projects`: one match each, both in **historical** `.engineering/context-locks/HCODER-WO-0025.md`, not executable source. Historical proof remains intact.
- `context.build`, `checkpoint.read`, `project.list`, `HIVE v1.0.3`, `http://localhost:8000`, `HIVE_MCP`: zero default-branch code-search matches. This is a targeted source-search observation, not a cryptographic proof of every possible dynamic runtime call.
- Read live `.github/workflows/governance.yml`, `desktop-shell.yml`, `native-package-matrix.yml` and `protected-release.yml`: their required jobs use this repository's own source/tests/foundation locks, Node/Rust toolchains and GitHub workflows; no separate HIVE service mount/REST/MCP preflight was observed.
- Read `foundations/foundations.lock.json`: `HIVE_INTERPRETER_BIN` and `HIVE_CUA_BIN` are **Hive Coder-owned** environment variable names for independent Open Interpreter and Cua executables. These are retained, not dependencies on the external HIVE platform.
- Read `apps/desktop/package.json` and `apps/desktop/src-tauri/Cargo.toml`: `hive-coder` names are product-owned. Stable `hive-*` contract/provenance names and `hive_runtime/` are kept.
- `HCODER-WO-0027` / Draft PR #93 is a separate unmerged updater candidate requiring exact-head semantic HEDS; after DEC-033, the owner may perform this as NOT_INDEPENDENT with extra HIGH_ASSURANCE risk/negative-test evidence. Its product bytes are unchanged by this migration, and it gains no signing/installation/restart authority.

## Scope / actual tracked changes

The scope comprises 18 governance/documentation files: the Work Order, Context Lock and Evidence Bundle; DEC-032 and DEC-033 ADRs; AGENTS and README; Requirements, Scope, Architecture, Deployment, Backlog, Decisions Ledger and Integration Contracts; additional Scope Correction Delta 001 paths `.engineering/gef/GEF-REVIEW-PROTOCOL.md`, `.engineering/gef/GEF-EXECUTION-PROTOCOL.md` and `docs/project-brain/09-DEFINITION-OF-DONE.md`; plus append-only WO-0027 Context Lock Deltas 003 and 004. No other tracked paths are admitted. Approved checkpoint, old decisions/history/evidence, product Python/Rust/TypeScript, lockfiles, workflow YAML and release/security configuration are frozen. Obsolete PRs closed reversible/unmerged; no branch or repository deleted.

## Required exact-head tests and review

- Governance source-pack/lock/compile/unit tests: required PASS on **final exact PR #96 head**.
- Desktop Shell Windows/Linux/macOS/web, including desktop security and governed build: required PASS on final head.
- Native Package Matrix Windows/Linux/macOS: required PASS on final head.
- Protected Release preflight and protection probe: required PASS on final head. Credential-bearing build-attest/sign/notarize/publish jobs may be legitimately SKIPPED, but do not count as PASS.
- DEC-033 exact-head OWNER_SELF_AUDIT / NOT_INDEPENDENT: required semantic HEDS-role audit for this operational PR, with zero unresolved HIGH/CRITICAL. The originally proposed second-human HEDS requirement is superseded by Scope Correction Delta 001.
- No local HIVE uninstall, local test suite, real physical Cua mutation, signing/notarization or production deployment is claimed.

**Final evidence references:** publish exact-final-head workflow run links, check IDs and owner self-audit labeled NOT_INDEPENDENT in durable PR/Issue comments after the final evidence commit. Earlier-head audits and CI cannot carry across a new head. Never copy earlier-head PASS to a changed head.

## Residual risk / rollback

Current documentation changes are prospective and only become canonical after governed approval/merge. Older historical documents may continue to mention HIVE; never treat them as current operational instructions. To revert this proposal before merge, close PR #96 without altering main; leave the external-HIVE PRs closed and reopen only on a new explicit user decision. User-controlled uninstall is outside this repository. Do not delete container data, other repositories or product-owned modules.

**Provisional reviewer verdict (superseded original snapshot):** AWAITING_EXACT_HEAD_CI_AND_OWNER_SELF_AUDIT / NOT_INDEPENDENT. **Checkpoint Delta:** NONE. **STOP:** do not resume feature development or claim the no-HIVE migration canonical before these gates.

## Correction evidence — CodeRabbit finding at PR #96/a33f30c (2026-09-29)

**Finding:** automatic review correctly noted Criterion 2 was supported by static search of original `main`, not a path-by-path runtime/import evidence capsule on the then-exact PR candidate. The review was a valid scope/evidence concern; it did not demonstrate a live external-HIVE dependency or a security defect. The following bounded proof used the actual branch source and verified that all executable/manifest/workflow paths listed below remained byte-identical to the locked base `a9b48bce43fcc2c1a14b70036ed4555f52ba3537` in the then-reviewed candidate `a33f30c626f840d8850901d66bbf718822e8eb18`. A fresh diff/HEAD and CI check must be made after this Evidence Bundle is changed. Do not claim coverage beyond the audited sites.

### Direct import/process graph and concrete Git blobs

- `hive_runtime/interpreter.py` blob `18f52295428ededc524fb1096144c45613cbf6ff` imports internal `.foundation_lock` -> `.preflight` -> `.process` and `.jsonrpc`. `InterpreterAdapter.from_binary()` uses independent pinned `openInterpreter` (ACP) and production `ManagedStdioProcess`; no separate HIVE project-registry or context-service client found in the inspected path.
- `hive_runtime/cua.py` blob `5cb3ed4e59432318d4e3e77bd1ebc037474206e2` imports the same local foundation/preflight/process/JSON-RPC components. `CuaAdapter.from_binary()` starts pinned `cuaDriver` with the separate upstream modern MCP protocol. This *is not* the removable external HIVE context MCP.
- `hive_runtime/foundation_lock.py` blob `3cc4fc7570c151c4b05bf524b825e963b21e983a` only reads `foundations/foundations.lock.json` and selects an exact pinned foundation version. `hive_runtime/preflight.py` blob `68db29b8582628ef5997736a710d1086bd0fba72` imports internal `.errors` and `.process.safe_child_environment`, and line 25 calls bounded `subprocess.run([binary, *version_args], shell=False)` only to verify the selected independent foundation binary.
- `hive_runtime/process.py` blob `75875ae9a07ada8a5bb692e6dfa9278ba3dcfcdd` imports stdlib `subprocess/threading/os` and internal `.errors`; lines 91-114 create a bounded `ManagedStdioProcess` from the caller-supplied adapter `ProcessSpec.command`, least-privilege child environment and `shell=False`. A separately supplied malicious/ad hoc command is outside this limited foundation-call-site audit; the inspected built-in adapters select the pinned independent foundations, not HIVE context-service binaries.
- `apps/desktop/src-tauri/src/runtime_status_supervisor.rs` blob `2f60e032039ddfbdad3adcbe3e5025022a9dc172` at lines 33-49 validates a fixed product-owned status-sidecar as sibling of the desktop executable, rejects link/reparse identities; lines 59-68 spawn exactly that `hive-runtime-status-sidecar` in `--stdio-status-v1` mode with `env_clear()`. That internal sidecar/IPC is **not** the separate installed HIVE server.
- `foundations/foundations.lock.json` blob `ab5350d47563a500e92c149434b36006b98091e2` specifies only pinned Open Interpreter `0.0.43` ACP and Cua Driver `0.28.1` MCP, with product-owned `HIVE_INTERPRETER_BIN` and `HIVE_CUA_BIN` variables. No `KayzenRoot/hive` package/service/URL/mount is defined in that inspected file.
- Active exact-base workflow blobs inspected and identical across the then-reviewed candidate: Governance `1f823d7672f95217ca144a4fe8c8d96f318b63d4`, Desktop Shell `7eb76979345c554dacc1b3a5fac0a26a0019367e`, Native Package Matrix `118bbbe8f453dd130852d97a40b2e0781ab71d92`, Protected Release `12902a49a344a53350df926da382a6f85629a74c`. These use the repository checkout/toolchains/foundation locks and GitHub APIs, without the separate HIVE runtime/REST/MCP/container/index. Protected Release's `https://api.github.com/repos` endpoint is GitHub environment-protection inspection, not an external HIVE service.

**Bounded search classification:** on original base `main`, `HIVE_PROJECTS_ROOT` and `/workspace/projects` appeared only inside historical `.engineering/context-locks/HCODER-WO-0025.md` (intentionally preserved). Searches for `context.build`, `checkpoint.read`, `project.list`, `HIVE v1.0.3`, `http://localhost:8000` and `HIVE_MCP` returned no default-branch matches. The PR change list for `a33f30c...` had 14 governance/docs paths and **zero executable, manifest or workflow changes**, so the inspected base implementation blobs also apply to that exact candidate. Those search observations are bounded by what GitHub indexed; they are not proof that no custom runtime caller could ever invoke an arbitrary executable. If a future Work Order introduces such a client, it needs its own admission.

**Unknowns retained:** no inspection of the owner's actual local Windows process list, untracked files, global Codex MCP configuration or installed HIVE Docker images; no exhaustive dynamic-import/network graph or production-sidecar/physical Cua E2E run; no claim that HIVE has been uninstalled from Windows. The source-audit criterion is met only for the specified tracked paths and recorded actual import/process launch chains, not for arbitrary externally injected user code.

## Scope Correction Delta 001 proof — owner-only GitHub acceptance

The 2026-09-29 user directive removes the requirement for any collaborator or independent second account. Current GitHub ruleset `hive-main-governed` #23768014 explicitly has `required_approving_review_count=0`, no specific reviewers or required CODEOWNERS review; it still requires all 13 exact-head status checks, base freshness, a PR, closed blocking review threads and squash-only linear history. The optional `kayzenweb3` request was removed from this PR. Independent bot Greptile only posted trial-credit exhaustion, not a review. CodeRabbit's specific source-audit finding is handled here as a real finding, and its actual thread must be resolved only after current source/diff reinspection. No external collaborator or paid bot is an admission requirement.

Proposed DEC-033 replaces the prospective second-human reviewer identity gate with a substantive owner-recorded exact-head semantic audit, always labeled `OWNER_SELF_AUDIT / NOT_INDEPENDENT`, and preserves all objective gates. HIGH_ASSURANCE retains explicit owner risk acceptance and negative/challenge proof. The prior independently reviewed CP-0020..CP-0026 records remain historically intact. **This evidence file cannot embed its own final Git SHA or its subsequent CI execution IDs without changing its own SHA**; therefore the exact-final-head CI and owner review receipts must be published as durable linked comments on PR #96 and Issue #95 after the final docs commit and checked again immediately before merge. A new head invalidates previous CI and review receipts.

**Provisional STOP state after same-PR corrections:** CORRECTION_APPLIED / AWAITING_NEW_EXACT_HEAD_CI_AND_OWNER_SELF_AUDIT (NOT_INDEPENDENT). Checkpoint Delta NONE until governed merge and fresh exact-main postvalidation.
