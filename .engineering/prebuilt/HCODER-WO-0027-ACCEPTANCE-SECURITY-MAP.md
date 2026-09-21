# HCODER-WO-0027 — Acceptance & Security Map

| ID | Property | Proof required | Failure |
|---|---|---|---|
| U1 | Rust-only updater | Cargo dep present; no JS updater dep; no updater capability permission | HIGH |
| U2 | Single invoke bridge | all invokes in desktopBridge; exact allowlist | HIGH |
| U3 | Argument-free update commands | source/static test proves no caller payload | HIGH |
| U4 | No placeholder trust | missing key/endpoint => unavailable before request | HIGH |
| U5 | HTTPS only | parser/config test rejects non-HTTPS and dangerous flags | HIGH |
| U6 | Signed-version binding | exact upstream feature enabled; missing/mismatch negative tests | CRITICAL |
| U7 | No downgrade | allowDowngrades false; no weakening comparator; DEC-028 tests | CRITICAL |
| U8 | Same channel | cross-channel candidate refused | HIGH |
| U9 | Strictly newer | equal/older refused | HIGH |
| U10 | Signature before ready | only verified download bytes can be hashed/admitted | CRITICAL |
| U11 | Candidate identity binding | substitution between check/download refused | HIGH |
| U12 | Verified bytes vault | one trusted in-memory candidate; no arbitrary file staging | HIGH |
| U13 | Proof non-authority | frontend proof cannot authorize any mutation/install | HIGH |
| U14 | No install/restart invoke | command/service allowlists prove absence | CRITICAL |
| U15 | No generic network surface | no caller headers/proxy/url/key; no generic HTTP plugin | HIGH |
| U16 | Package law preserved | bundle.active false; Native Package Matrix green | HIGH |
| U17 | Existing desktop authority preserved | capability permissions []; security gate green | HIGH |
| U18 | Error redaction | bounded codes, no response body/URL/signature/credentials echoed | MEDIUM |
| U19 | Platform truth | no uniform restart/install success claim | MEDIUM |
| U20 | Exact-head evidence | four required workflows green on one SHA | HIGH |

## Negative corpus
At minimum:
- missing config;
- empty key;
- empty endpoints;
- http endpoint;
- malformed endpoint;
- equal version;
- older version;
- stable↔beta/dev mismatch;
- malformed version;
- missing signed version;
- signed-version mismatch;
- invalid signature/download error;
- stale candidate;
- candidate replacement;
- duplicate download;
- direct plugin import;
- updater capability permission;
- extra invoke site;
- caller endpoint/key/header/proxy/target;
- install/restart command introduction.

No finding is closed by prose alone.