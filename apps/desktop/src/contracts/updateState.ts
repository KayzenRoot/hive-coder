/**
 * Update-state model (HCODER-WO-0024 / HCODER-DIST-001A).
 *
 * This module is the deterministic, side-effect-free state law for a future
 * governed updater. It defines the states, the legal transitions, the mandatory
 * authenticity gate in front of any install-ready state, and bounded
 * redaction-safe error metadata.
 *
 * No state here performs, schedules or authorises a network request, download,
 * install, restart, signature check, release call, process spawn or filesystem
 * mutation. The production `UpdateService` that consumes this law is inert.
 */

import { isReleaseChannel, versionMatchesChannel, type ReleaseChannel } from "./releaseChannel";
import { isStrictlyNewer, isValidVersion } from "./version";

export const UPDATE_STATE_CONTRACT = "hive-update-state-v1" as const;

export const UPDATE_STATES = [
  "idle",
  "checking",
  "available",
  "downloading",
  "verifying",
  "ready",
  "installing",
  "success",
  "failure",
  "unavailable",
] as const;

export type UpdateState = (typeof UPDATE_STATES)[number];

export function isUpdateState(value: unknown): value is UpdateState {
  return typeof value === "string" && (UPDATE_STATES as readonly string[]).includes(value);
}

/**
 * Legal transitions. Every transition not listed here is illegal and must fail
 * closed. Unknown states are rejected before this table is consulted.
 *
 * The table states *structural* legality only. Two of its edges are additionally
 * authenticity-gated in `evaluateTransition`: entering `ready` (the install-ready
 * boundary) and entering `installing` from `ready`.
 */
export const LEGAL_TRANSITIONS: Readonly<Record<UpdateState, readonly UpdateState[]>> = {
  idle: ["checking"],
  checking: ["available", "unavailable", "failure", "idle"],
  available: ["downloading", "idle", "failure"],
  downloading: ["verifying", "failure"],
  verifying: ["ready", "failure"],
  ready: ["installing", "idle", "failure"],
  installing: ["success", "failure"],
  success: ["idle"],
  failure: ["idle"],
  unavailable: ["idle"],
};

/** Closed vocabulary of transition verdicts, including verdict reasons. */
export const TRANSITION_REASONS = [
  "legal_transition",
  "unknown_state",
  "illegal_transition",
  "authenticity_proof_required",
  "malformed_authenticity_proof",
] as const;

export type TransitionReason = (typeof TRANSITION_REASONS)[number];

export function isTransitionReason(value: unknown): value is TransitionReason {
  return typeof value === "string" && (TRANSITION_REASONS as readonly string[]).includes(value);
}

export type TransitionVerdict =
  | { readonly ok: true; readonly reason: "legal_transition" }
  | { readonly ok: false; readonly reason: Exclude<TransitionReason, "legal_transition"> };

export const MAX_AUTHENTICITY_HASH_CHARS = 64;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;

/**
 * Cryptographic schemes admissible in this slice. The set is deliberately empty:
 * HCODER-WO-0024 defines the *structure* of an authenticity proof without
 * inventing, faking or bypassing a real verification scheme. Consequently no
 * proof can be accepted yet, and `ready` is structurally unreachable.
 */
export const ADMITTED_AUTHENTICITY_SCHEMES: readonly string[] = [];

export interface AuthenticityProof {
  /** Verification scheme identifier. Must be admitted to be acceptable. */
  readonly scheme: string;
  /** SHA-256 of the update artifact, lowercase hex, exactly 64 chars. */
  readonly artifactSha256: string;
  /** SHA-256 of the signed update metadata, lowercase hex, exactly 64 chars. */
  readonly metadataSha256: string;
  /** Monotonic non-negative verification instant, epoch milliseconds. */
  readonly verifiedAtEpochMs: number;
}

export type ProofVerdict =
  | { readonly ok: true }
  | { readonly ok: false; readonly reason: "no_admitted_scheme" | "malformed_authenticity_proof" };

