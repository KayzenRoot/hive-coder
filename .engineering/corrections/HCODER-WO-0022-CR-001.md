# Correction Delta — HCODER-WO-0022-CR-001

**MODE:** CORRECTION  
**SEVERITY:** HIGH — required publication guarantee is not yet proven implementable across first-class platforms  
**SAME WO:** required — HCODER-WO-0022 / Issue #61  
**SOURCE HEAD:** `3de2f66196c2b10457b0674e3bc78a37e803c321`  
**ACCEPTED/FROZEN:** CP-0021 create-only `write_file_v1`; Permission & Control Plane law; HIGH_ASSURANCE approval/permit rules; root/link/reparse/.git protections; request binding of exact approved old state and exact new bytes; no-clobber intent; all authority exclusions.

## Finding
`HCODER-WO-0022-CR-001` — the initial WO-0022 contract required the final publication operation itself to behave as compare-and-swap against the exact approved destination identity/state. The prebuilt feasibility analysis has not established a portable native namespace primitive on Windows, Linux and macOS that both publishes ordinary workspace-file replacement atomically and predicates that publication on the destination still naming the approved object.

Ordinary atomic replacement is not equivalent to expected-target CAS. A last-moment validation followed by an unconditional rename/replace retains a late substitution window. Detecting substitution after publication is also insufficient because the namespace has already mutated and rollback can race.

## Security consequence
Implementing `os.replace`, ordinary `rename`/`renameat`, `renameat2(RENAME_EXCHANGE)`, `MoveFileEx`, `ReplaceFile`, truncate-and-rewrite, or equivalent path-only publication and labeling it CAS would create a false security claim. That shortcut is forbidden.

A cooperative Hive-only lease by itself also does not prove the original guarantee against an uncooperative external process. Advisory locking may serialize Hive actors but must not be represented as preventing arbitrary external mutation unless the platform/filesystem supplies enforceable semantics and the native adversarial tests prove them.

## Correction decision
The original strict expected-target publication law is **SUSPENDED, NOT WEAKENED** pending proof. `replace_file_v1` remains fail-closed and MUST NOT gain mutation authority from this correction record alone.

Before implementation may resume, WO-0022 must select and prove exactly one corrected publication contract:

1. **Strict native CAS contract:** identify a supported platform/filesystem primitive whose publication operation itself objectively conditions success on the approved destination identity/state; prove it with adversarial late-race tests on every supported platform; or
2. **Explicit bounded-race contract:** revise DEC-026 and the Work Order to state the precise residual external-process race that cannot be eliminated for ordinary workspace files, preserve atomic publication and prepublication identity/content revalidation, and treat the residual as an explicit product/security assumption. This path requires governed approval and must never be described as strict CAS; or
3. **Controlled versioned-store contract:** change the mutation architecture so the authoritative object is version/content addressed and publication occurs through a separately controlled pointer/version primitive with objectively testable CAS semantics. This is a larger architecture change and requires explicit scope review before adoption.

No option is selected merely by this Correction Delta. Selection requires source-backed feasibility evidence and an updated DEC-026 candidate.

## Required platform proof
- Linux/POSIX: prove the exact semantics of the selected publication primitive and run real late destination-substitution/content-change races.
- Windows/NTFS: prove handle/reparse/identity semantics and real late replacement/junction races.
- macOS/Darwin: dedicated native proof lane under HCODER-PLATFORM-001 / Issue #63; do not infer Darwin guarantees from Linux/POSIX behavior.
- Any filesystem-specific limitation must be represented in the support contract and surfaced as fail-closed capability availability, not silently downgraded.

## Permit ordering correction
A valid single-use permit MUST NOT be consumed merely to reach an intentionally unimplemented publication seam. Permit consumption must move to the last safe point at which the selected publication mechanism is ready to mutate, while cancellation/session/expected-state checks remain effective through that boundary. Exact ordering must be proven by tests before promotion.

## Required source updates before resolution
- `.engineering/work-orders/HCODER-WO-0022.md`
- `.engineering/context-locks/HCODER-WO-0022.md` if assumptions change
- `.engineering/prebuilt/HCODER-WO-0022-IMPLEMENTATION-PACK.md`
- `.engineering/prebuilt/HCODER-WO-0022-EXECUTOR-BRIEF.md`
- `docs/project-brain/adrs/DEC-026-GOVERNED-EXISTING-FILE-REPLACEMENT.md`
- `.engineering/evidence/HCODER-WO-0022.md`
- platform implementation/tests only after a corrected contract is selected

## Closure evidence required
- source-backed feasibility record for the selected contract;
- adversarial native race tests on supported platforms;
- permit ordering/replay/cancellation evidence;
- focused + full regression suites;
- exact-head Governance and Desktop Shell green;
- HEDS review with unresolved HIGH/CRITICAL = 0.

**STATUS:** OPEN / CORRECTION REQUIRED.  
**STOP:** do not merge PR #62, canonicalize DEC-026, mark WO-0022 complete, or enable existing-file mutation until this Correction Delta is resolved with objective evidence.