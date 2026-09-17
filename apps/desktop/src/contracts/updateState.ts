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
 * The table states *structural* legality only. Transitions whose destination is
 * an authenticity-dependent state are additionally authenticity-gated in
 * `evaluateTransition`; see `AUTHENTICITY_DEPENDENT_STATES`.
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

/**
 * Bounded vocabulary of outcomes a *persisted* history entry may carry.
 *
 * This is deliberately narrower than `TransitionReason`. `illegal_transition` and
 * `unknown_state` describe a live evaluation of raw input, and a persisted
 * `UpdateEvent` cannot represent that situation: its `from` and `to` are already
 * validated state names and its edge must be a declared legal transition.
 * Persisting attempted raw input requires a distinct, separately reviewed event
 * type rather than overloading this one.
 */
export const PERSISTED_EVENT_OUTCOMES = [
  "legal_transition",
  "authenticity_proof_required",
  "malformed_authenticity_proof",
] as const;

export type PersistedEventOutcome = (typeof PERSISTED_EVENT_OUTCOMES)[number];

export function isPersistedEventOutcome(value: unknown): value is PersistedEventOutcome {
  return typeof value === "string" && (PERSISTED_EVENT_OUTCOMES as readonly string[]).includes(value);
}

/**
 * Bounded refusal outcomes admissible on a reachable proof-gated attempt, i.e. on
 * `verifying -> ready`: an attempt was made and refused, and the refusal reason is
 * one the gate itself can produce.
 */
export const PROOF_REFUSAL_OUTCOMES = ["authenticity_proof_required", "malformed_authenticity_proof"] as const;

export type ProofRefusalOutcome = (typeof PROOF_REFUSAL_OUTCOMES)[number];

/**
 * States whose claim depends on a successful traversal of the proof-gated install
 * path: `ready` is install-ready, `installing` is downstream of it, and `success`
 * is reachable only from `installing`.
 *
 * Asserting any of them asserts that an authenticity proof was verified and acted
 * on. No state in this set may therefore be claimed by a transition, a status
 * snapshot or a recorded history entry while no scheme is admitted.
 */
export const AUTHENTICITY_DEPENDENT_STATES = ["ready", "installing", "success"] as const;

export type AuthenticityDependentState = (typeof AUTHENTICITY_DEPENDENT_STATES)[number];

export function isAuthenticityDependentState(value: unknown): value is AuthenticityDependentState {
  return typeof value === "string" && (AUTHENTICITY_DEPENDENT_STATES as readonly string[]).includes(value);
}

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
 *
 * The proof must be a plain own-data record: a class instance, an
 * `Object.create(...)` object or an accessor-backed object is refused without any
 * getter being invoked.
 */
export function evaluateAuthenticityProof(proof: unknown): ProofVerdict {
  const candidate = asPlainRecord(proof);
  if (candidate === null) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  const scheme = candidate.data("scheme");
  if (typeof scheme !== "string" || scheme.length === 0) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  const artifactSha256 = candidate.data("artifactSha256");
  if (
    typeof artifactSha256 !== "string" ||
    !SHA256_PATTERN.test(artifactSha256) ||
    artifactSha256.length !== MAX_AUTHENTICITY_HASH_CHARS
  ) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  const metadataSha256 = candidate.data("metadataSha256");
  if (typeof metadataSha256 !== "string" || !SHA256_PATTERN.test(metadataSha256)) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  const verifiedAtEpochMs = candidate.data("verifiedAtEpochMs");
  if (
    typeof verifiedAtEpochMs !== "number" ||
    !Number.isSafeInteger(verifiedAtEpochMs) ||
    verifiedAtEpochMs < 0
  ) {
    return { ok: false, reason: "malformed_authenticity_proof" };
  }
  if (!ADMITTED_AUTHENTICITY_SCHEMES.includes(scheme)) {
    return { ok: false, reason: "no_admitted_scheme" };
  }
  return { ok: true };
}

