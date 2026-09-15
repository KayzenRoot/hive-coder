# HCODER-WO-0016-CR-002 — Enforce physical bounded-read ceiling

**Status:** CORRECTION REQUIRED  
**Severity:** MEDIUM  
**Detected by:** HEDS exact-head review of PR #35  
**Affected implementation head:** `12a7367c24cf2ac9f6727081f4c40a9eafe5b3f8`

## Finding
`read_bounded_text()` checked file length through metadata and then called `read_to_string()` without an actual read limiter. A concurrently growing workspace file could therefore exceed the declared byte ceiling after the metadata check. The workspace remains read-only from Hive Coder, but the observation itself would no longer satisfy WO-0016's deterministic bounded-read requirement.

## Required correction
- use no-follow metadata immediately before opening the bounded text file;
- reject link/reparse files at this read boundary as defense in depth;
- read through an actual `max_bytes + 1` limiter;
- reject the result if the physical bytes read exceed the declared ceiling;
- decode UTF-8 only after the byte ceiling is enforced;
- add a deterministic regression proving oversized data is rejected;
- rerun exact-head Governance + Desktop Shell and HEDS.

## Residual race note
Path-based standard-library reads cannot make arbitrary concurrently mutating external workspaces transactionally immutable. The corrected boundary prevents static link/reparse admission and enforces a hard byte ceiling even under concurrent growth. Any remaining sub-operation path replacement race is presentation-only in WO-0016: the snapshot cannot mint authority, execute content, expose arbitrary file reads, or mutate the workspace. It must remain documented and may be hardened further with handle-relative/no-follow capability I/O before future privileged workspace operations.

## Authority impact
None. This correction only tightens the existing read-only observation boundary.

## Stop condition
RESOLVED only after exact-head tests/gates prove the physical byte limiter and HEDS finds no remaining HIGH/CRITICAL issue in the WO-0016 read boundary.
