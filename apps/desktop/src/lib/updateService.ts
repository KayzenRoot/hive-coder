/**
 * Hive-owned UpdateService boundary (HCODER-WO-0024 / HCODER-DIST-001A).
 *
 * This is the seam that keeps any future Tauri updater implementation detail out
 * of core/product logic. Product code depends on this interface, never on an
 * updater plugin, endpoint, HTTP client or installer.
 *
 * The production implementation here is deliberately INERT and fail-closed: it
 * can report the current version and channel and evaluate pure contract law, and
 * it can do nothing else. It performs no network request, download, install,
 * restart, signature check, release call, process spawn or filesystem mutation.
 */

import {
  DEFAULT_RELEASE_CHANNEL,
  evaluateEligibility,
  isReleaseChannel,
  versionMatchesChannel,
  type ChannelEligibility,
  type ReleaseChannel,
} from "../contracts/releaseChannel";
import {
  UPDATE_STATE_CONTRACT,
  evaluateStatus,
  evaluateTransition,
  isUpdateState,
  type TransitionVerdict,
  type UpdateStatus,
} from "../contracts/updateState";
import { isValidVersion } from "../contracts/version";

export const UPDATE_SERVICE_BOUNDARY = "hive-update-service-v1" as const;

/** Why the updater is or is not usable. Bounded vocabulary. */
export const UPDATE_AVAILABILITY_REASONS = [
  "inert_this_slice",
  "not_configured",
  "unsupported_platform",
] as const;

export type UpdateAvailabilityReason = (typeof UPDATE_AVAILABILITY_REASONS)[number];

export interface UpdateAvailability {
  readonly available: boolean;
  readonly reason: UpdateAvailabilityReason;
}

export interface UpdateService {
  readonly boundary: typeof UPDATE_SERVICE_BOUNDARY;
  /** Current product version. Read-only observation. */
  currentVersion(): string;
  /** Current release channel. Read-only observation. */
  currentChannel(): ReleaseChannel;
  /** Whether an updater is usable at all in this build. */
  availability(): UpdateAvailability;
  /** Bounded, redaction-safe status snapshot. */
  status(): UpdateStatus;
  /**
   * Pure contract evaluation of a candidate against the installed state.
   * No side effect: it neither fetches nor records anything.
   */
  evaluateCandidate(candidateVersion: unknown): ChannelEligibility;
  /**
   * Validate a proposed state transition against contract law. Evaluation only;
   * the service never advances its own state.
   */
  evaluateTransition(from: unknown, to: unknown, proof?: unknown): TransitionVerdict;
}

export interface UpdateServiceOptions {
  readonly currentVersion: string;
  readonly currentChannel?: unknown;
}

export type UpdateServiceConfigurationErrorCode =
  | "malformed_version"
  | "unknown_channel"
  | "version_channel_mismatch";

export class UpdateServiceConfigurationError extends Error {
  public readonly code: UpdateServiceConfigurationErrorCode;

  public constructor(code: UpdateServiceConfigurationErrorCode) {
    super(`update service configuration rejected: ${code}`);
    this.name = "UpdateServiceConfigurationError";
    this.code = code;
  }
}

/**
 * Inert production UpdateService.
 *
 * It reports immutable configuration, evaluates contract law, and exposes no
 * mutation, transport or installation path whatsoever. `availability()` always
 * reports unavailable in this slice.
 *
 * Configuration is a single identity, not two independent fields: a version that
 * is individually valid but does not belong to the configured channel is
 * rejected at construction, because a client that reports `beta` while running
 * `0.1.0` would compute eligibility against the wrong release line.
 */
export class InertUpdateService implements UpdateService {
  public readonly boundary = UPDATE_SERVICE_BOUNDARY;
  readonly #version: string;
  readonly #channel: ReleaseChannel;

  public constructor(options: UpdateServiceOptions) {
    if (!isValidVersion(options.currentVersion)) {
      throw new UpdateServiceConfigurationError("malformed_version");
    }
    const channel = options.currentChannel ?? DEFAULT_RELEASE_CHANNEL;
    if (!isReleaseChannel(channel)) {
      throw new UpdateServiceConfigurationError("unknown_channel");
    }
    if (!versionMatchesChannel(options.currentVersion, channel)) {
      throw new UpdateServiceConfigurationError("version_channel_mismatch");
    }
    this.#version = options.currentVersion;
    this.#channel = channel;
  }

  public currentVersion(): string {
    return this.#version;
  }

  public currentChannel(): ReleaseChannel {
    return this.#channel;
  }

  public availability(): UpdateAvailability {
    return { available: false, reason: "inert_this_slice" };
  }

  public status(): UpdateStatus {
    const snapshot: UpdateStatus = {
      contract: UPDATE_STATE_CONTRACT,
      state: "unavailable",
      channel: this.#channel,
      currentVersion: this.#version,
      candidateVersion: null,
      authenticityProof: null,
      error: { code: "service_inert", detail: "updater is not enabled in this build" },
      events: [],
    };
    const verdict = evaluateStatus(snapshot);
    if (!verdict.ok) {
      // A malformed snapshot must never reach product state.
      throw new UpdateServiceConfigurationError("malformed_version");
    }
    // The validated canonical object is returned, not the hand-built literal.
    return verdict.status;
  }

  public evaluateCandidate(candidateVersion: unknown): ChannelEligibility {
    return evaluateEligibility(this.#version, candidateVersion, this.#channel);
  }

  public evaluateTransition(from: unknown, to: unknown, proof?: unknown): TransitionVerdict {
    return evaluateTransition(from, to, proof);
  }
}

/**
 * Structural assertion used by tests and gates: the inert service exposes no
 * mutating, transport or installation member. This is a contract property, not a
 * stylistic one — a future authorised updater must arrive through a governed
 * Work Order that widens this boundary explicitly.
 */
export const FORBIDDEN_UPDATE_SERVICE_MEMBERS = [
  "check",
  "checkNow",
  "download",
  "downloadAndInstall",
  "install",
  "installUpdate",
  "restart",
  "applyUpdate",
  "fetch",
  "request",
  "sign",
  "publish",
  "record",
  "advance",
  "mutate",
] as const;

export function exposesForbiddenMember(candidate: object): string | null {
  for (const member of FORBIDDEN_UPDATE_SERVICE_MEMBERS) {
    if (member in candidate) return member;
  }
  return null;
}

export function isUpdateStateName(value: unknown): boolean {
  return isUpdateState(value);
}
