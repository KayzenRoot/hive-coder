/**
 * Hive-owned UpdateService boundary (HCODER-WO-0024 / HCODER-DIST-001A).
 *
 * This is the seam that keeps any Tauri updater implementation detail out of
 * core/product logic. Product code depends on this interface, never on an
 * updater plugin, endpoint, HTTP client or installer.
 *
 * Two implementations exist on purpose:
 *
 * - `InertUpdateService` is the deliberately fail-closed DEC-028 boundary. It
 *   performs no network request, download, install, restart, signature check,
 *   release call, process spawn or filesystem mutation, and it is what a build
 *   without a trusted update backend runs on.
 * - `BridgedUpdateService` is the HCODER-WO-0027 / DEC-031 adapter. It forwards
 *   exactly three argument-free operations — read status, check, download and
 *   verify — to a named backend bridge, and it admits nothing else. It still
 *   performs no install, restart, publication or filesystem mutation, and it
 *   accepts no caller-supplied endpoint, key, version, channel, target or
 *   comparator: a snapshot that fails contract law, or that disagrees with this
 *   client's own version/channel identity, is discarded rather than displayed.
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
  "bridge_unreachable",
  "configured",
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
  /**
   * Whether an updater is usable at all in this build. Not the same fact as
   * "the backend answered": a build whose update trust root is absent has a
   * perfectly reachable bridge that must never be reported as usable.
   */
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
 * A service identity is one value, not two independent fields: a version that is
 * individually valid but does not belong to the configured channel is rejected
 * here, because a client that reports `beta` while running `0.1.0` would compute
 * eligibility against the wrong release line.
 */
