# Release Provenance Contract v1

**Contract ID:** `hive-release-provenance-v1`  
**Owner:** Hive Coder  
**Governed by:** `HCODER-WO-0026` / `DEC-030` (PROPOSED / NOT CANONICAL)  
**Status:** CANDIDATE  
**Verifier:** `tools/desktop/release_provenance.py`  
**Descends from:** `hive-package-inventory-v1` (`HCODER-WO-0025` / `DEC-029`, canonical)

## Purpose

Bind one platform's generated native packages to the exact source, version, channel and packaging evidence they came from, and record — as separate, separately-gated claims — whether they were publisher-signed, platform-trusted, provenance-attested and published. This contract is an evidence document and an admission gate. It is not a signing service, not a credential store, and not a release.

The document is **deterministic and timestamp-free**: the same facts always serialize to the same bytes, and no wall-clock field exists. Mutable timing stays external, in the signature timestamp authority and the transparency log.

## Guarantee separation

Five claims — plus the upstream binding that anchors them — never interchangeable:

| Claim | Field | Satisfied by | Cannot be substituted by |
| --- | --- | --- | --- |
| Artifact integrity | `packages[].unsignedDigest` / `releasedDigest` | `hive-package-inventory-v1` digest recomputed from bytes | anything |
| Upstream binding | `inventory.digest` | SHA-256 of the canonical serialization of the exact inventory document | a copy with edited fields |
| Build provenance | `attestation` | verified GitHub artifact attestation bundle | publisher signing, integrity |
| Publisher authenticity | `packages[].signing` | OS-level signature by a publisher identity | **attestation**, digests |
| Platform trust | `packages[].notarization` | notarization + stapling + verification | signing alone |
| Publication | `publication` | an actually completed protected publication | intent, a workflow definition |

A workflow or reviewer may not read one row as another. In particular `attestation.status = verified` never satisfies a publisher-signing requirement, and no digest ever means publisher authenticity.

## Document shape

Exact top-level keys, in this order:

```text
schemaVersion, sourceSha, canonicalVersion, releaseChannel, platform,
architecture, inventory, attestation, packages, publication
```

Presence **and order** are both enforced, matching `hive-package-inventory-v1`. No JSON Schema language is used and no new dependency is admitted: the governed Python dependency lock admits only `dulwich`, so closure is enforced in code.

- `schemaVersion` — literal `hive-release-provenance-v1`;
- `sourceSha` — `^[0-9a-f]{40}$`, and equal to the inventory's `sourceSha`;
- `canonicalVersion` — the canonical product version per `hive-version-v1`, equal to the inventory's, and channel-coherent (below);
- `releaseChannel` — closed enum `stable` | `beta` | `dev`;
- `platform` — closed enum `windows` | `macos` | `linux`;
- `architecture` — `^[A-Za-z0-9._-]{1,64}$`, equal to the inventory's;
- `inventory` — the upstream binding object;
- `attestation` — the provenance block;
- `packages` — 1..8 entries, one per package type;
- `publication` — the publication block.

## Upstream binding

Exact keys:

```text
digest, packageCount
```

`digest` is the lowercase SHA-256 of the exact bytes produced by canonical serialization of the upstream `hive-package-inventory-v1` document. `packageCount` equals that document's entry count. Because the binding is over the serialized bytes, editing any inventory field — including a package digest — changes the binding instead of surviving it.

## Package entry shape

Exact keys:

```text
packageType, relativePath, byteSize, unsignedDigest, releasedDigest, signing, notarization
```

- `packageType` — closed enum inherited from `hive-package-inventory-v1` (`msi`, `nsis`, `app`, `dmg`, `deb`, `appimage`), and it must be a type the declared `platform` produces. One entry per package type: a repeated `packageType` is refused before any comparison, so no key collapse can hide a duplicate;
- `relativePath` — non-empty, POSIX-separated, at most 512 characters, relative to the bounded package root; absolute, drive-letter, UNC, rooted, backslash-separated and `..`-traversing paths fail closed;
- `byteSize` — positive integer, the **released** size;
- `unsignedDigest`, `releasedDigest` — `^[0-9a-f]{64}$`.

The unsigned/released pair exists so that a byte change is always accounted for:

