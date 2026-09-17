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

import { isReleaseChannel, type ReleaseChannel } from "./releaseChannel";
import { isValidVersion } from "./version";

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
 */
export const LEGAL_TRANSITIONS: Readonly<Record<UpdateState, readonly UpdateState[]>> = {
  idle: ["checking"],
  checking: ["available", "unavailable", "failure", "idle"],
  available: ["downloading", "idle", "failure"],
  downloading: ["verifying", "failure"],
  verifying: ["ready", "failure"],
  // Leaving `ready` towards `installing` additionally requires a consumed
  // authenticity proof; see `evaluateTransition`.
  ready: ["installing", "idle", "failure"],
  installing: ["success", "failure"],
  success: ["idle"],
  failure: ["idle"],
  unavailable: ["idle"],
};

export type TransitionReason =
  | "legal_transition"
  | "unknown_state"
  | "illegal_transition"
  | "authenticity_proof_required"
  | "malformed_authenticity_proof";

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
 * Deterministic transition law. Unknown states fail closed; illegal transitions
 * fail closed; entering `installing` from `ready` is refused without an accepted
 * authenticity proof.
 */
export function evaluateTransition(from: unknown, to: unknown, proof?: unknown): TransitionVerdict {
  if (!isUpdateState(from) || !isUpdateState(to)) {
    return { ok: false, reason: "unknown_state" };
  }
  if (!LEGAL_TRANSITIONS[from].includes(to)) {
    return { ok: false, reason: "illegal_transition" };
  }
  if (from === "ready" && to === "installing") {
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

/** States that require an accepted authenticity proof before install can begin. */
export function requiresAuthenticityProof(state: UpdateState): boolean {
  return state === "installing";
}

/** True only for the deterministic, side-effect-free states of this slice. */
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
  readonly error: UpdateError | null;
  readonly events: readonly UpdateEvent[];
}

export type StatusVerdict =
  | { readonly ok: true; readonly status: UpdateStatus }
  | { readonly ok: false; readonly reason: "invalid_status" | "oversized_status" };

/**
 * Validate a status snapshot. Every field is bounded; unknown states, channels,
 * error codes, malformed versions and oversized event lists fail closed.
 */
export function evaluateStatus(input: unknown): StatusVerdict {
  if (typeof input !== "object" || input === null) return { ok: false, reason: "invalid_status" };
  const value = input as Record<string, unknown>;
  if (value.contract !== UPDATE_STATE_CONTRACT) return { ok: false, reason: "invalid_status" };
  if (!isUpdateState(value.state)) return { ok: false, reason: "invalid_status" };
  if (!isReleaseChannel(value.channel)) return { ok: false, reason: "invalid_status" };
  if (!isValidVersion(value.currentVersion)) return { ok: false, reason: "invalid_status" };
  if (value.candidateVersion !== null && !isValidVersion(value.candidateVersion)) {
    return { ok: false, reason: "invalid_status" };
  }
  if (!Array.isArray(value.events)) return { ok: false, reason: "invalid_status" };
  if (value.events.length > MAX_UPDATE_STATUS_EVENTS) return { ok: false, reason: "oversized_status" };
  if (value.error !== null) {
    if (typeof value.error !== "object" || value.error === null) return { ok: false, reason: "invalid_status" };
    const errorValue = value.error as Record<string, unknown>;
    if (!evaluateUpdateError(errorValue.code, errorValue.detail).ok) return { ok: false, reason: "invalid_status" };
  }
  return { ok: true, status: input as UpdateStatus };
}

export function isSafeEventLabel(value: unknown): value is string {
  return typeof value === "string" && value.length <= MAX_UPDATE_EVENT_LABEL_CHARS && SAFE_LABEL_PATTERN.test(value);
}
