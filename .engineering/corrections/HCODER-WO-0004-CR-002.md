# Correction Delta — HCODER-WO-0004-CR-002

## Finding
**HIGH · APPROVAL DISPLAY / MUTABLE REQUEST RACE.** `ActionRequest.arguments` and the first `ApprovalChallenge` display mappings could be mutated by caller-owned objects. That created a confused-deputy risk where the content presented for approval could drift from the content later authorized.

## Correction
Every security operation now creates one canonical request snapshot and derives the decision fingerprint from that snapshot. Approval target/display data are stored internally as canonical JSON strings and exposed only as fresh copies. The challenge binds the digest of the actual canonical arguments. Mutating original request arguments after approval changes the next fingerprint and causes authorization rejection.

## Regression proof required
Tests must mutate both returned challenge mappings and caller-owned request arguments and prove the stored challenge remains unchanged and the stale approval cannot authorize the modified request.