- if `signing.status` is `unavailable` or `unsigned-candidate`, then `releasedDigest` **must equal** `unsignedDigest` and `byteSize` **must equal** the upstream inventory's recorded size — bytes that changed with no signing account are tampering, not an unsigned release;
- if `signing.status` is `signed` or `verified`, a difference is expected and `byteSize` is not pinned to the upstream size, but the entry still has to name both digests.

## Signing state machine

Exact keys:

```text
status, verification, identity
```

`status` is a closed ladder:

```text
unavailable -> unsigned-candidate -> signed -> verified
```

- `unavailable` — the credential class does not exist for this build; not a failure and not a success;
- `unsigned-candidate` — bytes exist and are deliberately unsigned (the `HCODER-CP-0025` state);
- `signed` — a signing operation completed, independently unverified;
- `verified` — a signature was verified against a publisher identity.

`verification` is the closed enum `none` | `failed` | `passed`. `identity` is `null` or an object with exactly:

```text
certificateFingerprint, certificateSubject, timestampAuthority
```

Rules: `signed` and `verified` require a non-null `identity` whose `certificateFingerprint` matches `^[0-9a-f]{40,64}$`; `unavailable` and `unsigned-candidate` require `identity = null` and `verification = none`; `verification = failed` is only legal with `status = signed` and is terminal for the document — a later document may neither advance past it nor rewind it to `none`, because an attempted-and-failed verification is a fact about this release rather than a scratch field; `verified` requires `verification = passed`. Private key material, certificate files and passwords are structurally unrepresentable in this block.

## Notarization state machine

Exact keys:

```text
status, verification, reason
```

`status` is the closed ladder `not-applicable -> pending -> stapled -> verified`, plus the terminal `failed`.

- `not-applicable` requires `reason` to be exactly one of `platform-windows`, `platform-linux`, `unsigned-artifact`; other states require `reason` to be the empty string;
- `not-applicable` requires `verification = none`;
- `stapled` requires `packages[].signing.status` to be `signed` or `verified` — you cannot staple a ticket to an unsigned artifact;
- `verified` requires `verification = passed`;
- `failed` is terminal for that document: a later document may not advance it, and a notarization retried after a failure is a new release document rather than a repair of this record. Re-issuing the same failed verdict with the same fields changes nothing;
- notarization is only meaningful on `platform = macos`; a non-macos entry may only hold `not-applicable`.

This is where the honest asymmetry of the matrix is recorded: Windows has no notarization concept, and Linux has no platform-trust claim at all, so a Linux entry can never enter a publisher-authenticity or platform-trust state.

## Attestation block

Exact keys:

```text
status, verification, signerWorkflow, sourceRef, runId, bundleDigest
```

`status` is the closed ladder `unavailable -> generated -> verified`.

- `signerWorkflow` — empty, or `owner/repo@refs/heads/<branch>` / `owner/repo@refs/tags/<tag>`;
- `sourceRef` — empty, or `refs/...` with at most 255 characters;
- `runId` — `0` when absent, otherwise a positive integer;
- `bundleDigest` — empty, or `^[0-9a-f]{64}$`.

`generated` requires `signerWorkflow`, `sourceRef`, a non-zero `runId` and a `bundleDigest`, and must not carry `verification = passed` — an achieved verification is the `verified` state, not an attribute of a lower one. It may keep `verification = none`, and `failed` is legal here so a failed verification stays visible. `verified` additionally requires `verification = passed`. **Generating an attestation is not a security success; only verification is.** `unavailable` requires every other field empty or `0`.

## Publication block

Exact keys:

```text
status, releaseId, releaseTag, assetSetDigest
```

`status` is the closed ladder `not-published -> staged -> published`.

- `not-published` requires `releaseId = 0`, `releaseTag = ""` and `assetSetDigest = ""` — this is the state of every document produced by `HCODER-WO-0026`;
- `staged` requires a non-zero `releaseId` and a `releaseTag` matching `^[A-Za-z0-9._/-]{1,128}$`;
- `published` additionally requires `assetSetDigest` to equal the SHA-256 of the canonical serialization of the document's own `packages` list.

A publication claim whose artifact set does not hash to the recorded identity is a fabricated claim and fails closed.

