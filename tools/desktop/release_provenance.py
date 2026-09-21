"""Deterministic release-provenance contract validator and admission gate.

This tool judges ``hive-release-provenance-v1`` documents (HCODER-WO-0026 /
DEC-030). It is standard-library only, offline, read-only apart from an explicit
``--json-out``, and deterministic: the same facts always produce the same bytes.

It is an **admission authority, not a claim-minting authority**. ``--build`` can
emit only the honest credential-free baseline state and offers no flag able to
produce a signing, notarization, attestation or publication claim; a credentialed
stage produces candidate documents and this tool alone decides whether they are
admissible.

What each guarantee means, and does not mean
--------------------------------------------
The contract keeps five claims separate on purpose. ``unsignedDigest`` /
``releasedDigest`` are byte identity and integrity, inherited from
``hive-package-inventory-v1``. ``inventory.digest`` binds the document to the
exact upstream packaging evidence it descends from. ``attestation`` is build
provenance: which build, from which source, produced these bytes.
``signing`` is operating-system publisher authenticity. ``notarization`` is
platform trust. ``publication`` records an actually completed release. None of
them substitutes for another: a verified attestation never satisfies a
publisher-signing requirement, and no digest ever means publisher authenticity.

Nothing here signs, notarizes, uploads, installs, executes or publishes anything,
and nothing here reads a credential. Private key material, certificates,
notarization credentials and tokens are structurally unrepresentable.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from tools.desktop.package_inventory import (
    KNOWN_PACKAGE_TYPES,
    InventoryError,
    serialize_inventory,
)
from tools.desktop.version_drift import is_valid_version

SCHEMA_VERSION = "hive-release-provenance-v1"

DOCUMENT_KEYS = (
    "schemaVersion",
    "sourceSha",
    "canonicalVersion",
    "releaseChannel",
    "platform",
    "architecture",
    "inventory",
    "attestation",
    "packages",
    "publication",
)
INVENTORY_KEYS = ("digest", "packageCount")
PACKAGE_KEYS = (
    "packageType",
    "relativePath",
    "byteSize",
    "unsignedDigest",
    "releasedDigest",
    "signing",
    "notarization",
)
SIGNING_KEYS = ("status", "verification", "identity")
SIGNING_IDENTITY_KEYS = ("certificateFingerprint", "certificateSubject", "timestampAuthority")
NOTARIZATION_KEYS = ("status", "verification", "reason")
ATTESTATION_KEYS = ("status", "verification", "signerWorkflow", "sourceRef", "runId", "bundleDigest")
PUBLICATION_KEYS = ("status", "releaseId", "releaseTag", "assetSetDigest")

#: Closed ladders. A document may only move forward along its own ladder, one state at a time.
SIGNING_LADDER = ("unavailable", "unsigned-candidate", "signed", "verified")
NOTARIZATION_LADDER = ("not-applicable", "pending", "stapled", "verified")
ATTESTATION_LADDER = ("unavailable", "generated", "verified")
PUBLICATION_LADDER = ("not-published", "staged", "published")
NOTARIZATION_FAILURE = "failed"

VERIFICATIONS = ("none", "failed", "passed")
RELEASE_CHANNELS = ("stable", "beta", "dev")
#: Prerelease identifier required for a version to belong to the channel.
#: Mirrors ``hive-release-channel-v1`` in ``apps/desktop/src/contracts/releaseChannel.ts``.
CHANNEL_PRERELEASE_PREFIX: dict[str, str | None] = {"stable": None, "beta": "beta", "dev": "dev"}
PLATFORMS = ("linux", "macos", "windows")
NOTARIZATION_NA_REASONS = ("platform-windows", "platform-linux", "unsigned-artifact")

#: Package types whose platform offers no enforceable publisher-trust model.
#: Linux is honest about this: AppImage signatures are not validated by the
#: runtime and ``.deb`` signatures are not consulted by apt/dpkg at install time.
NO_PUBLISHER_TRUST_PLATFORMS = ("linux",)

#: Foreign record law. A deployment environment record is authored by the hosting
#: platform and gains fields over time, so unknown keys are tolerated here while
#: every judged field must be present and exact: a record that lacks one is
#: UNPROVEN, never assumed protected. The record's own timing fields are ignored,
#: because the judgement is about semantics and not about recency.
ENVIRONMENT_RECORD_KEYS = ("name", "can_admins_bypass", "protection_rules")
REQUIRED_REVIEWERS_RULE = "required_reviewers"
MAX_ENVIRONMENT_NAME = 255

HEX64 = re.compile(r"^[0-9a-f]{64}$")
SOURCE_SHA = re.compile(r"^[0-9a-f]{40}$")
FINGERPRINT = re.compile(r"^[0-9a-f]{40,64}$")
ARCHITECTURE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
RELEASE_TAG = re.compile(r"^[A-Za-z0-9._/-]{1,128}$")
SOURCE_REF = re.compile(r"^refs/[A-Za-z0-9._/-]{1,250}$")
SIGNER_WORKFLOW = re.compile(
    r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+@refs/(?:heads|tags)/[A-Za-z0-9._/-]{1,250}$"
)
_FOREIGN_ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|[\\/]{2})")

MAX_PACKAGES = 8
MAX_RELATIVE_PATH = 512
MAX_RELEASE_TAG = 128
MAX_SUBJECT = 256
SUBJECT_DIGEST_ALGORITHM = "sha256"
#: ``sigstore-go`` refuses to verify a statement holding more than this many subjects,
#: so an over-cap set would produce an attestation that stays green at generation time
#: and can never be confirmed by anyone downstream.
MAX_ATTESTATION_SUBJECTS = 1024
#: Package types that are directory bundles rather than one file. This is the same
#: distinction the packaging model draws with its ``is_directory`` spec, and a subject
#: that contradicts it is refused rather than guessed.
DIRECTORY_PACKAGES = ("app",)
#: The inventory records this structural check for a directory bundle, whose digest is
#: the canonical sorted-tree encoding rather than a hash of one file. It is what lets
#: the subject model state each subject's identity kind from data instead of prose.
TREE_DIGEST_CHECK = "tree_digest"
#: ``actions/attest`` reads a checksums file as ``<hex> <flag><name>`` and strips one
#: leading flag character, so a name beginning with a space or an asterisk would be
#: silently rewritten before it ever became a subject.
SUBJECT_NAME_UNSAFE_START = (" ", "*")
#: The subject model is an in-toto statement, so a bundle payload must say so. Without
#: that check any signed JSON could stand in for provenance.
IN_TOTO_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
#: Either predicate binds the statement's subjects to a build. A bundle holding some
#: other predicate is genuine evidence about something else, and this contract does not
#: let it be counted as provenance for these packages.
ATTESTATION_PREDICATE_TYPES = (
    "https://slsa.dev/provenance/v1",
    "https://payments.developers.google.com/cloud/deep-rune/v1alpha1/schema/v1.0",
)
MAX_TIMESTAMP_AUTHORITY = 256
MAX_INPUT_BYTES = 262144


class ProvenanceError(Exception):
    """Raised when a release-provenance document is not admissible."""


def _require_closed(document: Any, keys: tuple[str, ...], *, label: str) -> dict[str, Any]:
    """Require an object that is exactly the closed schema, in declared key order.

    Presence *and* order are both enforced, so an unknown key cannot ride along and
    a reordered document cannot be accepted and then re-serialized differently.
    """
    if not isinstance(document, dict):
        raise ProvenanceError(f"{label} is not a JSON object")
    if tuple(document.keys()) != keys:
        raise ProvenanceError(f"{label} keys are not the exact closed schema (expected {list(keys)})")
    return document


def _require_enum(value: Any, allowed: tuple[str, ...], *, label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ProvenanceError(f"{label} {value!r} is not one of {list(allowed)}")
    return value


def _require_int(value: Any, *, label: str, minimum: int = 0) -> int:
    # ``bool`` is an ``int`` subclass in Python: a boolean must not satisfy an integer field.
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ProvenanceError(f"{label} must be an integer >= {minimum}: {value!r}")
    return value


def _require_bounded_str(value: Any, *, label: str, maximum: int, pattern: re.Pattern[str] | None = None) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise ProvenanceError(f"{label} must be a string of at most {maximum} characters: {value!r}")
    if pattern is not None and not pattern.match(value):
        raise ProvenanceError(f"{label} does not match the closed shape: {value!r}")
    return value


def _validate_relative(relative: Any) -> str:
    if not isinstance(relative, str) or not relative:
        raise ProvenanceError(f"relativePath must be a non-empty string: {relative!r}")
    if len(relative) > MAX_RELATIVE_PATH:
        raise ProvenanceError(f"relativePath exceeds {MAX_RELATIVE_PATH} characters")
    if relative.startswith("/") or relative.startswith("\\") or _FOREIGN_ABSOLUTE.match(relative):
        raise ProvenanceError(f"absolute path is not allowed: {relative}")
    if "\\" in relative:
        raise ProvenanceError(f"relative path must use POSIX separators: {relative}")
    if ".." in Path(relative).parts:
        raise ProvenanceError(f"path traversal is not allowed: {relative}")
    return relative


def split_prerelease(version: str) -> str | None:
    """First-order prerelease segment of a strict SemVer version, or ``None``.

    Build metadata is stripped before the prerelease split, so ``1.0.0-alpha+001``
    yields ``alpha`` and a hyphen inside build metadata cannot masquerade as a
    prerelease.
    """
    without_build = version.split("+", 1)[0]
    core, separator, prerelease = without_build.partition("-")
    if not separator or not core:
        return None
    return prerelease


def version_matches_channel(version: str, channel: str) -> bool:
    """The Python half of ``hive-release-channel-v1``; must agree with the TypeScript rule."""
    prefix = CHANNEL_PRERELEASE_PREFIX[channel]
    prerelease = split_prerelease(version)
    if prefix is None:
        return prerelease is None
    if prerelease is None:
        return False
    return prerelease.split(".", 1)[0] == prefix


def canonical_bytes(payload: Any) -> bytes:
    """Canonical serialization: declared key order, two-space indent, ASCII, trailing newline."""
    return (json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=False) + "\n").encode("utf-8")


def inventory_binding_digest(inventory_document: dict[str, Any]) -> str:
    """SHA-256 over the exact canonical bytes of the upstream inventory document.

    Reusing ``serialize_inventory`` is deliberate: it is the only serializer whose
    bytes define the upstream evidence, so binding here cannot drift from the
    packaging model that produced it.
    """
    return hashlib.sha256(serialize_inventory(inventory_document).encode("utf-8")).hexdigest()


def asset_set_digest(packages: list[dict[str, Any]]) -> str:
    """Immutable identity of the released package set as recorded by this document."""
    return hashlib.sha256(canonical_bytes(packages)).hexdigest()


def attestation_subjects(inventory_document: Any) -> list[dict[str, str]]:
    """The exact attestation subject set this release must attest, from validated inventory.

    One subject per package, named by the inventory's own ``relativePath`` and digested
    by the inventory's own ``digest``: the packaging model already authored this
    identity, so re-discovering it from the filesystem would create a second, rival
    package inventory and silently allow the two to disagree.

    ``identityKind`` separates the two ways a CP-0025 digest is computed. A macOS
    ``.app`` is a directory bundle whose digest is a sorted-tree encoding, and no GitHub
    attestation surface hashes a directory; recording that fact per subject is what
    keeps the tree digest from being read as a file digest downstream.
    """
    if not isinstance(inventory_document, dict):
        raise ProvenanceError("upstream inventory is not a JSON object")
    try:
        serialize_inventory(inventory_document)
    except InventoryError as exc:
        raise ProvenanceError(f"upstream inventory is not a valid hive-package-inventory-v1 document: {exc}") from exc

    entries = inventory_document["packages"]
    if not entries:
        raise ProvenanceError("an attestation subject set needs at least one package")
    if len(entries) > MAX_ATTESTATION_SUBJECTS:
        raise ProvenanceError(f"package count exceeds the {MAX_ATTESTATION_SUBJECTS}-subject ceiling")

    subjects: list[dict[str, str]] = []
    for entry in sorted(entries, key=lambda item: (item["packageType"], item["relativePath"])):
        relative = _validate_relative(entry["relativePath"])
        if relative.startswith(SUBJECT_NAME_UNSAFE_START):
            raise ProvenanceError(f"relativePath would be rewritten by the checksums grammar: {relative!r}")
        if "\r" in relative or "\n" in relative:
            raise ProvenanceError(f"subject names may not contain a line ending: {relative!r}")
        if entry["digestAlgorithm"] != SUBJECT_DIGEST_ALGORITHM:
            raise ProvenanceError(
                f"subject digest algorithm must be {SUBJECT_DIGEST_ALGORITHM!r}: {entry['digestAlgorithm']!r}"
            )
        digest = entry["digest"]
        if not HEX64.match(digest):
            raise ProvenanceError(f"subject digest is not a lowercase 64-character hex SHA-256: {digest!r}")
        declared_tree = TREE_DIGEST_CHECK in entry["structuralValidation"]
        actual_tree = entry["packageType"] in DIRECTORY_PACKAGES
        if declared_tree != actual_tree:
            raise ProvenanceError(
                f"package {entry['packageType']} declares a {'tree' if declared_tree else 'file'} digest "
                f"but is a {'directory bundle' if actual_tree else 'file'}"
            )
        subjects.append(
            {
                "name": relative,
                "digest": f"{SUBJECT_DIGEST_ALGORITHM}:{digest}",
                "identityKind": "sorted-tree" if declared_tree else "file-bytes",
            }
        )
    return subjects


def render_attestation_checksums(inventory_document: Any) -> str:
    """The ``actions/attest`` ``subject-checksums`` body for exactly this release's packages.

    Two spaces separate digest from name: the first is the delimiter and the second is
    the text-mode flag the parser consumes. A trailing newline is required because the
    parser splits on line endings and a last record without one is still a record, but
    an empty line between records would be dropped rather than reported.
    """
    lines = []
    for subject in attestation_subjects(inventory_document):
        algorithm, separator, digest = subject["digest"].partition(":")
        if not separator or algorithm != SUBJECT_DIGEST_ALGORITHM:
            raise ProvenanceError(f"unsupported subject digest: {subject['digest']!r}")
        lines.append(f"{digest}  {subject['name']}")
    return "\n".join(lines) + "\n"


def bundle_subjects(bundle_document: Any) -> list[dict[str, Any]]:
    """The subjects an attestation bundle actually signed, read from its own statement.

    A DSSE envelope carries the statement as a base64 payload, and that payload is the
    only place a subject lives. Signatures, certificate identity and timestamps say that
    someone signed *something*; only the payload says *what*. So the subject set can be
    judged from the bundle document offline, with no signature and no network.
    """
    if not isinstance(bundle_document, dict):
        raise ProvenanceError("attestation bundle is not a JSON object")
    envelope = bundle_document.get("dsseEnvelope")
    if not isinstance(envelope, dict):
        raise ProvenanceError("attestation bundle carries no dsseEnvelope")
    payload = envelope.get("payload")
    if not isinstance(payload, str) or not payload:
        raise ProvenanceError("attestation envelope carries no payload")
    try:
        statement_bytes = base64.b64decode(payload, validate=True)
    except ValueError as exc:
        raise ProvenanceError(f"attestation envelope payload is not base64: {exc}") from exc
    try:
        statement = json.loads(statement_bytes)
    except ValueError as exc:
        raise ProvenanceError(f"attestation statement is not JSON: {exc}") from exc
    if not isinstance(statement, dict):
        raise ProvenanceError("attestation statement is not a JSON object")
    if statement.get("_type") != IN_TOTO_STATEMENT_TYPE:
        raise ProvenanceError(
            f"attestation statement is not an in-toto statement: {statement.get('_type')!r}"
        )
    if statement.get("predicateType") not in ATTESTATION_PREDICATE_TYPES:
        raise ProvenanceError(
            f"attestation predicate is not build provenance this contract can read: "
            f"{statement.get('predicateType')!r}"
        )
    subjects = statement.get("subject")
    if not isinstance(subjects, list):
        raise ProvenanceError("attestation statement carries no subject list")
    return subjects


def verify_attestation_subjects(observed: Any, inventory_document: Any) -> list[dict[str, str]]:
    """Require the subjects a bundle actually signed to be exactly this release's packages.

    ``gh attestation verify`` matches a supplied artifact against the statement by digest
    alone and reports nothing about the other subjects, so verifying one package is not
    evidence about the set. This is the check that closes that gap: no missing subject, no
    unexpected subject, no digest bound to a name that the inventory never recorded.
    """
    expected = attestation_subjects(inventory_document)
    if not isinstance(observed, list):
        raise ProvenanceError("attestation subjects are not a list")
    if not observed:
        raise ProvenanceError("attestation holds no subject, so it attests nothing")
    if len(observed) > MAX_ATTESTATION_SUBJECTS:
        raise ProvenanceError(f"attestation exceeds the {MAX_ATTESTATION_SUBJECTS}-subject ceiling")

    expected_by_name = {subject["name"]: subject["digest"] for subject in expected}
    observed_by_name: dict[str, str] = {}
    for subject in observed:
        if not isinstance(subject, dict) or set(subject) != {"name", "digest"}:
            raise ProvenanceError(f"attestation subject is not a name/digest pair: {subject!r}")
        if not isinstance(subject["name"], str) or not isinstance(subject["digest"], dict):
            raise ProvenanceError(f"attestation subject fields are the wrong shape: {subject!r}")
        if not subject["digest"]:
            raise ProvenanceError(f"attestation subject carries no digest: {subject['name']!r}")
        for algorithm, digest in subject["digest"].items():
            if algorithm != SUBJECT_DIGEST_ALGORITHM or not HEX64.match(str(digest)):
                raise ProvenanceError(
                    f"attestation subject {subject['name']!r} has an unexpected digest: {algorithm}={digest!r}"
                )
        name = subject["name"]
        digest = f"{SUBJECT_DIGEST_ALGORITHM}:{subject['digest'][SUBJECT_DIGEST_ALGORITHM]}"
        if name in observed_by_name:
            raise ProvenanceError(
                f"attestation repeats a subject name, so the set is not a package identity: {name!r}"
            )
        observed_by_name[name] = digest

    if observed_by_name == expected_by_name:
        return expected
    details = []
    missing = sorted(name for name in expected_by_name if name not in observed_by_name)
    unexpected = sorted(name for name in observed_by_name if name not in expected_by_name)
    differing = sorted(
        name
        for name, digest in observed_by_name.items()
        if name in expected_by_name and expected_by_name[name] != digest
    )
    if missing:
        details.append(f"missing {missing}")
    if unexpected:
        details.append(f"unexpected {unexpected}")
    if differing:
        details.append(f"a digest differs on {differing}")
    raise ProvenanceError(
        "attestation subject set is not this release's package set: "
        f"{'; '.join(details)} (expected {sorted(expected_by_name)})"
    )


def _validate_signing(signing: Any, *, label: str) -> str:
    _require_closed(signing, SIGNING_KEYS, label=f"{label} signing")
    status = _require_enum(signing["status"], SIGNING_LADDER, label=f"{label} signing.status")
    verification = _require_enum(signing["verification"], VERIFICATIONS, label=f"{label} signing.verification")
    identity = signing["identity"]

    if status in ("unavailable", "unsigned-candidate"):
        if identity is not None:
            raise ProvenanceError(f"{label} signing identity is unrepresentable before any signing occurs")
        if verification != "none":
            raise ProvenanceError(f"{label} unsigned state must not carry a verification result")
        return status

    if not isinstance(identity, dict):
        raise ProvenanceError(f"{label} signing {status} requires a public identity object")
    _require_closed(identity, SIGNING_IDENTITY_KEYS, label=f"{label} signing.identity")
    _require_bounded_str(
        identity["certificateFingerprint"], label=f"{label} certificateFingerprint", maximum=64, pattern=FINGERPRINT
    )
    _require_bounded_str(identity["certificateSubject"], label=f"{label} certificateSubject", maximum=MAX_SUBJECT)
    _require_bounded_str(
        identity["timestampAuthority"], label=f"{label} timestampAuthority", maximum=MAX_TIMESTAMP_AUTHORITY
    )

    if verification == "failed":
        if status != "signed":
            raise ProvenanceError(f"{label} failed verification cannot coexist with signing.status {status!r}")
        # A failed verification must stay visible rather than rewinding the record; the
        # ladder refuses any later advance past it.
    if status == "verified" and verification != "passed":
        raise ProvenanceError(f"{label} signing success requires an independent passed verification result")
    if status == "signed" and verification == "passed":
        raise ProvenanceError(f"{label} a passed verification result must be recorded as verified, not signed")
    return status


def _validate_notarization(notarization: Any, *, platform: str, signing_status: str, label: str) -> None:
    _require_closed(notarization, NOTARIZATION_KEYS, label=f"{label} notarization")
    status = _require_enum(
        notarization["status"], NOTARIZATION_LADDER + (NOTARIZATION_FAILURE,), label=f"{label} notarization.status"
    )
    verification = _require_enum(
        notarization["verification"], VERIFICATIONS, label=f"{label} notarization.verification"
    )
    reason = _require_bounded_str(notarization["reason"], label=f"{label} notarization.reason", maximum=64)

    if platform != "macos" and status != "not-applicable":
        raise ProvenanceError(f"{label} platform {platform} has no notarization state to hold")
    if status == NOTARIZATION_FAILURE:
        if verification != "failed":
            raise ProvenanceError(f"{label} notarization failure must be recorded with a failed verification")
        return
    if status == "not-applicable":
        _require_enum(reason, NOTARIZATION_NA_REASONS, label=f"{label} notarization not-applicable reason")
        if verification != "none":
            raise ProvenanceError(f"{label} not-applicable notarization must not carry a verification result")
        return
    if reason:
        raise ProvenanceError(f"{label} notarization {status!r} must not carry a not-applicable reason")
    if status in ("stapled", "verified") and signing_status not in ("signed", "verified"):
        raise ProvenanceError(f"{label} cannot staple a ticket to an unsigned artifact")
    if status == "verified" and verification != "passed":
        raise ProvenanceError(f"{label} notarization success requires an independent passed verification result")
    if status in ("pending", "stapled") and verification == "passed":
        raise ProvenanceError(f"{label} a passed verification result must be recorded as verified")


def _validate_attestation(attestation: Any) -> None:
    _require_closed(attestation, ATTESTATION_KEYS, label="attestation")
    status = _require_enum(attestation["status"], ATTESTATION_LADDER, label="attestation.status")
    verification = _require_enum(attestation["verification"], VERIFICATIONS, label="attestation.verification")
    signer = _require_bounded_str(attestation["signerWorkflow"], label="signerWorkflow", maximum=304)
    source_ref = _require_bounded_str(attestation["sourceRef"], label="sourceRef", maximum=255)
    run_id = _require_int(attestation["runId"], label="runId")
    bundle = _require_bounded_str(attestation["bundleDigest"], label="bundleDigest", maximum=64)

    if status == "unavailable":
        if signer or source_ref or bundle or run_id:
            raise ProvenanceError("unavailable attestation must not carry identity fields")
        if verification != "none":
            raise ProvenanceError("unavailable attestation must not carry a verification result")
        return
    if verification == "failed" and status != "generated":
        raise ProvenanceError(f"failed attestation verification cannot coexist with status {status!r}")
    if signer and not SIGNER_WORKFLOW.match(signer):
        raise ProvenanceError(f"signerWorkflow does not match owner/repo@refs/... : {signer!r}")
    if source_ref and not SOURCE_REF.match(source_ref):
        raise ProvenanceError(f"sourceRef does not match refs/... : {source_ref!r}")
    if bundle and not HEX64.match(bundle):
        raise ProvenanceError(f"bundleDigest must be a 64-character lowercase hex SHA: {bundle!r}")
    if status == "generated":
        if not signer or not source_ref or not bundle or run_id <= 0:
            raise ProvenanceError("generated attestation requires signerWorkflow, sourceRef, runId and bundleDigest")
        if verification == "passed":
            # Mirrors the signing rule: an achieved verification is a state, not an attribute of a lower one.
            raise ProvenanceError("a passed verification result must be recorded as verified, not generated")
        return
    if verification != "passed":
        raise ProvenanceError("attestation success requires an independent passed verification result")


def _validate_publication(publication: Any, packages: list[dict[str, Any]]) -> str:
    _require_closed(publication, PUBLICATION_KEYS, label="publication")
    status = _require_enum(publication["status"], PUBLICATION_LADDER, label="publication.status")
    release_id = _require_int(publication["releaseId"], label="releaseId")
    tag = _require_bounded_str(publication["releaseTag"], label="releaseTag", maximum=MAX_RELEASE_TAG)
    asset_set = _require_bounded_str(publication["assetSetDigest"], label="assetSetDigest", maximum=64)

    if status == "not-published":
        if release_id or tag or asset_set:
            raise ProvenanceError("not-published state must not carry release identity")
        return status
    if not release_id or not tag:
        raise ProvenanceError(f"publication {status!r} requires an exact release id and tag")
    if not RELEASE_TAG.match(tag):
        raise ProvenanceError(f"releaseTag does not match the closed shape: {tag!r}")
    if status == "published":
        if not HEX64.match(asset_set):
            raise ProvenanceError("published state requires the released artifact-set identity digest")
        if asset_set != asset_set_digest(packages):
            raise ProvenanceError(
                "publication claim does not match the released artifact set recorded in this document"
            )
    elif asset_set:
        raise ProvenanceError("staged state must not yet assert an artifact-set identity digest")
    return status


def validate_document(document: Any) -> dict[str, Any]:
    """Validate the closed schema and the whole internal law of one document."""
    _require_closed(document, DOCUMENT_KEYS, label="provenance document")
    if document["schemaVersion"] != SCHEMA_VERSION:
        raise ProvenanceError(f"schemaVersion {document['schemaVersion']!r} != {SCHEMA_VERSION!r}")
    source_sha = _require_bounded_str(document["sourceSha"], label="sourceSha", maximum=40, pattern=SOURCE_SHA)
    version = _require_bounded_str(document["canonicalVersion"], label="canonicalVersion", maximum=128)
    if not is_valid_version(version):
        raise ProvenanceError(f"canonicalVersion is not a valid {SCHEMA_VERSION} version: {version!r}")
    channel = _require_enum(document["releaseChannel"], RELEASE_CHANNELS, label="releaseChannel")
    platform = _require_enum(document["platform"], PLATFORMS, label="platform")
    _require_bounded_str(document["architecture"], label="architecture", maximum=64, pattern=ARCHITECTURE)

    if not version_matches_channel(version, channel):
        raise ProvenanceError(f"canonicalVersion {version!r} does not belong to releaseChannel {channel!r}")

    inventory = _require_closed(document["inventory"], INVENTORY_KEYS, label="inventory")
    _require_bounded_str(inventory["digest"], label="inventory.digest", maximum=64, pattern=HEX64)
    _require_int(inventory["packageCount"], label="inventory.packageCount", minimum=1)

    packages = document["packages"]
    if not isinstance(packages, list) or not packages:
        raise ProvenanceError("packages must be a non-empty list")
    if len(packages) > MAX_PACKAGES:
        raise ProvenanceError(f"packages exceeds the closed ceiling of {MAX_PACKAGES} entries")

    seen_types: set[str] = set()
    for entry in packages:
        _require_closed(entry, PACKAGE_KEYS, label="package entry")
        package_type = _require_enum(entry["packageType"], tuple(sorted(KNOWN_PACKAGE_TYPES)), label="packageType")
        _validate_relative(entry["relativePath"])
        _require_int(entry["byteSize"], label="byteSize", minimum=1)
        for key in ("unsignedDigest", "releasedDigest"):
            _require_bounded_str(entry[key], label=key, maximum=64, pattern=HEX64)

        if package_type in seen_types:
            raise ProvenanceError(f"duplicate package entry: {package_type}")
        seen_types.add(package_type)

        if KNOWN_PACKAGE_TYPES[package_type] != platform:
            raise ProvenanceError(f"package type {package_type} is not produced on platform {platform}")

        signing_status = _validate_signing(entry["signing"], label=f"package {package_type}")
        if platform in NO_PUBLISHER_TRUST_PLATFORMS and signing_status in ("signed", "verified"):
            raise ProvenanceError(
                f"package {package_type} claims publisher authenticity on {platform}, which offers no "
                "enforceable publisher-trust model"
            )
        _validate_notarization(
            entry["notarization"], platform=platform, signing_status=signing_status, label=f"package {package_type}"
        )

    if len(seen_types) != inventory["packageCount"]:
        raise ProvenanceError(
            f"package count {len(seen_types)} does not match the bound inventory packageCount "
            f"{inventory['packageCount']}"
        )
    ordered = sorted(packages, key=lambda entry: (entry["packageType"], entry["relativePath"]))
    if packages != ordered:
        raise ProvenanceError("packages must be ordered by (packageType, relativePath) for determinism")
    _validate_attestation(document["attestation"])
    _validate_publication(document["publication"], packages)

    return document


def verify_against_inventory(document: dict[str, Any], inventory_document: dict[str, Any]) -> None:
    """Prove the document descends from *this exact* upstream inventory document."""
    validate_document(document)
    if not isinstance(inventory_document, dict):
        raise ProvenanceError("upstream inventory is not a JSON object")
    try:
        digest = inventory_binding_digest(inventory_document)
    except InventoryError as exc:
        raise ProvenanceError(f"upstream inventory is not a valid hive-package-inventory-v1 document: {exc}") from exc

    if document["inventory"]["digest"] != digest:
        raise ProvenanceError(
            "inventory.digest does not match the canonical bytes of the supplied upstream inventory "
            "(the packaging evidence this release claims to descend from is not that document)"
        )
    for key, label in (
        ("sourceSha", "sourceSha"),
        ("canonicalVersion", "canonicalVersion"),
        ("platform", "platform"),
        ("architecture", "architecture"),
    ):
        if document[key] != inventory_document[key]:
            raise ProvenanceError(f"{label} mismatch against upstream inventory: {document[key]!r} != {inventory_document[key]!r}")

    upstream = {entry["packageType"]: entry for entry in inventory_document["packages"]}
    if set(upstream) != {entry["packageType"] for entry in document["packages"]}:
        raise ProvenanceError(
            f"package set does not match the upstream inventory: {sorted(upstream)} != "
            f"{sorted(entry['packageType'] for entry in document['packages'])}"
        )
    for entry in document["packages"]:
        origin = upstream[entry["packageType"]]
        if entry["relativePath"] != origin["relativePath"]:
            raise ProvenanceError(
                f"package {entry['packageType']} relativePath does not match the upstream inventory: "
                f"{entry['relativePath']!r} != {origin['relativePath']!r}"
            )
        if entry["unsignedDigest"] != origin["digest"]:
            raise ProvenanceError(
                f"package {entry['packageType']} unsignedDigest does not match the upstream inventory digest"
            )
        status = entry["signing"]["status"]
        if status in ("unavailable", "unsigned-candidate"):
            if entry["releasedDigest"] != entry["unsignedDigest"]:
                raise ProvenanceError(
                    f"package {entry['packageType']} bytes changed without a signing account "
                    f"(signing.status {status!r})"
                )
            if entry["byteSize"] != origin["byteSize"]:
                raise ProvenanceError(
                    f"package {entry['packageType']} byteSize does not match the upstream inventory"
                )


def _advance(before: str, after: str, ladder: tuple[str, ...], *, label: str) -> None:
    """Require a forward, non-skip, non-regression move along one closed ladder."""
    if before == after:
        return
    if before not in ladder or after not in ladder:
        raise ProvenanceError(f"{label} transition {before!r} -> {after!r} leaves the closed ladder")
    step = ladder.index(after) - ladder.index(before)
    if step < 0:
        raise ProvenanceError(f"{label} regression {before!r} -> {after!r} is not permitted")
    if step > 1:
        skipped = ladder[ladder.index(before) + 1]
        raise ProvenanceError(f"{label} transition {before!r} -> {after!r} skips {skipped!r}")


def validate_transition(before: Any, after: Any) -> None:
    """Prove a later document advances the same release rather than rewriting it."""
    old = validate_document(before)
    new = validate_document(after)

    for key in (
        "sourceSha",
        "canonicalVersion",
        "releaseChannel",
        "platform",
        "architecture",
    ):
        if old[key] != new[key]:
            raise ProvenanceError(f"{key} is immutable across a provenance transition: {old[key]!r} != {new[key]!r}")
    if old["inventory"]["digest"] != new["inventory"]["digest"]:
        raise ProvenanceError("inventory.digest is immutable: rebinding to other packaging evidence is a new release")
    _advance(old["attestation"]["status"], new["attestation"]["status"], ATTESTATION_LADDER, label="attestation")
    if old["attestation"]["status"] != "unavailable":
        # A held status is not the whole claim: which build attested these bytes is itself a
        # fact that a later document must not quietly re-point at another run or bundle.
        for key in ("signerWorkflow", "sourceRef", "runId", "bundleDigest"):
            if old["attestation"][key] != new["attestation"][key]:
                raise ProvenanceError(f"attestation {key} is immutable once an attestation has been asserted")

    old_packages = {entry["packageType"]: entry for entry in old["packages"]}
    new_packages = {entry["packageType"]: entry for entry in new["packages"]}
    if set(old_packages) != set(new_packages):
        raise ProvenanceError(
            f"released package set is immutable: {sorted(old_packages)} != {sorted(new_packages)}"
        )
    for package_type, old_entry in old_packages.items():
        new_entry = new_packages[package_type]
        if old_entry["relativePath"] != new_entry["relativePath"]:
            raise ProvenanceError(f"package {package_type} relativePath is immutable")
        if old_entry["unsignedDigest"] != new_entry["unsignedDigest"]:
            raise ProvenanceError(f"package {package_type} unsignedDigest is immutable")
        _advance(
            old_entry["signing"]["status"],
            new_entry["signing"]["status"],
            SIGNING_LADDER,
            label=f"package {package_type} signing",
        )
        if old_entry["signing"]["verification"] == "failed" and new_entry["signing"]["verification"] != "failed":
            raise ProvenanceError(
                f"package {package_type} cannot escape a failed signing verification by moving forward"
            )
        if old_entry["signing"]["identity"] is not None and new_entry["signing"]["identity"] != old_entry["signing"]["identity"]:
            raise ProvenanceError(f"package {package_type} signing identity is immutable once asserted")
        if old_entry["signing"]["status"] in ("signed", "verified") and new_entry["releasedDigest"] != old_entry["releasedDigest"]:
            # The signing account pins which bytes the signature covers; re-pointing them while the
            # ladder stands still would swap the artifact under an intact-looking certificate claim.
            raise ProvenanceError(f"package {package_type} releasedDigest is immutable once a signing account exists")
        old_notar = old_entry["notarization"]["status"]
        new_notar = new_entry["notarization"]["status"]
        if old_notar == NOTARIZATION_FAILURE:
            raise ProvenanceError(f"package {package_type} cannot escape a failed notarization")
        if new_notar == NOTARIZATION_FAILURE:
            if old_notar == "verified":
                raise ProvenanceError(f"package {package_type} cannot move from verified to failed notarization")
        else:
            _advance(old_notar, new_notar, NOTARIZATION_LADDER, label=f"package {package_type} notarization")

    _advance(old["publication"]["status"], new["publication"]["status"], PUBLICATION_LADDER, label="publication")
    if old["publication"]["status"] == "published":
        raise ProvenanceError("a published release is immutable and cannot be transitioned")


def publication_gate(document: dict[str, Any], inventory_document: dict[str, Any]) -> list[str]:
    """Return the precise reasons this document's artifacts are not yet publishable.

    An empty list is the only admissible answer. The gate reads each guarantee
    separately on purpose: a verified attestation never clears a publisher-signing
    requirement, and platform trust is required exactly where the platform offers it.
    """
    verify_against_inventory(document, inventory_document)
    reasons: list[str] = []
    platform = document["platform"]

    attestation = document["attestation"]
    if attestation["status"] != "verified" or attestation["verification"] != "passed":
        reasons.append("build-provenance-attestation-unverified")

    for entry in document["packages"]:
        package_type = entry["packageType"]
        signing = entry["signing"]
        notarization = entry["notarization"]
        if platform in NO_PUBLISHER_TRUST_PLATFORMS:
            # Linux has no enforceable publisher-trust model, so the honest gate is
            # provenance plus artifact integrity and must never demand a fake signature.
            continue
        if signing["status"] != "verified" or signing["verification"] != "passed":
            reasons.append(f"publisher-signing-unverified:{package_type}")
        if platform == "macos" and (
            notarization["status"] != "verified" or notarization["verification"] != "passed"
        ):
            reasons.append(f"platform-trust-unverified:{package_type}")

    publication = document["publication"]
    if publication["status"] == "published":
        reasons.append("already-published-immutable")
    return reasons


def assess_protection(record: Any, *, expected_name: str | None = None) -> dict[str, Any]:
    """Judge whether one platform environment record describes a gate, not a name.

    Naming an environment is not protection: a platform that silently creates the
    environment on first reference turns a typo into an unprotected release path, and
    protection rules that an administrator may bypass are not a gate at all. An empty
    reason list is the only admissible answer for a credential-bearing stage.
    """
    if not isinstance(record, dict):
        raise ProvenanceError("environment record is not a JSON object")
    missing = [key for key in ENVIRONMENT_RECORD_KEYS if key not in record]
    if missing:
        raise ProvenanceError(f"environment record lacks judged fields: {missing}")

    name = _require_bounded_str(record["name"], label="environment.name", maximum=MAX_ENVIRONMENT_NAME)
    if expected_name is not None and name != expected_name:
        raise ProvenanceError(
            f"environment record identity does not match the environment being probed: "
            f"{name!r} != {expected_name!r}"
        )
    bypass = record["can_admins_bypass"]
    if not isinstance(bypass, bool):
        raise ProvenanceError(f"can_admins_bypass must be an explicit boolean: {bypass!r}")
    rules = record["protection_rules"]
    if not isinstance(rules, list):
        raise ProvenanceError("protection_rules must be a list")

    reasons: list[str] = []
    if not rules:
        reasons.append("protection-rules-absent")
    reviewer_rules = [rule for rule in rules if isinstance(rule, dict) and rule.get("type") == REQUIRED_REVIEWERS_RULE]
    if not reviewer_rules:
        reasons.append("required-reviewers-rule-absent")
    reviewers_counted = 0
    for rule in reviewer_rules:
        reviewers = rule.get("reviewers")
        if not isinstance(reviewers, list):
            raise ProvenanceError("required reviewers rule carries no reviewers list")
        reviewers_counted += sum(1 for entry in reviewers if isinstance(entry, dict) and isinstance(entry.get("reviewer"), dict))
        if rule.get("prevent_self_review") is not True:
            reasons.append("self-review-permitted")
    if reviewer_rules and reviewers_counted < 1:
        reasons.append("required-reviewer-count-below-one")
    if bypass is not False:
        reasons.append("admins-can-bypass-protection")
    return {"environment": name, "protected": not reasons, "reasons": sorted(set(reasons))}


def serialize_provenance(document: dict[str, Any]) -> str:
    """Canonical serialization: declared key order, two-space indent, ASCII, trailing newline."""
    validate_document(document)
    return canonical_bytes(document).decode("ascii")


def build_baseline(
    *,
    inventory_document: dict[str, Any],
    release_channel: str,
) -> dict[str, Any]:
    """Emit the honest credential-free baseline for one real inventory document.

    This is the only document this tool can produce. Every state is hardcoded to
    what a package that has only been built and inventoried actually is:
    unsigned, un-notarized, un-attested and unpublished. There is deliberately no
    parameter that could raise any of them, so a baseline cannot smuggle a claim.
    """
    if not isinstance(inventory_document, dict):
        raise ProvenanceError("upstream inventory is not a JSON object")
    try:
        digest = inventory_binding_digest(inventory_document)
    except InventoryError as exc:
        raise ProvenanceError(f"upstream inventory is not a valid hive-package-inventory-v1 document: {exc}") from exc

    channel = _require_enum(release_channel, RELEASE_CHANNELS, label="releaseChannel")
    platform = _require_enum(inventory_document["platform"], PLATFORMS, label="platform")
    packages = [
        {
            "packageType": entry["packageType"],
            "relativePath": entry["relativePath"],
            "byteSize": entry["byteSize"],
            "unsignedDigest": entry["digest"],
            "releasedDigest": entry["digest"],
            "signing": {"status": "unsigned-candidate", "verification": "none", "identity": None},
            "notarization": {
                "status": "not-applicable",
                "verification": "none",
                "reason": "platform-windows" if platform == "windows" else "platform-linux"
                if platform == "linux"
                else "unsigned-artifact",
            },
        }
        for entry in sorted(inventory_document["packages"], key=lambda item: item["packageType"])
    ]
    document = {
        "schemaVersion": SCHEMA_VERSION,
        "sourceSha": inventory_document["sourceSha"],
        "canonicalVersion": inventory_document["canonicalVersion"],
        "releaseChannel": channel,
        "platform": platform,
        "architecture": inventory_document["architecture"],
        "inventory": {"digest": digest, "packageCount": len(packages)},
        "attestation": {
            "status": "unavailable",
            "verification": "none",
            "signerWorkflow": "",
            "sourceRef": "",
            "runId": 0,
            "bundleDigest": "",
        },
        "packages": packages,
        "publication": {"status": "not-published", "releaseId": 0, "releaseTag": "", "assetSetDigest": ""},
    }
    validate_document(document)
    return document


def _load(path: Path) -> Any:
    """Read one bounded UTF-8 JSON document without leaking a file handle."""
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ProvenanceError(f"unreadable input: {type(exc).__name__}") from exc
    if len(payload) > MAX_INPUT_BYTES:
        raise ProvenanceError(f"input exceeds the closed ceiling of {MAX_INPUT_BYTES} bytes")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProvenanceError("input is not valid UTF-8") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProvenanceError(f"input is not valid JSON: {exc.msg}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Hive Coder release-provenance validator and admission gate (read-only)"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true", help="emit the credential-free baseline for an inventory")
    mode.add_argument("--verify", action="store_true", help="validate a document and its upstream binding")
    mode.add_argument("--gate", action="store_true", help="decide whether the artifacts are publishable")
    mode.add_argument("--transition", action="store_true", help="prove a document only advances another")
    mode.add_argument("--channel-gate", action="store_true", help="check the canonical version against a channel")
    mode.add_argument(
        "--environment-protection",
        action="store_true",
        help="judge a fetched deployment-environment record as a gate or not a gate",
    )
    mode.add_argument(
        "--attest-subjects",
        action="store_true",
        help="emit the exact attestation subjects an inventory requires, and confirm a signed bundle holds them",
    )
    parser.add_argument("--provenance", type=Path, default=None, help="release-provenance document to judge")
    parser.add_argument("--inventory", type=Path, default=None, help="upstream hive-package-inventory-v1 document")
    parser.add_argument("--attest-bundle", type=Path, default=None, help="attestation bundle whose subjects to judge")
    parser.add_argument("--before", type=Path, default=None, help="earlier provenance document")
    parser.add_argument("--after", type=Path, default=None, help="later provenance document")
    parser.add_argument("--environment-record", type=Path, default=None, help="deployment-environment record to judge")
    parser.add_argument("--environment-name", default=None, help="environment name the record must describe")
    parser.add_argument("--release-channel", default=None, choices=list(RELEASE_CHANNELS))
    parser.add_argument("--json-out", type=Path, default=None, help="write the emitted document to this path")
    args = parser.parse_args(argv)

    try:
        if args.build:
            if args.inventory is None or args.release_channel is None:
                raise ProvenanceError("--build requires --inventory and --release-channel")
            document = build_baseline(
                inventory_document=_load(args.inventory),
                release_channel=args.release_channel,
            )
            payload = serialize_provenance(document)
            if args.json_out is not None:
                args.json_out.write_text(payload, encoding="utf-8")
            sys.stdout.write(payload)
            return 0

        if args.channel_gate:
            if args.release_channel is None:
                raise ProvenanceError("--channel-gate requires --release-channel")
            from tools.desktop.version_drift import inspect as inspect_version

            report = inspect_version()
            if report.status != "LOCKED":
                print(f"RELEASE_CHANNEL=INCOHERENT\nREASON=canonical version drift is {report.status}")
                return 2
            if report.canonicalVersion is None:
                print("RELEASE_CHANNEL=INCOHERENT\nREASON=the version source reports no canonical version to bind")
                return 2
            if not version_matches_channel(report.canonicalVersion, args.release_channel):
                print(
                    f"RELEASE_CHANNEL=INCOHERENT\nREASON=canonical version "
                    f"{report.canonicalVersion!r} does not belong to channel {args.release_channel!r}"
                )
                return 2
            print(f"RELEASE_CHANNEL=COHERENT\nCANONICAL_VERSION={report.canonicalVersion}")
            return 0

        if args.environment_protection:
            if args.environment_record is None:
                raise ProvenanceError("--environment-protection requires --environment-record")
            try:
                verdict = assess_protection(
                    _load(args.environment_record), expected_name=args.environment_name
                )
            except ProvenanceError as exc:
                # A record this tool cannot judge is an unproven gate, never a proven one.
                print(f"RELEASE_PROTECTION=UNPROVEN\nUNPROVEN_BECAUSE={exc}")
                return 2
            print(f"RELEASE_PROTECTION={'PROTECTED' if verdict['protected'] else 'UNPROTECTED'}")
            print(f"ENVIRONMENT={verdict['environment']}")
            for reason in verdict["reasons"]:
                print(f"UNPROVEN_BECAUSE={reason}")
            return 0 if verdict["protected"] else 2

        if args.attest_subjects:
            if args.inventory is None or args.attest_bundle is None:
                raise ProvenanceError("--attest-subjects requires --inventory and --attest-bundle")
            expected = verify_attestation_subjects(bundle_subjects(_load(args.attest_bundle)), _load(args.inventory))
            print("ATTESTATION_SUBJECT_SET=MATCHES_PACKAGES")
            for subject in expected:
                print(f"ATTESTATION_SUBJECT_BOUND={subject['name']} identity={subject['identityKind']}")
            return 0

        if args.transition:
            if args.before is None or args.after is None:
                raise ProvenanceError("--transition requires --before and --after")
            validate_transition(_load(args.before), _load(args.after))
            print("RELEASE_TRANSITION=LEGAL")
            return 0

        if args.provenance is None or args.inventory is None:
            raise ProvenanceError(f"--{'gate' if args.gate else 'verify'} requires --provenance and --inventory")
        document = _load(args.provenance)
        inventory_document = _load(args.inventory)

        if args.gate:
            reasons = publication_gate(document, inventory_document)
            if reasons:
                print("RELEASE_GATE=DENY")
                for reason in reasons:
                    print(f"REASON={reason}")
                return 2
            print("RELEASE_GATE=ALLOW")
            return 0

        verify_against_inventory(document, inventory_document)
        print("RELEASE_PROVENANCE=VALID")
        return 0
    except ProvenanceError as exc:
        print(f"RELEASE_PROVENANCE=INVALID\nREASON={exc}")
        return 2
    except OSError as exc:
        print(f"RELEASE_PROVENANCE=INVALID\nREASON=io:{type(exc).__name__}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