/**
 * Structural + policy validation of an authenticity proof. A proof is acceptable
 * only when it is well formed *and* its scheme is admitted. Because no scheme is
 * admitted in this slice, this always refuses — which is the intended behaviour.
 */
export function evaluateAuthenticityProof(proof: unknown): ProofVerdict {
  if (typeof proof !== "object" || proof === null) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  const candidate = proof as Record<string, unknown>;
  if (typeof candidate.scheme !== "string" || candidate.scheme.length === 0) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  if (
    typeof candidate.artifactSha256 !== "string" ||
    !SHA256_PATTERN.test(candidate.artifactSha256) ||
    candidate.artifactSha256.length !== MAX_AUTHENTICITY_HASH_CHARS
  ) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  if (typeof candidate.metadataSha256 !== "string" || !SHA256_PATTERN.test(candidate.metadataSha256)) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  if (
    typeof candidate.verifiedAtEpochMs !== "number" ||
    !Number.isSafeInteger(candidate.verifiedAtEpochMs) ||
    candidate.verifiedAtEpochMs < 0
  ) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  if (!ADMITTED_AUTHENTICITY_SCHEMES.includes(candidate.scheme)) {
    return { ok: false, reason: "no_admitted_scheme" };
  }
  return { ok: true };
}

/**
 * The authenticity gate sits on the edge that *enters an install-ready state*,
 * not merely on the edge that starts installing.
 *
 * `ready` is install-ready by definition: once a client is `ready`, the artifact
 * is present, verified enough to install and awaiting only the install call.
 * Admitting `verifying -> ready` without a proof would make install-ready
 * reachable from untrusted input, so that edge carries the same gate. The
 * `ready -> installing` edge is re-gated as defence in depth so a proof cannot be
 * consumed once and then reused to drive a second install.
 */
const PROOF_GATED_TRANSITIONS: readonly (readonly [UpdateState, UpdateState])[] = [
  ["verifying", "ready"],
  ["ready", "installing"],
];

function isProofGatedTransition(from: UpdateState, to: UpdateState): boolean {
  return PROOF_GATED_TRANSITIONS.some(([gatedFrom, gatedTo]) => gatedFrom === from && gatedTo === to);
}

/**
 * Deterministic transition law. Unknown states fail closed; illegal transitions
 * fail closed; entering `ready` or `installing` is refused without an accepted
 * authenticity proof.
 */
export function evaluateTransition(from: unknown, to: unknown, proof?: unknown): TransitionVerdict {
  if (!isUpdateState(from) || !isUpdateState(to)) {
    return { ok: false, reason: "unknown_state" };
  }
  if (!LEGAL_TRANSITIONS[from].includes(to)) {
    return { ok: false, reason: "illegal_transition" };
  }
  if (isProofGatedTransition(from, to)) {
    // An absent proof is "required"; a present-but-malformed proof is malformed;
    // a well-formed proof whose scheme is not admitted is still "required".
    if (proof === undefined || proof === null) {
      return { ok: false, reason: "authenticity_proof_required" };
    }
    const proofVerdict = evaluateAuthenticityProof(proof);
    if (!proofVerdict.ok) {
      return {
        ok: false,
        reason:
          proofVerdict.reason === "malformed_authenticity_proof"
            ? "malformed_authenticity_proof"
            : "authenticity_proof_required",
      };
    }
  }
  return { ok: true, reason: "legal_transition" };
}

/**
 * States whose *entry* requires an accepted authenticity proof.
 *
 * `ready` is the install-ready state and is the primary gate; `installing` is
 * re-gated so that a proof is required at the moment of install as well.
 */
export function requiresAuthenticityProof(state: UpdateState): boolean {
  return state === "ready" || state === "installing";
}

/**
 * True only when an install-ready state can be reached at all. No scheme is
 * admitted in this slice, so with the gate on `verifying -> ready` the
 * install-ready boundary is unreachable by construction rather than by
 * convention.
 */
