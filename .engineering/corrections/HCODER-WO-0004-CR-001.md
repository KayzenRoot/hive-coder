# Correction Delta — HCODER-WO-0004-CR-001

## Finding
**HIGH · EXPIRY / CLOCK SAFETY.** The first candidate used wall-clock time for session, approval and permit expiry. A host wall-clock rollback could extend an authorization lifetime beyond its intended security TTL.

## Correction
Security TTLs now use a dedicated monotonic clock (`time.monotonic` by default). Audit timestamps use a separate wall clock. The signed token record is cross-checked against every signed security claim, token input length is bounded before decode, strict base64 validation is used, and the HMAC key floor is raised to 256 bits.

## Regression proof required
Tests must prove wall-clock rollback cannot extend an approval, short keys are rejected, oversized/tampered tokens fail closed, and Linux + Windows exact-head suites pass.
