# HCODER-WO-0023 — Executor Brief

**Status:** PREBUILT / DO NOT EXPAND AUTHORITY

## Single mission

Complete `git_stage_paths_v1`: stage exact approved regular-file paths into the local repository index through a Hive-owned governed adapter.

## Read first

1. Issue #68.
2. `.engineering/context-locks/HCODER-WO-0023.md`.
3. `.engineering/prebuilt/HCODER-WO-0023-IMPLEMENTATION-PACK.md`.
4. Canonical Permission & Control Plane and WO-0021/WO-0022 patterns.
5. Current desktop `git-head-read-v1` only for repository observation semantics. Do not turn the desktop shell into a mutation authority.

## Execution order

1. Inspect available dependencies/provenance and choose the safest non-process Git index adapter.
2. If a dedicated `git.write` capability is needed, amend the Context Lock allowed-file set before touching control types/policy tests.
3. Materialize contract/types and failing acceptance/security tests first.
4. Implement repository identity and support-envelope checks.
5. Implement exact request observation/binding.
6. Implement transactional index staging with ownership-safe lock behavior.
7. Consume permit only at final safe mutation boundary.
8. Verify exact staged result and redacted receipt.
9. Add independent Windows/Linux/macOS focused CI evidence.
10. Update Evidence Ledger, run HEDS, correct within the same WO until H/C = 0/0.

## Forbidden shortcuts

- `shell=True` or shell command strings;
- exposing `git` argv to model/tool input;
- `git add` subprocess without an approved correction delta;
- hooks or external filters;
- deleting a pre-existing `index.lock`;
- direct truncate/rewrite of the live index;
- broad `.git` write permission;
- commit/ref/branch/remote mutation;
- network or credentials;
- claiming Linux proof covers macOS or Windows.

## Completion signal

Return only when exact-head native evidence proves the same bounded contract on Windows, Linux and macOS, HEDS reports 0 HIGH / 0 CRITICAL, and no authority beyond exact-path index staging was introduced.