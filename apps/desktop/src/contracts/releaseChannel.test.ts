import { describe, expect, it } from "vitest";

import {
  CHANNEL_PRODUCT_LABEL,
  DEFAULT_RELEASE_CHANNEL,
  DEV_CHANNEL,
  RELEASE_CHANNELS,
  STABLE_CHANNEL,
  evaluateCrossChannel,
  evaluateEligibility,
  isReleaseChannel,
  versionMatchesChannel,
} from "./releaseChannel";
import { isValidVersion } from "./version";

describe("release channel contract", () => {
  it("defines exactly the governed channels with stable as production default", () => {
    expect(RELEASE_CHANNELS).toEqual(["stable", "beta", "dev"]);
    expect(DEFAULT_RELEASE_CHANNEL).toBe("stable");
  });

  it("maps machine values losslessly to product labels", () => {
    expect(CHANNEL_PRODUCT_LABEL.stable).toBe("stable");
    expect(CHANNEL_PRODUCT_LABEL.beta).toBe("beta");
    expect(CHANNEL_PRODUCT_LABEL.dev).toBe("dev/internal");
    expect(Object.keys(CHANNEL_PRODUCT_LABEL)).toEqual([...RELEASE_CHANNELS]);
  });

  it("fails closed on unknown channel values", () => {
    for (const value of ["", "stable ", "STABLE", "nightly", "internal", null, undefined, 3, {}]) {
      expect(isReleaseChannel(value)).toBe(false);
      expect(evaluateEligibility("1.0.0", "1.1.0", value)).toEqual({ eligible: false, reason: "unknown_channel" });
    }
  });

  it("matches version shape to channel and rejects malformed versions", () => {
    expect(versionMatchesChannel("1.0.0", "stable")).toBe(true);
    expect(versionMatchesChannel("1.0.0-beta.1", "beta")).toBe(true);
    expect(versionMatchesChannel("1.0.0-dev.3", "dev")).toBe(true);
    expect(versionMatchesChannel("1.0.0-beta.1+build.9", "beta")).toBe(true);

    expect(versionMatchesChannel("1.0.0-beta.1", "stable")).toBe(false);
    expect(versionMatchesChannel("1.0.0", "beta")).toBe(false);
    expect(versionMatchesChannel("1.0.0-beta.1", "dev")).toBe(false);
    expect(versionMatchesChannel("not-a-version", "stable")).toBe(false);
    expect(versionMatchesChannel("1.0.0", "nightly")).toBe(false);
  });

  it("derives channel shape from the canonical strict parser only", () => {
    // Each of these carries a channel-looking prerelease prefix but is not valid
    // SemVer. A second, looser shape parser in this module would accept them and
    // report a malformed version as belonging to the beta channel.
    const malformedBetaShaped = [
      "1.0.0-beta.",
      "1.0.0-beta..1",
      "1.0.0-beta.01",
      "1.0.0-beta.1.",
      "1.0.0-beta+",
      "1.0.0-",
      "1.0.0-+x",
      "01.0.0-beta.1",
      "1.0-beta.1",
      "1.0.0-beta.β",
      "1.0.0 -beta.1",
    ];
    for (const version of malformedBetaShaped) {
      expect(isValidVersion(version), version).toBe(false);
      expect(versionMatchesChannel(version, "beta"), version).toBe(false);
      expect(versionMatchesChannel(version, "dev"), version).toBe(false);
      expect(versionMatchesChannel(version, "stable"), version).toBe(false);
      expect(evaluateEligibility(version, "2.0.0-beta.1", "beta"), version).toEqual({
        eligible: false,
        reason: "malformed_version",
      });
    }
    // The same check in the opposite direction: dev-shaped malformed versions.
    expect(versionMatchesChannel("1.0.0-dev.1.", "dev")).toBe(false);
    expect(versionMatchesChannel("1.0.0-dev..1", "dev")).toBe(false);
    expect(isValidVersion("1.0.0-dev.1.")).toBe(false);
    expect(isValidVersion("1.0.0-dev..1")).toBe(false);
    // A valid version whose prefix differs only by case is not a channel match.
    expect(isValidVersion("1.0.0-BETA.1")).toBe(true);
    expect(versionMatchesChannel("1.0.0-BETA.1", "beta")).toBe(false);
  });

  it("allows only a strictly newer same-channel upgrade", () => {
    expect(evaluateEligibility("0.1.0", "0.1.1", "stable")).toEqual({
      eligible: true,
      reason: "same_channel_upgrade",
    });
    expect(evaluateEligibility("1.0.0-beta.1", "1.0.0-beta.2", "beta")).toEqual({
      eligible: true,
      reason: "same_channel_upgrade",
    });
  });

  it("refuses a downgrade or an identical version", () => {
    expect(evaluateEligibility("1.0.0", "0.9.0", "stable")).toEqual({
      eligible: false,
      reason: "downgrade_not_permitted",
    });
    expect(evaluateEligibility("1.0.0", "1.0.0", "stable")).toEqual({ eligible: false, reason: "not_newer" });
  });

  it("refuses a numerically newer version that does not belong to the channel", () => {
    // A newer prerelease must never be offered as a stable upgrade.
    expect(evaluateEligibility("1.0.0", "2.0.0-beta.1", "stable")).toEqual({
      eligible: false,
      reason: "prerelease_channel_mismatch",
    });
    // Nor may a release version be offered on a prerelease channel.
    expect(evaluateEligibility("1.0.0-beta.1", "2.0.0", "beta")).toEqual({
      eligible: false,
      reason: "prerelease_channel_mismatch",
    });
  });

  it("refuses a client whose current version does not belong to the channel", () => {
    expect(evaluateEligibility("1.0.0-beta.1", "1.0.0-beta.2", "stable")).toEqual({
      eligible: false,
      reason: "cross_channel_not_permitted",
    });
  });

  it("fails closed on malformed versions in eligibility evaluation", () => {
    expect(evaluateEligibility("0.1", "0.2.0", "stable")).toEqual({ eligible: false, reason: "malformed_version" });
    expect(evaluateEligibility("0.1.0", "0.2", "stable")).toEqual({ eligible: false, reason: "malformed_version" });
  });

  it("never performs an implicit cross-channel promotion or demotion", () => {
    for (const from of RELEASE_CHANNELS) {
      for (const to of RELEASE_CHANNELS) {
        if (from === to) continue;
        expect(evaluateCrossChannel(from, to)).toEqual({
          permitted: false,
          reason: "cross_channel_not_permitted",
          requiresGovernedDecision: true,
        });
      }
    }
    expect(evaluateCrossChannel(STABLE_CHANNEL, "nightly")).toEqual({ permitted: false, reason: "unknown_channel" });
    expect(evaluateCrossChannel(DEV_CHANNEL, STABLE_CHANNEL).permitted).toBe(false);
  });

  it("exposes no channel whose constant is not in the channel list", () => {
    const exported = [STABLE_CHANNEL, DEV_CHANNEL];
    for (const channel of exported) {
      expect(RELEASE_CHANNELS).toContain(channel);
    }
  });
});
