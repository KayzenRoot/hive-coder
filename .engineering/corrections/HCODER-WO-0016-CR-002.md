# HCODER-WO-0016-CR-002 — Enforce physical bounded-read ceiling

**Status:** RESOLVED  
**Severity:** MEDIUM  
**Detected by:** HEDS exact-head review of PR #35  
**Affected implementation head:** `12a7367c24cf2ac9f6727081f4c40a9eafe5b3f8`  
**Correction commit:** `d42c280ee1e7e5295119f07112de72c5ab9f2ce3`  
**Validated technical head:** `07dda00f7371bcb02158f0c26258b03fa0dec88d`

## Finding
`read_bounded_text()` originally checked file length through metadata and then called an unbounded text read. Concurrent growth after the metadata check could exceed the declared byte ceiling.

## Resolution
- no-follow metadata is revalidated at the bounded text boundary;
- link/reparse and non-regular inputs fail closed;
- reads use a physical `max_bytes + 1` limiter;
- actual over-ceiling bytes are rejected before UTF-8 decoding;
- a deterministic regression proves oversized data rejection and exact-ceiling acceptance.

## Objective validation
Exact technical head `07dda00f7371bcb02158f0c26258b03fa0dec88d` passed Governance run `34996930586`, Desktop Shell run `34996930809`, Windows Rust **11/11 PASS**, and HEDS technical review `5213079423` with unresolved HIGH/CRITICAL findings `0`.

## Residual race boundary
Standard path-based reads cannot make an arbitrarily mutating external workspace transactionally immutable. In WO-0016 this is non-authoritative presentation only: content is not executed and the snapshot cannot mint authority. Future privileged workspace/file operations must use a separately reviewed handle-relative/no-follow capability design rather than inheriting this residual.

## Authority impact
None. The correction only tightens the existing read-only observation boundary.