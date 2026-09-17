/**
 * Release-channel contract (HCODER-WO-0024 / HCODER-DIST-001A).
 *
 * Machine values map losslessly to product semantics. `dev` carries the product
 * label "dev/internal"; the machine value is deliberately short and
 * filename/URL-safe so it can be used in artifact names and metadata without
 * escaping.
 *
 * Pure contract logic only: no network, no installer, no side effect.
 */

import { compareVersions, isStrictlyNewer, parseVersion } from "./version";

export const CHANNEL_CONTRACT = "hive-release-channel-v1" as const;

export const STABLE_CHANNEL = "stable" as const;
export const BETA_CHANNEL = "beta" as const;
export const DEV_CHANNEL = "dev" as const;

export type ReleaseChannel = typeof STABLE_CHANNEL | typeof BETA_CHANNEL | typeof DEV_CHANNEL;

export const RELEASE_CHANNELS = [STABLE_CHANNEL, BETA_CHANNEL, DEV_CHANNEL] as const;

/** Stable is the default production channel. */
export const DEFAULT_RELEASE_CHANNEL: ReleaseChannel = STABLE_CHANNEL;

/** Prerelease prefix required for a version to belong to the channel. */
export const CHANNEL_PRERELEASE_PREFIX: Readonly<Record<ReleaseChannel, string | null>> = {
  stable: null,
  beta: "beta",
  dev: "dev",
};

/** Product-facing labels. `dev` is the machine value for "dev/internal". */
export const CHANNEL_PRODUCT_LABEL: Readonly<Record<ReleaseChannel, string>> = {
  stable: "stable",
  beta: "beta",
  dev: "dev/internal",
};

/**
 * Relative maturity ordering. Higher is more production-facing. This ordering is
 * intentionally *not* a licence to promote or demote across channels; it exists
 * only to reason about explicit user-visible channel selection.
 */
export const CHANNEL_RANK: Readonly<Record<ReleaseChannel, number>> = {
  dev: 1,
  beta: 2,
  stable: 3,
};

export function isReleaseChannel(value: unknown): value is ReleaseChannel {
  return typeof value === "string" && (RELEASE_CHANNELS as readonly string[]).includes(value);
}

export type EligibilityReason =
  | "same_channel_upgrade"
  | "unknown_channel"
  | "malformed_version"
  | "not_newer"
  | "downgrade_not_permitted"
  | "cross_channel_not_permitted"
  | "prerelease_channel_mismatch";

export type ChannelEligibility =
  | { readonly eligible: true; readonly reason: "same_channel_upgrade" }
  | { readonly eligible: false; readonly reason: Exclude<EligibilityReason, "same_channel_upgrade"> };

const REFUSED = (reason: Exclude<EligibilityReason, "same_channel_upgrade">): ChannelEligibility => ({
  eligible: false,
  reason,
});

/**
 * Does this version shape belong to this channel?
 *
 * `stable` admits only fully released versions with no prerelease component.
 * `beta` and `dev` admit only versions whose first prerelease identifier equals
 * the channel's prefix. This is a *shape* test, not a promotion authorisation.
 *
 * The shape is derived exclusively from the canonical strict SemVer parser in
 * `version.ts`. A second, looser pattern here would let a version that the strict
 * contract refuses — an empty prerelease identifier such as `1.0.0-beta.`, for
 * instance — satisfy the channel-prefix test, so this function has no parser of
 * its own: malformed input never matches any channel.
 */
export function versionMatchesChannel(version: unknown, channel: unknown): boolean {
  if (!isReleaseChannel(channel)) return false;
  const prefix = CHANNEL_PRERELEASE_PREFIX[channel];
  const parsed = parseVersion(version);
  if (!parsed.ok) return false;
  const prerelease = parsed.version.prerelease;
  if (prefix === null) return prerelease === null;
  return prerelease !== null && prerelease[0] === prefix;
}

/**
 * Deterministic eligibility law for moving from `current` to `candidate` on the
 * same channel. There is deliberately no cross-channel path in this slice:
 * a channel change is a governed decision, never an implicit upgrade side effect.
 */
export function evaluateEligibility(
  current: unknown,
  candidate: unknown,
  channel: unknown,
): ChannelEligibility {
  if (!isReleaseChannel(channel)) return REFUSED("unknown_channel");
  const comparison = compareVersions(candidate, current);
  if (comparison === null) return REFUSED("malformed_version");
  if (!versionMatchesChannel(current, channel)) return REFUSED("cross_channel_not_permitted");
  if (!versionMatchesChannel(candidate, channel)) return REFUSED("prerelease_channel_mismatch");
  if (comparison === 0) return REFUSED("not_newer");
  if (comparison < 0) return REFUSED("downgrade_not_permitted");
  if (!isStrictlyNewer(candidate, current)) return REFUSED("not_newer");
  return { eligible: true, reason: "same_channel_upgrade" };
}

/**
 * Explicit cross-channel intent. Even when requested deliberately, this slice
 * refuses to move a client between channels; it reports the required governed
 * decision instead of performing an implicit promotion or demotion.
 */
export type CrossChannelVerdict =
  | { readonly permitted: false; readonly reason: "cross_channel_not_permitted"; readonly requiresGovernedDecision: true }
  | { readonly permitted: false; readonly reason: "unknown_channel" };

export function evaluateCrossChannel(from: unknown, to: unknown): CrossChannelVerdict {
  if (!isReleaseChannel(from) || !isReleaseChannel(to)) {
    return { permitted: false, reason: "unknown_channel" };
  }
  return { permitted: false, reason: "cross_channel_not_permitted", requiresGovernedDecision: true };
}