/**
 * The authenticity gate sits on every edge that *enters an authenticity-dependent
 * state*, not merely on the edge that starts installing.
 *
 * `ready` is install-ready by definition: once a client is `ready`, the artifact
 * is present, verified enough to install and awaiting only the install call.
 * Admitting `verifying -> ready` without a proof would make install-ready
 * reachable from untrusted input. `ready -> installing` and `installing -> success`
 * are gated for the same reason: a completed install is as much an
 * authenticity claim as an install-ready one.
 */
const PROOF_GATED_TRANSITIONS: readonly (readonly [UpdateState, UpdateState])[] = [
  ["verifying", "ready"],
  ["ready", "installing"],
  ["installing", "success"],
];

function isProofGatedTransition(from: UpdateState, to: UpdateState): boolean {
  return PROOF_GATED_TRANSITIONS.some(([gatedFrom, gatedTo]) => gatedFrom === from && gatedTo === to);
}

/**
 * Deterministic transition law. Unknown states fail closed; illegal transitions
 * fail closed; entering any authenticity-dependent state is refused without an
 * accepted authenticity proof.
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
 * States whose entry, and whose presence in a status snapshot or recorded
 * history, requires an accepted authenticity proof.
 */
export function requiresAuthenticityProof(state: UpdateState): boolean {
  return isAuthenticityDependentState(state);
}

/**
 * True only when an authenticity-dependent state can be reached at all. No scheme
 * is admitted in this slice, so with the gate on every entering edge the whole
 * install path is unreachable by construction rather than by convention.
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
  /** Outcome of the recorded attempt; a closed semantic vocabulary, not `TransitionReason`. */
  readonly reason: PersistedEventOutcome;
}

export interface UpdateStatus {
  readonly contract: typeof UPDATE_STATE_CONTRACT;
  readonly state: UpdateState;
  readonly channel: ReleaseChannel;
  readonly currentVersion: string;
  /** Candidate version when one is known; `null` otherwise. */
  readonly candidateVersion: string | null;
  /**
   * Accepted authenticity proof. Admissible only in an authenticity-dependent
   * state (`ready`, `installing`, `success`), where it is mandatory; `null`
   * everywhere else.
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

/**
 * A validated plain record: a JSON-like data object whose own enumerable string
 * keys are the only properties it has, and whose values are reachable without
 * executing any accessor.
 *
 * `Object.keys()` alone is not sufficient here. A required field can be inherited
 * through a custom prototype or a class instance, and a field can be backed by a
 * getter that runs arbitrary code the moment validation reads it. Both are
 * refused, and they are refused *before* any application field is read: values
 * come from own property descriptors, never from property access, so a getter is
 * never invoked by this validator.
 */
interface PlainRecord {
  /** Own enumerable string keys, in insertion order. */
  readonly keys: readonly string[];
  /** Value of an own data property, or `undefined` when it is absent. */
  data(key: string): unknown;
}

function asPlainRecord(value: unknown): PlainRecord | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
  const prototype: object | null = Object.getPrototypeOf(value);
  if (prototype !== Object.prototype && prototype !== null) return null;
  if (Object.getOwnPropertySymbols(value).length > 0) return null;
  const keys = Object.keys(value);
  // A non-enumerable own property is invisible to `Object.keys()` yet still
  // readable through normal access, so the two name sets must agree exactly.
  if (Object.getOwnPropertyNames(value).length !== keys.length) return null;
  const values = new Map<string, unknown>();
  for (const key of keys) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (descriptor === undefined) return null;
    if (descriptor.get !== undefined || descriptor.set !== undefined) return null;
    values.set(key, descriptor.value);
  }
  return { keys, data: (key: string) => values.get(key) };
}

function hasOnlyKeys(record: PlainRecord, allowed: readonly string[]): boolean {
  return record.keys.every((key) => allowed.includes(key));
}

/**
 * Read one array element without invoking a possibly accessor-backed index, and
 * refuse holes. A sparse or accessor-backed array is not JSON-like data.
 */
