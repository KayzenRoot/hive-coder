import { describe, expect, it } from "vitest";

import {
  FORBIDDEN_UPDATE_SERVICE_MEMBERS,
  InertUpdateService,
  UPDATE_SERVICE_BOUNDARY,
  UpdateServiceConfigurationError,
  exposesForbiddenMember,
  type UpdateService,
} from "./updateService";
import { evaluateStatus } from "../contracts/updateState";

/**
 * Test-only stand-in for a future authorised updater.
 *
 * It is defined inside this test file on purpose: it is therefore structurally
 * incapable of being imported by production code, so it can never become
 * production authority. `updateService.contract.test` asserts that its identity
 * appears nowhere outside tests.
 */
class TestOnlyUpdateService implements UpdateService {
  public readonly boundary = UPDATE_SERVICE_BOUNDARY;
  public readonly TEST_ONLY = "hive-test-only-update-service-v1";
  public checkCalls = 0;

  public currentVersion(): string {
    return "0.1.0";
  }

  public currentChannel() {
    return "stable" as const;
  }

  public availability() {
    return { available: true, reason: "not_configured" as const };
  }

  public status() {
    return new InertUpdateService({ currentVersion: "0.1.0" }).status();
  }

  public evaluateCandidate(candidateVersion: unknown) {
    return new InertUpdateService({ currentVersion: "0.1.0" }).evaluateCandidate(candidateVersion);
  }

  public evaluateTransition(from: unknown, to: unknown, proof?: unknown) {
    return new InertUpdateService({ currentVersion: "0.1.0" }).evaluateTransition(from, to, proof);
  }
}

