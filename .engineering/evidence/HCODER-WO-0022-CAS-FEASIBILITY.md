# HCODER-WO-0022 — Cross-Platform CAS Feasibility Evidence

**Correction:** `HCODER-WO-0022-CR-001`  
**Purpose:** determine whether ordinary Windows/Linux/macOS workspace replacement exposes a documented native primitive that atomically predicates publication on the destination still being the exact previously approved object/state.  
**Result:** no such cross-platform primitive has been established by the reviewed platform contracts. The strict-CAS option remains unproven and MUST remain fail-closed.

## Linux / POSIX finding
Linux `renameat2(..., RENAME_EXCHANGE)` documents atomic exchange of two existing pathnames. `RENAME_NOREPLACE` provides destination nonexistence protection, and cannot be combined with `RENAME_EXCHANGE`. These semantics do not document a predicate such as “exchange/replace only if destination still has expected inode/content identity”. Therefore validate-then-exchange still leaves a late destination substitution window relative to the WO-0022 strict contract.

Primary reference reviewed: Linux `rename(2)` / `renameat2(2)` manual, including `RENAME_EXCHANGE` and `RENAME_NOREPLACE` semantics.

## Windows finding
Microsoft documents `MoveFileEx(..., MOVEFILE_REPLACE_EXISTING)` as replacing an existing destination by name when permissions allow. The API contract does not expose an expected destination file-ID/content predicate.

Microsoft documents `ReplaceFile` as replacing one named file with another, with the resulting file taking the replacement file's file ID. The API contract likewise does not expose an argument that conditions success on the replaced pathname still identifying a previously approved file ID/content state.

Therefore neither documented Win32 surface proves the strict expected-target CAS law. Lower-level NT semantics may still be investigated, but no mutation authority may be granted from an undocumented assumption.

Primary references reviewed: Microsoft Learn `MoveFileEx` and `ReplaceFile`.

## macOS / Darwin finding
Apple documents volume capabilities for `renamex_np`/`renameatx_np`, including `RENAME_EXCL` (warn/fail on pre-existing destination) and `RENAME_SWAP` (swap source and target when both exist). Apple's APFS file-system guidance lists these safe-save rename APIs. The reviewed contract does not document a predicate binding the destination to an expected vnode/file identity or content digest at publication.

Therefore exclusive/swap rename support is not evidence of WO-0022 strict expected-target CAS. Darwin requires its own native adversarial lane under HCODER-PLATFORM-001 and cannot inherit a Linux conclusion.

Primary references reviewed: Apple Foundation volume exclusive/swap rename capability documentation and APFS safe-save API guidance.

## Engineering conclusion
The reviewed public contracts support atomic/exclusive/swap namespace operations, but none establishes the stronger WO-0022 property: a single publication operation that succeeds only if the destination still denotes the exact object/state approved earlier.

Accordingly:
- do not implement strict CAS by composing validation + unconditional rename/replace;
- do not claim cooperative advisory locking protects against arbitrary external writers;
- do not canonicalize DEC-026 under the original strict-CAS wording;
- keep `publish_replace` fail-closed until the Correction Delta selects a corrected contract;
- move permit consumption to the final mutation-ready boundary once that contract is selected.

## Recommended correction direction
For an ordinary developer workspace that must interoperate with editors, Git and external tools, the least architecture-distorting correction candidate is an **explicit bounded-race atomic replacement contract**: exact old identity/content and new bytes remain approval-bound; root/link/reparse protections and live revalidation remain mandatory; publication uses the strongest atomic same-filesystem primitive available; but the specification explicitly acknowledges that an uncooperative external process may race after the last successful revalidation when the OS does not expose expected-destination CAS.

This is a contract correction, not a hidden downgrade. It requires DEC-026/WO/context/test updates, HEDS review, and native race evidence demonstrating both the protected window and the precisely documented residual window before any mutation is enabled.

A content-addressed/versioned authoritative store remains a possible future stronger architecture, but would materially change normal workspace interoperability and should not be silently introduced inside WO-0022.

**STATUS:** FEASIBILITY REVIEW COMPLETE / CONTRACT SELECTION STILL GOVERNED.  
**STOP:** no existing-file mutation until CR-001 is resolved.