export function isInstallReadyReachable(): boolean {
  return ADMITTED_AUTHENTICITY_SCHEMES.length > 0;
}

// ---------------------------------------------------------------------------
// Bounded, redaction-safe error metadata
// ---------------------------------------------------------------------------

export const UPDATE_ERROR_CODES = [
  "malformed_version",
  "unknown_channel",
  "channel_not_eligible",
  "downgrade_not_permitted",
  "cross_channel_not_permitted",
  "authenticity_proof_required",
  "verification_failed",
  "download_failed",
  "install_failed",
  "service_unavailable",
  "service_inert",
] as const;

export type UpdateErrorCode = (typeof UPDATE_ERROR_CODES)[number];

export const MAX_UPDATE_ERROR_DETAIL_CHARS = 160;

/**
 * Diagnostic detail is accepted only when it is short, drawn from a deliberately
 * narrow charset, and free of credential-shaped material. The charset alone is
 * not sufficient: a token composed only of lowercase letters and underscores
 * would satisfy it, so known credential prefixes are rejected explicitly,
 * mirroring the repository's established redaction law in
 * `hive_runtime/control_audit.py`.
 */
const SAFE_DETAIL_PATTERN = /^[a-z0-9 ._:+-]*$/;

const FORBIDDEN_DETAIL_PATTERNS: readonly RegExp[] = [
  /\bBearer\s/i,
  /\bsk-[A-Za-z0-9_-]{8,}/i,
  /\bghp_[A-Za-z0-9]{12,}/,
  /\bgithub_pat_[A-Za-z0-9_]{12,}/,
  /\bxox[baprs]-[A-Za-z0-9-]{8,}/i,
  /\bAKIA[A-Z0-9]{12,}/,
  /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}/,
  /(?:api[_-]?key|token|secret|password|passwd)\s*[:=]/i,
  /[A-Za-z0-9+/]{32,}={0,2}/,
];

export function containsCredentialShape(detail: string): boolean {
  return FORBIDDEN_DETAIL_PATTERNS.some((pattern) => pattern.test(detail));
}

export interface UpdateError {
  readonly code: UpdateErrorCode;
  readonly detail: string;
}

export type ErrorVerdict =
  | { readonly ok: true; readonly error: UpdateError }
  | {
      readonly ok: false;
      readonly reason: "unknown_error_code" | "oversized_error_detail" | "unsafe_error_detail" | "credential_shaped_detail";
    };

export function evaluateUpdateError(code: unknown, detail: unknown): ErrorVerdict {
  if (typeof code !== "string" || !(UPDATE_ERROR_CODES as readonly string[]).includes(code)) {
    return { ok: false, reason: "unknown_error_code" };
  }
  if (typeof detail !== "string" || detail.length > MAX_UPDATE_ERROR_DETAIL_CHARS) {
    return { ok: false, reason: "oversized_error_detail" };
  }
  // Structural rule first: detail must be drawn from the narrow charset. This is
  // what rejects URLs, paths, uppercase-bearing blobs and control characters.
  if (!SAFE_DETAIL_PATTERN.test(detail)) {
    return { ok: false, reason: "unsafe_error_detail" };
  }
  // Second rule: a credential that happens to use only charset-safe characters
  // must still be refused.
  if (containsCredentialShape(detail)) {
    return { ok: false, reason: "credential_shaped_detail" };
  }
  return { ok: true, error: { code: code as UpdateErrorCode, detail } };
}

// ---------------------------------------------------------------------------
// Bounded update status snapshot
// ---------------------------------------------------------------------------

export const MAX_UPDATE_STATUS_EVENTS = 32;
export const MAX_UPDATE_EVENT_LABEL_CHARS = 64;
const SAFE_LABEL_PATTERN = /^[a-z0-9 ._:+-]*$/;

/**
 * Exact admissible key sets. A snapshot carrying any key outside its set is
 * refused rather than partially read, so untrusted payload cannot ride along
 * with a nominally valid snapshot.
 */