function admitServiceIdentity(options: UpdateServiceOptions): {
  readonly version: string;
  readonly channel: ReleaseChannel;
} {
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
  return { version: options.currentVersion, channel };
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
    const identity = admitServiceIdentity(options);
    this.#version = identity.version;
    this.#channel = identity.channel;
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
 * The three admitted operations, in the shape product code may depend on. Every
 * one of them is argument-free and answers with a validated snapshot; there is
 * deliberately no install, restart or rollback member.
 */
export interface UpdateAdmissionService extends UpdateService {
  refreshStatus(): Promise<UpdateStatus>;
  checkForUpdate(): Promise<UpdateStatus>;
  downloadUpdateCandidate(): Promise<UpdateStatus>;
}

/**
 * The honest local answer when no trusted snapshot exists: `unavailable`, with
 * no candidate and no proof. `unavailable` is the one state the contract allows
 * to carry an error without having attempted a transition, so a client that
 * never reached its backend says so rather than posing as `idle`.
 */
function unknownTrustSnapshot(currentVersion: string, channel: ReleaseChannel): UpdateStatus {
  const verdict = evaluateStatus({
    contract: UPDATE_STATE_CONTRACT,
    state: "unavailable",
    channel,
    currentVersion,
    candidateVersion: null,
    authenticityProof: null,
    error: { code: "service_unavailable", detail: "no admissible update status was obtained" },
    events: [],
  });
  if (!verdict.ok) {
    // Only a broken identity could make this literal invalid, and the
    // constructor already refused one.
    throw new UpdateServiceConfigurationError("malformed_version");
  }
  return verdict.status;
}

/**
 * The named, argument-free backend operations a trusted update bridge offers.
 *
 * This is an injection seam, not a generic command channel: the three members
 * are fixed, they take no parameters, and the production implementation binds
 * each one to its own literal Tauri command name in `desktopBridge.ts`.
 */
export interface UpdateStatusBridge {
  readUpdateStatus(): Promise<UpdateStatus>;
  requestUpdateCheck(): Promise<UpdateStatus>;
  requestUpdateCandidateDownload(): Promise<UpdateStatus>;
}

export interface BridgedUpdateServiceOptions extends UpdateServiceOptions {
  readonly bridge: UpdateStatusBridge;
}

/**
 * Bounded network-capable adapter (HCODER-WO-0027 / DEC-031).
 *
 * It forwards the three admitted operations and caches the last snapshot the
 * contract accepted. Everything it cannot do is the point: it cannot install,
 * restart, publish or mutate anything, it cannot be told an endpoint, key,
 * version, channel, target or comparator, and it cannot surface a backend
 * snapshot that disagrees with this client's own version/channel identity.
 *
 * A bridge fault is reported as an honest `unavailable` snapshot rather than as
 * a retained stale claim, so an unreachable backend can never be mistaken for a
 * client that is merely idle.
 */
export class BridgedUpdateService implements UpdateAdmissionService {
  public readonly boundary = UPDATE_SERVICE_BOUNDARY;
  readonly #version: string;
  readonly #channel: ReleaseChannel;
  readonly #bridge: UpdateStatusBridge;
  #snapshot: UpdateStatus;
  #bridgeReachable = false;

  public constructor(options: BridgedUpdateServiceOptions) {
    const identity = admitServiceIdentity(options);
    this.#version = identity.version;
    this.#channel = identity.channel;
    this.#bridge = options.bridge;
    this.#snapshot = unknownTrustSnapshot(identity.version, identity.channel);
  }

  public currentVersion(): string {
    return this.#version;
  }

  public currentChannel(): ReleaseChannel {
    return this.#channel;
  }

  /**
   * A reachable bridge and a configured updater are two different facts, and
   * only the second one makes updates usable.
   *
   * The client cannot read the trust root — it is Rust-side configuration and is
   * never named in this file — so the snapshot it was handed is its only
   * evidence. `unavailable` is what a build with no trust root reports, including
   * on a plain status read, which is why the other states may count as
   * configured: the bridge will not grant `idle` unless its own configuration
   * resolved.
   */
  public availability(): UpdateAvailability {
    if (!this.#bridgeReachable) {
      return { available: false, reason: "bridge_unreachable" };
    }
    if (this.#snapshot.state === "unavailable") {
      return { available: false, reason: "not_configured" };
    }
    return { available: true, reason: "configured" };
  }

  public status(): UpdateStatus {
    return this.#snapshot;
  }

  public evaluateCandidate(candidateVersion: unknown): ChannelEligibility {
    return evaluateEligibility(this.#version, candidateVersion, this.#channel);
  }

  public evaluateTransition(from: unknown, to: unknown, proof?: unknown): TransitionVerdict {
    return evaluateTransition(from, to, proof);
  }

  public async refreshStatus(): Promise<UpdateStatus> {
    return this.#admit(this.#bridge.readUpdateStatus());
  }

  public async checkForUpdate(): Promise<UpdateStatus> {
    return this.#admit(this.#bridge.requestUpdateCheck());
  }

  public async downloadUpdateCandidate(): Promise<UpdateStatus> {
    return this.#admit(this.#bridge.requestUpdateCandidateDownload());
  }

  async #admit(call: Promise<UpdateStatus>): Promise<UpdateStatus> {
    const fault = (): UpdateStatus => {
      this.#bridgeReachable = false;
      this.#snapshot = unknownTrustSnapshot(this.#version, this.#channel);
      return this.#snapshot;
    };
    let reported: unknown;
    try {
      reported = await call;
    } catch {
      return fault();
    }
    const verdict = evaluateStatus(reported);
    if (!verdict.ok) {
      return fault();
    }
    // Identity binding: the backend describes this running client, and a
    // snapshot naming another version or channel is not this client's state.
    if (verdict.status.currentVersion !== this.#version || verdict.status.channel !== this.#channel) {
      return fault();
    }
    this.#bridgeReachable = true;
    this.#snapshot = verdict.status;
    return this.#snapshot;
  }
}

/**
 * Structural assertion used by tests and gates: no UpdateService may expose an
 * install, restart, publication or state-advancing member. This is a contract
 * property, not a stylistic one — installation remains behind the separately
 * governed HCODER-DIST-001E authority.
 *
 * `check` and `download` were on this list while the boundary was inert.
 * HCODER-WO-0027 admits them as named, argument-free transport operations on
 * `BridgedUpdateService`, so asserting their absence would now assert the wrong
 * law. `downloadAndInstall` stays forbidden: the compound operation is exactly
 * the install authority this slice withholds.
 */
export const FORBIDDEN_UPDATE_SERVICE_MEMBERS = [
  "checkNow",
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
