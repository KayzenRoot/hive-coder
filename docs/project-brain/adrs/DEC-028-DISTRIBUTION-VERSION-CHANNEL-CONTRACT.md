# DEC-028 — Distribution Version And Release-Channel Contract

**Status:** PROPOSED / NOT CANONICAL  
**Work Order:** `HCODER-WO-0024`  
**Issue:** `#77`  
**Parent epic:** `HCODER-DIST-001` / Issue `#72`  
**Canonical base:** `HCODER-CP-0023` / `b6aff55ac12c1d31a883878f1d8478d642fbe8e6`  
**Reviews of this proposal:** `5236275753` — CORRECTION_REQUIRED (CRITICAL `0` / HIGH `4` / MEDIUM `2`) at prebuild head `4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`  
**Materialised under:** `HCODER-WO-0024` Context Lock Delta 001

> **State record.** This ADR is a **proposal**. It records a durable law that `HCODER-WO-0024` is establishing and has no canonical standing. It grants no authority, admits no updater, and is not evidence that Hive Coder is installable, signed, auto-updatable or production-distributable. It becomes canonical only through the promotion gate below, and only with an independent review that reports unresolved HIGH/CRITICAL `0/0`.

## Context

Hive Coder's product version lives in three manifests (`apps/desktop/src-tauri/tauri.conf.json`, `apps/desktop/src-tauri/Cargo.toml`, `apps/desktop/package.json`) with no stated precedence and no machine-checked agreement. There is no release-channel concept, no update-lifecycle model and no Hive-owned boundary behind which a future updater could be implemented.

A distribution/update capability cannot be reasoned about safely on top of that: a version identity that three files may independently disagree about, and a "newer" test that is not exact, are exactly the preconditions that make an unsafe upgrade possible. The law therefore has to be fixed before any distribution behaviour exists, and it must be fixed in a form that a later governed slice cannot quietly weaken.

## Decision candidate

**1. One canonical version source.** The shipped product version has exactly one source of truth: `apps/desktop/src-tauri/tauri.conf.json` → `version`. The Tauri application version identifies the shipped artifact and is the value a future updater compares against. The Rust package version and the npm package version are *mirrors*: they must equal the canonical value exactly and must never be edited independently. A tool-enforced drift gate fails the build when a mirror is missing, malformed or divergent.

**2. Strict SemVer 2.0.0 only.** Versions are parsed by one strict parser that fails closed on anything it cannot accept; nothing is trimmed, coerced or partially accepted. Precedence follows SemVer 2.0.0 exactly, including the rule that numeric prerelease identifiers compare by value. Because a SemVer numeric identifier is an arbitrary-precision integer rather than a machine integer, numeric comparison is performed exactly — by digit-length and lexicographic comparison — and never through floating-point conversion, which would collapse distinct identifiers above `2^53` into one value and produce a wrong "newer" answer.

**3. Channel is a shape of version, and version+channel is one identity.** A release channel is one of `stable`, `beta`, `dev` (product label `dev/internal`). `stable` versions carry no prerelease component; `beta` and `dev` versions carry the channel's name as their first prerelease identifier. A version and a channel are a single identity: a pair that is individually valid but mutually incompatible (`0.1.0` on `beta`, `0.1.0-beta.1` on `stable`) is rejected wherever the identity is asserted — service construction, status snapshots and the read model — rather than being half-validated field by field. Channel membership is a *shape* test derived from the same strict parser; it is not a promotion authorisation, and this contract admits no implicit cross-channel promotion or demotion and no silent downgrade.

**4. The update lifecycle is a closed state machine with an authenticity-gated install-ready boundary.** The lifecycle states and the legal transitions are declared exactly; anything else fails closed. `ready` means install-ready: the artifact is present, verified and awaiting only the install call. Entry into `ready` therefore requires an accepted authenticity/integrity proof, and entry into `installing` re-checks it as defence in depth. Cryptographic schemes are admitted by an explicit allowlist that is **empty** in this slice, so no proof can be accepted and the install-ready boundary is unreachable by construction rather than by convention. A status snapshot that claims `ready` or `installing` must carry a proof accepted under the same policy, and is therefore invalid while the allowlist is empty.

**5. Status snapshots are closed, bounded objects.** A status snapshot has an exact key set at the top level, inside its error object and inside every recorded event; unknown keys are refused rather than ignored, unknown states, channels, error codes and transition reasons are refused, events are validated individually against the declarative transition table and a maximum count, and the candidate version is constrained by state (`required`, `forbidden`, or either) and must be a strictly newer version belonging to the same channel. A validated snapshot is *reconstructed* from validated fields; the untrusted input object is never cast and returned, so an unvalidated property cannot ride into product state.

**6. The updater is behind a Hive-owned boundary and is inert.** Product code depends on an `UpdateService` interface, never on an updater plugin, endpoint, HTTP client or installer. The production implementation in this slice reports configuration, evaluates contract law and does nothing else: it exposes no check, download, install, restart, signing, publication or mutation member, and its availability is always reported as unavailable.

## Non-decision

This ADR does not approve, and does not create authority for: a Tauri updater plugin or any update transport; an updater endpoint, HTTP client, download, artifact fetch or metadata fetch; installation, restart or process execution; signing, key access, notarization or store submission; release/tag creation or artifact publication; `bundle.active=true`; any new dependency; any filesystem, Git, shell, Cua, credential or provider authority; and any change to the Permission & Control Plane. It establishes no claim about platforms on which the product is installable, and no release-readiness claim of any kind.

## Security law carried by this proposal

1. Default deny; the contract adds no authority.
2. Update metadata and artifacts are untrusted until a later governed slice proves verification; HTTPS is never authenticity proof.
3. No model, tool or backend may mint release or update authority.
4. Signing material never enters repository, logs, prompts or runtime state.
5. Version, channel and state parsing fail closed on malformed or unknown input.
6. No silent downgrade; no implicit cross-channel promotion or demotion.
7. The install-ready boundary requires an accepted authenticity proof, and no scheme is admitted in this slice.
8. Diagnostic metadata is bounded and redaction-safe; credential-shaped detail is refused.
9. The inert boundary exposes no mutating, transport or installation member.

## Promotion gate

`DEC-028` remains **PROPOSED / NOT CANONICAL**. It may be promoted only when all of the following hold and are recorded against an exact head:

| Condition | Status |
|---|---|
| Contract law implemented and materialised | PENDING independent review of the corrected head |
| Executable contract/security tests prove every property above, including the adversarial cases | PENDING independent review of the corrected head |
| Exact-head Governance and Desktop Shell green on the promotion head | PENDING |
| Independent HEDS with unresolved HIGH/CRITICAL `0/0` | PENDING |
| Governed merge with expected-head protection | PENDING |

Until every condition is met, no promotion claim may be made for this decision, for `HCODER-WO-0024`, or for Hive Coder's distribution or update capability.

## Recorded review history

The first implementation head of `HCODER-WO-0024` (`4710a47e2e099b03baa7fd3e5665bfbc882c4c8d`, gates green) was independently reviewed as `5236275753` and returned `CORRECTION_REQUIRED` with CRITICAL `0` / HIGH `4` / MEDIUM `2`: the authenticity gate sat on the install call instead of the install-ready boundary; version and channel were validated independently rather than as one identity; status snapshots were neither closed nor reconstructed; numeric prerelease precedence used floating-point conversion; the channel contract carried a second, looser version parser; and this ADR was referenced without existing. The corrections are carried in the same Work Order under Context Lock Delta 001. That review history is preserved here rather than being rewritten: the defective head was real, its gates were green, and green gates did not mean the properties held.