export const UPDATE_STATUS_KEYS = [
  "contract",
  "state",
  "channel",
  "currentVersion",
  "candidateVersion",
  "authenticityProof",
  "error",
  "events",
] as const;

export const UPDATE_ERROR_KEYS = ["code", "detail"] as const;

export const UPDATE_EVENT_KEYS = ["from", "to", "reason"] as const;

export interface UpdateEvent {
  readonly from: UpdateState;
  readonly to: UpdateState;
  readonly reason: TransitionReason;
}

export interface UpdateStatus {
  readonly contract: typeof UPDATE_STATE_CONTRACT;
  readonly state: UpdateState;
  readonly channel: ReleaseChannel;
  readonly currentVersion: string;
  /** Candidate version when one is known; `null` otherwise. */
  readonly candidateVersion: string | null;
  /**
   * Accepted authenticity proof. Admissible only in an install-ready state
   * (`ready`, `installing`), where it is mandatory; `null` everywhere else.
   */
  readonly authenticityProof: AuthenticityProof | null;
  readonly error: UpdateError | null;
  readonly events: readonly UpdateEvent[];
}

export type StatusVerdict =
  | { readonly ok: true; readonly status: UpdateStatus }
  | { readonly ok: false; readonly reason: "invalid_status" | "oversized_status" };

/** States in which a candidate version must be known. */
const CANDIDATE_REQUIRED_STATES: readonly UpdateState[] = [
  "available",
  "downloading",
  "verifying",
  "ready",
  "installing",
  "success",
];

/** States in which no candidate version may be present. */
const CANDIDATE_FORBIDDEN_STATES: readonly UpdateState[] = ["idle", "checking", "unavailable"];

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
  return value as Record<string, unknown>;
}

function hasOnlyKeys(value: Record<string, unknown>, allowed: readonly string[]): boolean {
  return Object.keys(value).every((key) => allowed.includes(key));
}

/**
 * Validate a status snapshot into a canonical object.
 *
 * Every field is bounded and cross-checked: unknown keys, unknown states or
 * channels, malformed versions, a version that does not belong to the declared
 * channel, an incoherent candidate, a proof outside an install-ready state,
 * unknown error codes or event shapes, and oversized event lists all fail closed.
 *
 * The returned status is **reconstructed** from validated fields. The caller's
 * object is never aliased, so an unvalidated property cannot survive into
 * product state through the returned value.
 */