describe("UpdateService boundary", () => {
  it("exposes the fixed boundary identity", () => {
    expect(UPDATE_SERVICE_BOUNDARY).toBe("hive-update-service-v1");
    expect(new InertUpdateService({ currentVersion: "0.1.0" }).boundary).toBe(UPDATE_SERVICE_BOUNDARY);
  });

  it("reports current version and channel as read-only observation", () => {
    const service = new InertUpdateService({ currentVersion: "0.1.0-beta.1", currentChannel: "beta" });
    expect(service.currentVersion()).toBe("0.1.0-beta.1");
    expect(service.currentChannel()).toBe("beta");
  });

  it("defaults to the stable production channel", () => {
    expect(new InertUpdateService({ currentVersion: "0.1.0" }).currentChannel()).toBe("stable");
  });

  it("fails closed on invalid configuration", () => {
    expect(() => new InertUpdateService({ currentVersion: "0.1" })).toThrow(UpdateServiceConfigurationError);
    expect(() => new InertUpdateService({ currentVersion: "0.1.0", currentChannel: "nightly" })).toThrow(
      UpdateServiceConfigurationError,
    );
  });

  it("fails closed when version and channel are independently valid but incompatible", () => {
    // `0.1.0` is a valid version and `beta` is a valid channel; together they are
    // not an identity, because a beta client runs a beta-prerelease version.
    const incompatible: Array<[string, string]> = [
      ["0.1.0", "beta"],
      ["0.1.0", "dev"],
      ["0.1.0-beta.1", "stable"],
      ["0.1.0-beta.1", "dev"],
      ["0.1.0-dev.1", "stable"],
      ["0.1.0-dev.1", "beta"],
    ];
    for (const [currentVersion, currentChannel] of incompatible) {
      expect(
        () => new InertUpdateService({ currentVersion, currentChannel }),
        `${currentVersion}/${currentChannel}`,
      ).toThrow(UpdateServiceConfigurationError);
    }
    expect(() => new InertUpdateService({ currentVersion: "0.1.0", currentChannel: "beta" })).toThrowError(
      /version_channel_mismatch/,
    );
    // The matching pairs are constructed successfully.
    for (const [currentVersion, currentChannel] of [
      ["0.1.0", "stable"],
      ["0.1.0-beta.1", "beta"],
      ["0.1.0-dev.1", "dev"],
    ] as const) {
      const service = new InertUpdateService({ currentVersion, currentChannel });
      expect(service.currentVersion()).toBe(currentVersion);
      expect(service.currentChannel()).toBe(currentChannel);
      expect(evaluateStatus(service.status()).ok).toBe(true);
    }
  });

  it("reports the updater as unavailable in this slice", () => {
    const availability = new InertUpdateService({ currentVersion: "0.1.0" }).availability();
    expect(availability.available).toBe(false);
    expect(availability.reason).toBe("inert_this_slice");
  });

  it("returns a valid bounded status that never claims readiness", () => {
    const status = new InertUpdateService({ currentVersion: "0.1.0" }).status();
    expect(status.state).toBe("unavailable");
    expect(status.candidateVersion).toBeNull();
    expect(status.authenticityProof).toBeNull();
    expect(status.error?.code).toBe("service_inert");
    expect(status.events).toEqual([]);
    // The snapshot the service reports is one the contract accepts.
    expect(evaluateStatus(status)).toMatchObject({ ok: true });
  });

  it("evaluates contract law without mutating anything", () => {
    const service = new InertUpdateService({ currentVersion: "0.1.0" });
    expect(service.evaluateCandidate("0.1.1")).toEqual({ eligible: true, reason: "same_channel_upgrade" });
    expect(service.evaluateCandidate("0.0.9")).toEqual({ eligible: false, reason: "downgrade_not_permitted" });
    expect(service.evaluateCandidate("0.2.0-beta.1")).toEqual({
      eligible: false,
      reason: "prerelease_channel_mismatch",
    });
    // Evaluating does not advance the service's own state.
    expect(service.status().state).toBe("unavailable");
    expect(service.currentVersion()).toBe("0.1.0");
  });

  it("refuses install transitions without an accepted authenticity proof", () => {
    const service = new InertUpdateService({ currentVersion: "0.1.0" });
    expect(service.evaluateTransition("ready", "installing")).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    // The gate sits on the install-ready edge as well, so `ready` itself is
    // unreachable through the service surface.
    expect(service.evaluateTransition("verifying", "ready")).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    expect(service.evaluateTransition("installing", "success")).toEqual({ ok: true, reason: "legal_transition" });
  });

  it("exposes no mutating, transport or installation member", () => {
    const service = new InertUpdateService({ currentVersion: "0.1.0" });
    expect(exposesForbiddenMember(service)).toBeNull();
    for (const forbidden of FORBIDDEN_UPDATE_SERVICE_MEMBERS) {
      expect(forbidden in service, forbidden).toBe(false);
    }
  });

  it("declares a forbidden-member vocabulary that the inert service does not violate", () => {
    expect(FORBIDDEN_UPDATE_SERVICE_MEMBERS.length).toBeGreaterThan(0);
    for (const forbidden of ["check", "download", "install", "restart"]) {
      expect(FORBIDDEN_UPDATE_SERVICE_MEMBERS).toContain(forbidden);
    }
  });

  it("detects a violating service so the guard is not vacuous", () => {
    const violating = {
      check: () => undefined,
      currentVersion: () => "0.1.0",
      currentChannel: () => "stable" as const,
      availability: () => ({ available: true, reason: "not_configured" as const }),
      status: () => new InertUpdateService({ currentVersion: "0.1.0" }).status(),
      evaluateCandidate: () => ({ eligible: false as const, reason: "not_newer" as const }),
      evaluateTransition: () => ({ ok: false as const, reason: "illegal_transition" as const }),
    };
    expect(exposesForbiddenMember(violating)).toBe("check");
  });

  it("keeps the test-only stand-in unreachable from production", () => {
    const standIn = new TestOnlyUpdateService();
    expect(standIn.TEST_ONLY).toBe("hive-test-only-update-service-v1");
    // The stand-in deliberately exposes a forbidden member, which is exactly why
    // it must remain confined to tests.
    expect(standIn.checkCalls).toBe(0);
    expect("checkCalls" in standIn).toBe(true);
    // The production service must not be replaced by it.
    expect(exposesForbiddenMember(new InertUpdateService({ currentVersion: "0.1.0" }))).toBeNull();
  });
});