`published` records that a release act completed and pins which bytes were released. It deliberately does **not** restate signing or attestation as a precondition, because that substitution is exactly what the guarantee-separation table forbids: a Linux release can be honestly `published` while holding `unsigned-candidate` signing, since Linux has no enforceable publisher-trust model. Whether a release was *admissible* is the gate's decision below, and the protected workflow runs the gate before it may publish.

## Publication gate

`--gate` answers one question — may these artifacts be published? — by reading each guarantee separately. It first revalidates the document and its upstream binding, then returns the precise list of unmet claims:

| Reason | Fires when |
| --- | --- |
| `build-provenance-attestation-unverified` | `attestation` is not `verified` with a `passed` result |
| `publisher-signing-unverified:<packageType>` | that package's signing is not `verified` with a `passed` result, on a platform with a publisher-trust model |
| `platform-trust-unverified:<packageType>` | on macOS, that package's notarization is not `verified` with a `passed` result |
| `already-published-immutable` | the document already claims publication |

An empty list is the only admissible answer. A verified attestation never clears a publisher-signing requirement, and macOS requires platform trust in addition to signing. For the platforms listed in `NO_PUBLISHER_TRUST_PLATFORMS` — Linux today — the signing and platform-trust requirements are skipped rather than faked: the honest Linux admission is build provenance plus artifact integrity, and the gate can never demand a signature that the platform's install path would not consult.

## Environment protection admission

A release workflow may name a deployment environment, and naming one proves nothing: a platform that creates the environment on first reference turns a typo into an unprotected release path. `--environment-protection` therefore judges a *record fetched from the platform* rather than a string in a YAML file:

```text
--environment-protection --environment-record <fetched.json> [--environment-name <expected>]
```

The record is foreign-authored, so unknown keys are tolerated while every judged field must be present and exact: `name`, `can_admins_bypass`, `protection_rules`. A record missing a judged field is refused, never assumed protected. The verdict is `PROTECTED` only when `protection_rules` carries a `required_reviewers` rule holding at least one reviewer entry and `prevent_self_review` set to `true`, and `can_admins_bypass` is `false`; each unmet condition is reported as its own `UNPROVEN_BECAUSE=` line:

| Reason | Fires when |
| --- | --- |
| `protection-rules-absent` | the record carries no protection rules at all |
| `required-reviewers-rule-absent` | no `required_reviewers` rule is present |
| `self-review-permitted` | a reviewer gate exists but allows the author to approve their own release |
| `required-reviewer-count-below-one` | the reviewer gate names nobody |
| `admins-can-bypass-protection` | `can_admins_bypass` is `true`, so the gate is advisory |

A record this tool cannot parse or judge prints `RELEASE_PROTECTION=UNPROVEN` and exits non-zero: an unjudgeable record is an unproven gate, and the tool never reports `RELEASE_PROVENANCE=INVALID` for input that is not a provenance document. Exit status 2 with `UNPROTECTED` and with `UNPROVEN` are the same operational answer — the release path is not gated — and a workflow must treat both as refusal.

## Channel coherence

`releaseChannel` and `canonicalVersion` are one identity, under the law already canonicalized by `hive-release-channel-v1`:

- `stable` admits only a version with **no** prerelease component;
- `beta` admits only a version whose **first** prerelease identifier is exactly `beta`;
- `dev` admits only a version whose first prerelease identifier is exactly `dev`;
- matching is case-sensitive, so `1.0.0-BETA.1` belongs to no channel;
- the version itself must satisfy `hive-version-v1` as enforced by `tools/desktop/version_drift.py`.

The Python rule and the TypeScript rule must agree; they are the same decision expressed twice, not two dialects.

## Canonical serialization

`json.dumps` with two-space indent, declared key order preserved (`sort_keys=False`), ASCII escaping, and a single trailing newline — identical to `hive-package-inventory-v1`. Entries are ordered by `(packageType, relativePath)`. Byte-stability is the point: two producers that agree on the facts agree on the bytes.

## Transition law

A later document may advance the same release but never silently rewrite it. Given a prior and a later document:

