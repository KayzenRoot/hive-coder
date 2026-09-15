# HCODER-WO-0016-CR-001 — Root-containment hardening

**Status:** CORRECTION REQUIRED  
**Severity:** HIGH  
**Detected by:** HEDS exact-head review of PR #35  
**Affected implementation head:** `3d57190dcebcf0328ecc1ad9e8652a1b09a58869`

## Finding
The initial evidence-bundle enumeration used `DirEntry::metadata()`. On Unix this follows a symlink before `is_link_or_reparse()` sees the metadata, so a symlinked `.md` entry could be counted as evidence outside the trusted workspace root. In addition, `safe_existing_path()` called `Path::exists()` before `symlink_metadata()`, allowing a dangling symlink to be misclassified as an absent path rather than an unsafe path.

This violates the WO-0016 root-containment invariant. Repository content is untrusted data, and a symlink/reparse transition must never silently broaden or masquerade as trusted workspace evidence.

A secondary contract defect was found in Git HEAD parsing: `ref: refs/heads/` could produce an empty branch string which the strict frontend contract rejects. Native state must fail closed before emitting malformed presentation data.

## Required correction
- use no-follow metadata for evidence directory entries;
- inspect child paths with `symlink_metadata()` before treating NotFound as absence, so dangling links are rejected;
- reject empty local branch references as DEGRADED native state;
- add deterministic regression tests covering symlink evidence escape (Unix where symlink creation is deterministic), dangling-link rejection and malformed empty branch refs;
- rerun exact-head Governance + Desktop Shell and HEDS.

## Authority impact
No new authority is permitted. The correction only tightens read-only validation and fail-closed behavior.

## Stop condition
This finding is RESOLVED only when the corrected exact head passes the required tests/gates and HEDS confirms no remaining HIGH/CRITICAL root-containment issue.