export function evaluateStatus(input: unknown): StatusVerdict {
  const value = asRecord(input);
  if (value === null) return { ok: false, reason: "invalid_status" };
  if (!hasOnlyKeys(value, UPDATE_STATUS_KEYS)) return { ok: false, reason: "invalid_status" };
  if (value.contract !== UPDATE_STATE_CONTRACT) return { ok: false, reason: "invalid_status" };
  if (!isUpdateState(value.state)) return { ok: false, reason: "invalid_status" };
  if (!isReleaseChannel(value.channel)) return { ok: false, reason: "invalid_status" };

  // One current version and one current channel form a single identity: an
  // independently valid pair that is mutually incompatible fails closed here.
  const state = value.state;
  const channel = value.channel;
  if (!isValidVersion(value.currentVersion)) return { ok: false, reason: "invalid_status" };
  const currentVersion = value.currentVersion;
  if (!versionMatchesChannel(currentVersion, channel)) return { ok: false, reason: "invalid_status" };

  const rawCandidate = value.candidateVersion;
  if (rawCandidate !== null && !isValidVersion(rawCandidate)) return { ok: false, reason: "invalid_status" };
  const candidateVersion: string | null = rawCandidate === null ? null : rawCandidate;

  if (CANDIDATE_REQUIRED_STATES.includes(state) && candidateVersion === null) {
    return { ok: false, reason: "invalid_status" };
  }
  if (CANDIDATE_FORBIDDEN_STATES.includes(state) && candidateVersion !== null) {
    return { ok: false, reason: "invalid_status" };
  }
  if (candidateVersion !== null) {
    if (!versionMatchesChannel(candidateVersion, channel)) return { ok: false, reason: "invalid_status" };
    // No silent downgrade: a candidate that is not strictly newer than the
    // installed version is incoherent and must never be reported.
    if (!isStrictlyNewer(candidateVersion, currentVersion)) return { ok: false, reason: "invalid_status" };
  }

  // Proof material is admissible only where it is mandatory. Because no scheme
  // is admitted in this slice, no proof can be accepted, so a snapshot claiming
  // `ready` or `installing` is always invalid here.
  const installReady = state === "ready" || state === "installing";
  const rawProof = value.authenticityProof;
  let authenticityProof: AuthenticityProof | null = null;
  if (installReady) {
    const proofRecord = asRecord(rawProof);
    if (proofRecord === null) return { ok: false, reason: "invalid_status" };
    if (!evaluateAuthenticityProof(proofRecord).ok) return { ok: false, reason: "invalid_status" };
    authenticityProof = {
      scheme: proofRecord.scheme as string,
      artifactSha256: proofRecord.artifactSha256 as string,
      metadataSha256: proofRecord.metadataSha256 as string,
      verifiedAtEpochMs: proofRecord.verifiedAtEpochMs as number,
    };
  } else if (rawProof !== null) {
    return { ok: false, reason: "invalid_status" };
  }

  const rawError = value.error;
  let error: UpdateError | null = null;
  if (rawError !== null) {
    const errorRecord = asRecord(rawError);
    if (errorRecord === null) return { ok: false, reason: "invalid_status" };
    if (!hasOnlyKeys(errorRecord, UPDATE_ERROR_KEYS)) return { ok: false, reason: "invalid_status" };
    const errorVerdict = evaluateUpdateError(errorRecord.code, errorRecord.detail);
    if (!errorVerdict.ok) return { ok: false, reason: "invalid_status" };
    error = errorVerdict.error;
  }
  if (state === "failure" && error === null) return { ok: false, reason: "invalid_status" };
  if (state !== "failure" && state !== "unavailable" && error !== null) {
    return { ok: false, reason: "invalid_status" };
  }

  const rawEvents = value.events;
  if (!Array.isArray(rawEvents)) return { ok: false, reason: "invalid_status" };
  if (rawEvents.length > MAX_UPDATE_STATUS_EVENTS) return { ok: false, reason: "oversized_status" };
  const events: UpdateEvent[] = [];
  for (const rawEvent of rawEvents) {
    const eventRecord = asRecord(rawEvent);
    if (eventRecord === null) return { ok: false, reason: "invalid_status" };
    if (!hasOnlyKeys(eventRecord, UPDATE_EVENT_KEYS)) return { ok: false, reason: "invalid_status" };
    const eventFrom = eventRecord.from;
    const eventTo = eventRecord.to;
    if (!isUpdateState(eventFrom) || !isUpdateState(eventTo)) return { ok: false, reason: "invalid_status" };
    if (!isTransitionReason(eventRecord.reason)) return { ok: false, reason: "invalid_status" };
    // Structural legality only. The proof gate is live policy applied at the
    // moment of transition by `evaluateTransition`; it is not a property of a
    // recorded history entry, which may legitimately predate a gate.
    if (!LEGAL_TRANSITIONS[eventFrom].includes(eventTo)) return { ok: false, reason: "invalid_status" };
    events.push({ from: eventFrom, to: eventTo, reason: eventRecord.reason });
  }

  return {
    ok: true,
    status: {
      contract: UPDATE_STATE_CONTRACT,
      state,
      channel,
      currentVersion,
      candidateVersion,
      authenticityProof,
      error,
      events,
    },
  };
}

export function isSafeEventLabel(value: unknown): value is string {
  return typeof value === "string" && value.length <= MAX_UPDATE_EVENT_LABEL_CHARS && SAFE_LABEL_PATTERN.test(value);
}