1. `sourceSha`, `canonicalVersion`, `releaseChannel`, `platform`, `architecture` and `inventory.digest` are **immutable**; any change is refused, so rebinding to other evidence is a new release, not an update;
2. the package set (`packageType`, `relativePath`) is immutable — adding or dropping a released artifact after the fact is refused;
3. each of `signing`, `notarization`, `attestation` and `publication` may only move forward along its own ladder, may not skip a state, and may not regress;
4. a state that has reached `failed` cannot be escaped by a later document;
5. `unsignedDigest` per package is immutable, so the account of what changed stays honest, and `releasedDigest` is immutable once a signing account exists, so the bytes a certificate claims over cannot be re-pointed under an intact-looking signing state;
6. once an identity has been asserted it is immutable: a non-null `signing.identity` may not be swapped for another certificate, and once `attestation.status` leaves `unavailable` its `signerWorkflow`, `sourceRef`, `runId` and `bundleDigest` are frozen. Holding a state while rewriting what that state refers to is a rewrite, not an advance.

## Refusal law

One exception type, `ProvenanceError`, with a lowercase human-readable reason. Unknown keys, missing keys, reordered keys, non-object documents, wrong schema version, unknown enum values, wrong digest format, wrong source SHA, wrong version, wrong channel, wrong platform/type pairing, duplicate or extra package entries, missing entries, absolute paths, traversal, package-set mismatch against the upstream inventory, digest mismatch against the upstream inventory, byte-change without a signing account, impossible state combinations, illegal transitions, identity rewrite under a held state, provenance-as-signing substitution, and fabricated publication claims all fail closed. Nothing is repaired, coerced, defaulted or silently normalized.

## Verifier surface

`tools/desktop/release_provenance.py` is offline, read-only apart from an explicit `--json-out`, and standard-library only. It never opens a network connection, never executes a package, never installs or uploads anything, and never reads a credential.

```text
--build      --inventory --release-channel --json-out
--verify     --provenance --inventory
--gate       --provenance --inventory
--transition --before --after
--channel-gate --release-channel
--environment-protection --environment-record --environment-name
```

Machine-readable results: `RELEASE_PROVENANCE=VALID|INVALID`, `RELEASE_GATE=ALLOW|DENY`, `RELEASE_TRANSITION=LEGAL|ILLEGAL`, `RELEASE_CHANNEL=COHERENT|INCOHERENT`, `RELEASE_PROTECTION=PROTECTED|UNPROTECTED|UNPROVEN`, each refusal followed by `REASON=` or `UNPROVEN_BECAUSE=` and a non-zero exit.

**The verifier is an admission authority, not a claim-minting authority.** `--build` emits only the honest credential-free baseline: it hardcodes `unavailable`/`unsigned-candidate` signing, `not-applicable` notarization, `unavailable` attestation and `not-published` publication, and offers no flag capable of producing a signing, notarization, attestation or publication claim. A later credentialed stage produces candidate documents by transformation; this tool alone decides whether they are admissible.

## Ceilings

- `packages` length 1..8; `relativePath` ≤ 512 characters; `sourceRef` ≤ 255; `releaseTag` ≤ 128; `certificateSubject` ≤ 256; `timestampAuthority` ≤ 256; digests 64-character lowercase hex; `sourceSha` 40-character lowercase hex; `certificateFingerprint` 40..64-character lowercase hex; `runId`/`releaseId` bounded Python integers;
- input files are read as bytes and rejected before parsing if they exceed 262,144 bytes;
- a document that exceeds a ceiling is refused, not truncated.

No separate total-document ceiling is claimed. Every field length and the package count are bounded above, so the serialized size is already bounded by their composition, and a ceiling that no admissible-shape document can reach would be an unfalsifiable claim rather than a bound.

## Authority statement

A valid, verified `hive-release-provenance-v1` document is **evidence about a build**. It is not:

- a publisher-authenticity guarantee for any operating system;
- proof that an artifact was signed, notarized or installed;
- proof that a release exists or that Hive Coder is distributable;
- an updater, endpoint, install, restart or rollback authority;
- a Hive runtime capability, permission or permit — CI release authority and product runtime authority are different domains, and this contract grants neither;
- a substitute for the independent review and governed merge that promotion requires.

## Versioning law

Any new field, enum value, state, transition edge, relaxed bound, or any change to a key tuple, an ordering rule or the serialization is a contract change: it requires a new schema identity (`hive-release-provenance-v2`), a governed Work Order, an accepted decision and review. Under v1, unknown input of any kind fails closed. Under a PROPOSED parent decision, nothing in this file is canonical, and no document conforming to it may be presented as publisher-authentic, notarized, published or production-distributable.