function arrayElement(array: readonly unknown[], index: number): { readonly present: boolean; readonly value: unknown } {
  const descriptor = Object.getOwnPropertyDescriptor(array, String(index));
  if (descriptor === undefined || descriptor.get !== undefined || descriptor.set !== undefined) {
    return { present: false, value: undefined };
  }
  return { present: true, value: descriptor.value };
}

export type PersistedEventRejection =
  | "unknown_state"
  | "unreachable_source_state"
  | "undeclared_edge"
  | "inadmissible_outcome";

export type PersistedEventVerdict =
  | { readonly ok: true; readonly event: UpdateEvent }
  | { readonly ok: false; readonly reason: PersistedEventRejection };

/**
 * Persisted-event law for current contract v1.
 *
 * A recorded history entry is evidence, so it must be an assertion this contract
 * could actually have produced. Four rules, in order:
 *
 * 1. `from` and `to` must be declared states.
 * 2. `from` must not be an authenticity-dependent state. Entering one requires an
 *    accepted authenticity proof, and no scheme is admitted in this slice, so
 *    such a state cannot have been entered and cannot be the source of a recorded
 *    event — in either direction, and for any reason. (Admitting a scheme would
 *    change that, and therefore requires a governed change to this law.)
 * 3. `from -> to` must be a declared legal edge.
 * 4. The outcome must be possible for that edge. On an ordinary reachable edge
 *    whose destination is not authenticity-dependent, the only possible outcome
 *    is `legal_transition`. On the one reachable proof-gated attempt,
 *    `verifying -> ready`, `legal_transition` is impossible while no scheme is
 *    admitted and only the bounded proof-refusal outcomes may be recorded.
 *
 * Because `from` may not be authenticity-dependent, `verifying -> ready` is the
 * only edge that can reach rule 4 in the gated branch: `ready -> installing` and
 * `installing -> success` both start from a state rule 2 already rejects.
 */
export function evaluatePersistedEvent(from: unknown, to: unknown, reason: unknown): PersistedEventVerdict {
  if (!isUpdateState(from) || !isUpdateState(to)) {
    return { ok: false, reason: "unknown_state" };
  }
  if (isAuthenticityDependentState(from)) {
    return { ok: false, reason: "unreachable_source_state" };
  }
  if (!LEGAL_TRANSITIONS[from].includes(to)) {
    return { ok: false, reason: "undeclared_edge" };
  }
  if (isAuthenticityDependentState(to)) {
    if (!isPersistedEventOutcome(reason) || reason === "legal_transition") {
      return { ok: false, reason: "inadmissible_outcome" };
    }
  } else if (reason !== "legal_transition") {
    return { ok: false, reason: "inadmissible_outcome" };
  }
  return { ok: true, event: { from, to, reason } };
}

/**
 * Validate a status snapshot into a canonical object.
 *
 * The input must be a plain own-data record, and so must its nested error, event
 * and proof objects; inherited, class-backed and accessor-backed records are
 * refused without any getter being invoked. Every field is then bounded and
 * cross-checked: unknown keys, unknown states or channels, malformed versions, a
 * version that does not belong to the declared channel, an incoherent candidate,
 * a proof outside an authenticity-dependent state, unknown error codes, and
 * oversized event lists all fail closed.
 *
 * Every recorded event is validated by `evaluatePersistedEvent`, so history must
 * be an assertion this contract could actually have produced: no event may assert
 * an authenticity-dependent source state, and no outcome may be attached to an
 * edge that could not have produced it.
 *
 * The returned status is **reconstructed** from validated fields. The caller's
 * object is never aliased, so an unvalidated property cannot survive into
 * product state through the returned value.
 */
