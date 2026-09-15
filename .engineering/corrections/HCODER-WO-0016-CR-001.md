# HCODER-WO-0016-CR-001 — Root-containment hardening

**Status:** RESOLVED  
**Severity:** HIGH  
**Detected by:** HEDS exact-head review of PR #35  
**Affected implementation head:** `3d57190dcebcf0328ecc1ad9e8652a1b09a58869`  
**Correction commit:** `edea51a6d5fae051be43754179f33f9f1e4a316c`  
**Validated technical head:** `07dda00f7371bcb02158f0c26258b03fa0dec88d`

## Finding
The initial evidence-bundle enumeration used `DirEntry::metadata()`, which can follow symlinks on Unix before link rejection. `safe_existing_path()` also used `exists()` before no-follow metadata, allowing a dangling symlink to look absent. An empty `ref: refs/heads/` could also produce malformed native Git presentation state.

## Resolution
- evidence entries use `fs::symlink_metadata(item.path())` and link/reparse entries are degraded/skipped rather than counted;
- child-path admission uses no-follow metadata and distinguishes true NotFound from unsafe dangling links;
- empty local branch references fail closed as DEGRADED;
- deterministic regressions cover malformed empty branch refs and, on Unix where deterministic symlink creation is available, dangling-link and evidence-symlink escape cases.

## Objective validation
Exact technical head `07dda00f7371bcb02158f0c26258b03fa0dec88d` passed Governance run `34996930586` and Desktop Shell run `34996930809`. HEDS review `5213079423` re-audited the correction and reports unresolved HIGH/CRITICAL findings `0`.

## Authority impact
None. The correction only tightens the approved read-only validation boundary.