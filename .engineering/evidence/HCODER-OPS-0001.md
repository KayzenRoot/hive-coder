# HCODER-OPS-0001 — Evidence Bundle (governance candidate)

**Status:** CANDIDATE / exact-head audit and independent HEDS required; no standalone policy promotion yet.  
**Issue:** #95; **PR:** #96 (Draft); **base:** `a9b48bce43fcc2c1a14b70036ed4555f52ba3537`.  
**Pre-evidence source candidate:** `6c117af5027efc53629d125d6ce643925d8aae8b`; this evidence-file addition changes the branch HEAD and invalidates promotion based only on pre-evidence workflow runs. Exact-final-head run IDs must be linked in PR #96/Issue #95 after this file is committed.  
**Risk:** ELEVATED; **Checkpoint Delta:** NONE until acceptance.  
**Decision:** DEC-032 PROPOSED; **accepted checkpoint:** HCODER-CP-0026.

## Exact-source investigation and boundary

At the captured canonical base, the separate `KayzenRoot/hive` context service was not an executable runtime/build or CI prerequisite found in the inspected product repository. The unmerged PR #94 would have added mandatory HIVE-v1.0.3-context/MCP preflight; it was closed unmerged as obsolete. Separate HIVE Issue #166/PR #167, which would have mounted the local Hive Coder checkout and registered/indexed it in HIVE, were also closed unmerged on user instruction. HIVE WO-032/Issue #163 was not modified, canceled or merged; a non-invasive comment records that its local CD14 work must not be used to unblock Hive Coder.

Evidence search using GitHub code search against **base main**:
- `HIVE_PROJECTS_ROOT` and `/workspace/projects`: one match each, both in **historical** `.engineering/context-locks/HCODER-WO-0025.md`, not executable source. Historical proof remains intact.
- `context.build`, `checkpoint.read`, `project.list`, `HIVE v1.0.3`, `http://localhost:8000`, `HIVE_MCP`: zero default-branch code-search matches. This is a targeted source-search observation, not a cryptographic proof of every possible dynamic runtime call.
- Read live `.github/workflows/governance.yml`, `desktop-shell.yml`, `native-package-matrix.yml` and `protected-release.yml`: their required jobs use this repository's own source/tests/foundation locks, Node/Rust toolchains and GitHub workflows; no separate HIVE service mount/REST/MCP preflight was observed.
- Read `foundations/foundations.lock.json`: `HIVE_INTERPRETER_BIN` and `HIVE_CUA_BIN` are **Hive Coder-owned** environment variable names for independent Open Interpreter and Cua executables. These are retained, not dependencies on the external HIVE platform.
- Read `apps/desktop/package.json` and `apps/desktop/src-tauri/Cargo.toml`: `hive-coder` names are product-owned. Stable `hive-*` contract/provenance names and `hive_runtime/` are kept.
- `HCODER-WO-0027` / Draft PR #93 is a separate already-implemented updater candidate requiring independent HEDS. Its product bytes are unchanged by this migration, and it gains no signing/installation/restart authority.

## Scope / actual tracked changes

Only the HCODER-OPS-0001 allowlist is admitted: new Work Order, Context Lock and DEC-032 candidate; current `AGENTS.md` and `README.md`; current Requirements, Scope, Architecture, Deployment, Backlog, Decisions Ledger and Integration Contracts; an append-only forward Context Lock Delta 003 for WO-0027; this Evidence Bundle. Approved checkpoint, old decisions/history/evidence, product Python/Rust/TypeScript, lockfiles, workflow YAML and release/security configuration are frozen. Obsolete PRs closed reversible/unmerged; no branch or repository deleted.

## Required exact-head tests and review

- Governance source-pack/lock/compile/unit tests: required PASS on **final exact PR #96 head**.
- Desktop Shell Windows/Linux/macOS/web, including desktop security and governed build: required PASS on final head.
- Native Package Matrix Windows/Linux/macOS: required PASS on final head.
- Protected Release preflight and protection probe: required PASS on final head. Credential-bearing build-attest/sign/notarize/publish jobs may be legitimately SKIPPED, but do not count as PASS.
- Independent HEDS exact-head review: REQUIRED, NOT YET RECORDED here. Owner self-audit alone is NOT INDEPENDENT.
- No local HIVE uninstall, local test suite, real physical Cua mutation, signing/notarization or production deployment is claimed.

**Final evidence references:** publish exact-final-head workflow run links, check IDs and independent review in the PR/Issue review record once those events exist. Never copy earlier-head PASS to a changed head.

## Residual risk / rollback

Current documentation changes are prospective and only become canonical after governed approval/merge. Older historical documents may continue to mention HIVE; never treat them as current operational instructions. To revert this proposal before merge, close PR #96 without altering main; leave the external-HIVE PRs closed and reopen only on a new explicit user decision. User-controlled uninstall is outside this repository. Do not delete container data, other repositories or product-owned modules.

**Provisional reviewer verdict:** AWAITING_EXACT_HEAD_CI_AND_INDEPENDENT_HEDS. **Checkpoint Delta:** NONE. **STOP:** do not resume feature development or claim the no-HIVE migration canonical before these gates.