export function evaluateStatus(input: unknown): StatusVerdict {
  const value = asPlainRecord(input);
  if (value === null) return { ok: false, reason: "invalid_status" };
  if (!hasOnlyKeys(value, UPDATE_STATUS_KEYS)) return { ok: false, reason: "invalid_status" };
  if (value.data("contract") !== UPDATE_STATE_CONTRACT) return { ok: false, reason: "invalid_status" };
  const rawState = value.data("state");
  if (!isUpdateState(rawState)) return { ok: false, reason: "invalid_status" };
  const rawChannel = value.data("channel");
  if (!isReleaseChannel(rawChannel)) return { ok: false, reason: "invalid_status" };

  // One current version and one current channel form a single identity: an
  // independently valid pair that is mutually incompatible fails closed here.
  const state = rawState;
  const channel = rawChannel;
  const rawCurrentVersion = value.data("currentVersion");
  if (!isValidVersion(rawCurrentVersion)) return { ok: false, reason: "invalid_status" };
  const currentVersion = rawCurrentVersion;
  if (!versionMatchesChannel(currentVersion, channel)) return { ok: false, reason: "invalid_status" };

  const rawCandidate = value.data("candidateVersion");
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

  // A status snapshot asserts reachability. Any authenticity-dependent state
  // requires a proof accepted under current policy, and no scheme is admitted in
  // this slice, so such a snapshot is always invalid here.
  const authenticityDependent = isAuthenticityDependentState(state);
  const rawProof = value.data("authenticityProof");
  let authenticityProof: AuthenticityProof | null = null;
  if (authenticityDependent) {
    const proofRecord = asPlainRecord(rawProof);
    if (proofRecord === null) return { ok: false, reason: "invalid_status" };
    if (!evaluateAuthenticityProof(proofRecord).ok) return { ok: false, reason: "invalid_status" };
    authenticityProof = {
      scheme: proofRecord.data("scheme") as string,
      artifactSha256: proofRecord.data("artifactSha256") as string,
      metadataSha256: proofRecord.data("metadataSha256") as string,
      verifiedAtEpochMs: proofRecord.data("verifiedAtEpochMs") as number,
    };
  } else if (rawProof !== null) {
    return { ok: false, reason: "invalid_status" };
  }

  const rawError = value.data("error");
  let error: UpdateError | null = null;
  if (rawError !== null) {
    const errorRecord = asPlainRecord(rawError);
    if (errorRecord === null) return { ok: false, reason: "invalid_status" };
    if (!hasOnlyKeys(errorRecord, UPDATE_ERROR_KEYS)) return { ok: false, reason: "invalid_status" };
    const errorVerdict = evaluateUpdateError(errorRecord.data("code"), errorRecord.data("detail"));
    if (!errorVerdict.ok) return { ok: false, reason: "invalid_status" };
    error = errorVerdict.error;
  }
  if (state === "failure" && error === null) return { ok: false, reason: "invalid_status" };
  if (state !== "failure" && state !== "unavailable" && error !== null) {
    return { ok: false, reason: "invalid_status" };
  }

  const rawEvents = value.data("events");
  if (!Array.isArray(rawEvents)) return { ok: false, reason: "invalid_status" };
  if (rawEvents.length > MAX_UPDATE_STATUS_EVENTS) return { ok: false, reason: "oversized_status" };
  const events: UpdateEvent[] = [];
  for (let index = 0; index < rawEvents.length; index += 1) {
    const element = arrayElement(rawEvents, index);
    if (!element.present) return { ok: false, reason: "invalid_status" };
    const eventRecord = asPlainRecord(element.value);
    if (eventRecord === null) return { ok: false, reason: "invalid_status" };
    if (!hasOnlyKeys(eventRecord, UPDATE_EVENT_KEYS)) return { ok: false, reason: "invalid_status" };
    // Every recorded entry is validated by the persisted-event law: declared
    // states, a reachable source, a declared legal edge, and an outcome that edge
    // could actually have produced. See `evaluatePersistedEvent`.
    const eventVerdict = evaluatePersistedEvent(
      eventRecord.data("from"),
      eventRecord.data("to"),
      eventRecord.data("reason"),
    );
    if (!eventVerdict.ok) return { ok: false, reason: "invalid_status" };
    events.push(eventVerdict.event);
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
