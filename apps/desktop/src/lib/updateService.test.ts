import { describe, expect, it } from "vitest";

import {
  BridgedUpdateService,
  FORBIDDEN_UPDATE_SERVICE_MEMBERS,
  InertUpdateService,
  UPDATE_SERVICE_BOUNDARY,
  UpdateServiceConfigurationError,
  exposesForbiddenMember,
  type UpdateStatusBridge,
  type UpdateService,
} from "./updateService";
import {
  ADMITTED_AUTHENTICITY_SCHEMES,
  AUTHENTICITY_PROOF_KEYS,
  UPDATE_STATE_CONTRACT,
  evaluateStatus,
  type UpdateStatus,
} from "../contracts/updateState";

/** The one scheme DEC-031 admits, in the exact shape the Rust bridge emits. */
const ACCEPTED_PROOF = {
  scheme: "tauri-minisign-signed-version-v1",
  artifactSha256: "a".repeat(64),
  metadataSha256: "b".repeat(64),
  verifiedAtEpochMs: 1_700_000_000_000,
} as const;

/** Well formed in every field, refused because its scheme was never admitted. */
const UNADMITTED_PROOF = { ...ACCEPTED_PROOF, scheme: "invented-scheme-v1" } as const;

/**
 * Test-only stand-in for a future authorised updater.
 *
 * It is defined inside this test file on purpose: it is therefore structurally
 * incapable of being imported by production code, so it can never become
 * production authority. It also exposes an install member, which is precisely
 * the shape the forbidden-member guard must refuse.
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
    return { available: true, reason: "configured" as const };
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

  /** Beyond HCODER-DIST-001E authority: present on the stand-in, never on production. */
  public installUpdate() {
    return undefined;
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

  it("refuses installation on the strength of evidence alone", () => {
    const service = new InertUpdateService({ currentVersion: "0.1.0" });
    // Install progress needs the separately governed DIST-001E authority, so no
    // proof — including the one scheme this contract admits — makes those edges
    // legal.
    expect(service.evaluateTransition("ready", "installing")).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
    expect(service.evaluateTransition("ready", "installing", ACCEPTED_PROOF)).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
    expect(service.evaluateTransition("installing", "success", ACCEPTED_PROOF)).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
    // `ready` is the authenticity claim this slice can produce, and it is gated
    // on the proof alone.
    expect(service.evaluateTransition("verifying", "ready")).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    expect(service.evaluateTransition("verifying", "ready", ACCEPTED_PROOF)).toEqual({
      ok: true,
      reason: "legal_transition",
    });
    expect(service.evaluateTransition("downloading", "verifying")).toEqual({ ok: true, reason: "legal_transition" });
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
    // HCODER-WO-0027 admits `check` and `download` as named, argument-free
    // transport operations, so the vocabulary that remains forbidden is exactly
    // the install/restart authority of HCODER-DIST-001E plus the mutating and
    // generic-transport surface.
    for (const forbidden of ["install", "installUpdate", "downloadAndInstall", "restart", "applyUpdate"]) {
      expect(FORBIDDEN_UPDATE_SERVICE_MEMBERS).toContain(forbidden);
    }
    for (const admitted of ["check", "download"]) {
      expect(FORBIDDEN_UPDATE_SERVICE_MEMBERS, admitted).not.toContain(admitted);
    }
  });

  it("detects a violating service so the guard is not vacuous", () => {
    const violating = {
      installUpdate: () => undefined,
      currentVersion: () => "0.1.0",
      currentChannel: () => "stable" as const,
      availability: () => ({ available: true, reason: "not_configured" as const }),
      status: () => new InertUpdateService({ currentVersion: "0.1.0" }).status(),
      evaluateCandidate: () => ({ eligible: false as const, reason: "not_newer" as const }),
      evaluateTransition: () => ({ ok: false as const, reason: "illegal_transition" as const }),
    };
    expect(exposesForbiddenMember(violating)).toBe("installUpdate");
  });

  it("keeps the test-only stand-in unreachable from production", () => {
    const standIn = new TestOnlyUpdateService();
    expect(standIn.TEST_ONLY).toBe("hive-test-only-update-service-v1");
    // The stand-in deliberately exposes an install member, which is exactly why
    // it must remain confined to tests — and why the guard would refuse it.
    expect(exposesForbiddenMember(standIn)).toBe("installUpdate");
    expect(standIn.checkCalls).toBe(0);
    // The production service must not be replaced by it.
    expect(exposesForbiddenMember(new InertUpdateService({ currentVersion: "0.1.0" }))).toBeNull();
  });
});

/**
 * A backend that answers from a fixed table.
 *
 * It cannot reach a network and holds no signing key. So every `ready` snapshot
 * admitted below is this contract's behaviour against a fake authority — it is
 * not, and must not be read as, evidence that a live update path ran.
 */
class FakeUpdateBridge implements UpdateStatusBridge {
  public readonly calls: string[] = [];
  /** When set for an operation, that operation rejects instead of answering. */
  public failures: Partial<Record<keyof UpdateStatusBridge, Error>> = {};
  readonly #replies: Partial<Record<keyof UpdateStatusBridge, unknown>>;

  public constructor(replies: Partial<Record<keyof UpdateStatusBridge, unknown>> = {}) {
    this.#replies = replies;
  }

  public readUpdateStatus(): Promise<UpdateStatus> {
    return this.#reply("readUpdateStatus");
  }

  public requestUpdateCheck(): Promise<UpdateStatus> {
    return this.#reply("requestUpdateCheck");
  }

  public requestUpdateCandidateDownload(): Promise<UpdateStatus> {
    return this.#reply("requestUpdateCandidateDownload");
  }

  async #reply(name: keyof UpdateStatusBridge): Promise<UpdateStatus> {
    this.calls.push(name);
    const failure = this.failures[name];
    if (failure !== undefined) throw failure;
    const reply = this.#replies[name];
    if (reply === undefined) throw new Error(`no ${name} reply configured`);
    // The live bridge receives untyped JSON, so a fixture may be any shape at all;
    // the service's own validation is what decides what becomes product state.
    return reply as UpdateStatus;
  }
}

/** Snapshot-shaped data that lives behind a class prototype, so not a record. */
class SnapshotLike {
  public contract = UPDATE_STATE_CONTRACT;
  public state = "idle";
}

/** A stable-channel snapshot for a `0.1.0` client. */
function snapshot(overrides: Partial<UpdateStatus> = {}): UpdateStatus {
  return {
    contract: UPDATE_STATE_CONTRACT,
    state: "idle",
    channel: "stable",
    currentVersion: "0.1.0",
    candidateVersion: null,
    authenticityProof: null,
    error: null,
    events: [],
    ...overrides,
  };
}

function bridged(replies: Partial<Record<keyof UpdateStatusBridge, unknown>> = {}) {
  const bridge = new FakeUpdateBridge(replies);
  const service = new BridgedUpdateService({ bridge, currentVersion: "0.1.0" });
  return { bridge, service };
}

/** The snapshot a service reports when it cannot stand behind what it received. */
const HONEST_FAULT = {
  state: "unavailable",
  candidateVersion: null,
  authenticityProof: null,
  error: { code: "service_unavailable" },
  events: [],
} as const;

describe("BridgedUpdateService", () => {
  it("admits exactly the scheme DEC-031 names", () => {
    expect(ADMITTED_AUTHENTICITY_SCHEMES).toEqual([ACCEPTED_PROOF.scheme]);
    expect(UNADMITTED_PROOF.scheme).not.toBe(ACCEPTED_PROOF.scheme);
  });

  it("says so when it has never reached its backend", () => {
    const { bridge, service } = bridged();
    expect(bridge.calls).toEqual([]);
    expect(service.status().state).toBe("unavailable");
    expect(service.availability()).toEqual({ available: false, reason: "bridge_unreachable" });
    // The pre-call snapshot is still one the contract accepts, and it does not
    // pose as `idle`: nothing was checked, so nothing may be claimed about releases.
    expect(evaluateStatus(service.status()).ok).toBe(true);
    expect(service.status().error?.code).toBe("service_unavailable");
  });

  it("fails closed on an incomplete identity like the inert service does", () => {
    expect(() => new BridgedUpdateService({ bridge: new FakeUpdateBridge(), currentVersion: "0.1.0", currentChannel: "beta" })).toThrow(
      UpdateServiceConfigurationError,
    );
  });

  it("admits a valid snapshot and caches it as the reported state", async () => {
    const { service } = bridged({ readUpdateStatus: snapshot({ state: "available", candidateVersion: "0.2.0" }) });
    const admitted = await service.refreshStatus();
    expect(admitted.state).toBe("available");
    expect(admitted.candidateVersion).toBe("0.2.0");
    expect(service.status()).toEqual(admitted);
    expect(service.availability()).toEqual({ available: true, reason: "configured" });
  });

  it("reports a reachable bridge and a configured updater as separate facts", async () => {
    // The shape a build with no updater trust root answers with, including on a
    // plain status read that attempted nothing. The bridge answered, so it is
    // reachable; nothing about that makes an updater usable.
    const inert = bridged({
      readUpdateStatus: snapshot({
        state: "unavailable",
        error: { code: "service_unavailable", detail: "the updater has no trusted public key and endpoint configured" },
      }),
    });
    expect((await inert.service.refreshStatus()).state).toBe("unavailable");
    expect(inert.service.availability()).toEqual({ available: false, reason: "not_configured" });

    // Every remaining state is one the bridge only grants after its own trusted
    // configuration resolved, so each of them evidences a configured updater.
    for (const state of ["idle", "checking", "available", "ready", "failure"] as const) {
      const { service } = bridged({
        readUpdateStatus: snapshot({
          state,
          candidateVersion: state === "available" || state === "ready" ? "0.2.0" : null,
          authenticityProof: state === "ready" ? ACCEPTED_PROOF : null,
          error: state === "failure" ? { code: "download_failed", detail: "the candidate download failed" } : null,
        }),
      });
      expect((await service.refreshStatus()).state, state).toBe(state);
      expect(service.availability(), state).toEqual({ available: true, reason: "configured" });
    }
  });

  it("keeps a configured updater configured when a remote check fails", async () => {
    const { service } = bridged({
      requestUpdateCheck: snapshot({
        state: "failure",
        error: { code: "service_unavailable", detail: "update service is unreachable" },
      }),
    });

    const failed = await service.checkForUpdate();
    expect(failed.state).toBe("failure");
    expect(failed.error?.code).toBe("service_unavailable");
    // The bridge answered and the build's trust configuration resolved. An
    // endpoint outage is a check failure, not a missing updater configuration.
    expect(service.availability()).toEqual({ available: true, reason: "configured" });
  });

  it("reports the shipped build as reachable and unusable on its first read", async () => {
    // Before any call there is no evidence either way, so nothing is claimed.
    const { bridge, service } = bridged({ readUpdateStatus: snapshot({ state: "unavailable" }) });
    expect(service.availability()).toEqual({ available: false, reason: "bridge_unreachable" });
    await service.refreshStatus();
    expect(bridge.calls).toEqual(["readUpdateStatus"]);
    expect(service.availability().available).toBe(false);
  });

  it("routes each operation to exactly one named backend call", async () => {
    const { bridge, service } = bridged({
      readUpdateStatus: snapshot(),
      requestUpdateCheck: snapshot({ state: "available", candidateVersion: "0.2.0" }),
      requestUpdateCandidateDownload: snapshot({ state: "verifying", candidateVersion: "0.2.0" }),
    });
    await service.refreshStatus();
    expect(bridge.calls).toEqual(["readUpdateStatus"]);
    await service.checkForUpdate();
    expect(bridge.calls).toEqual(["readUpdateStatus", "requestUpdateCheck"]);
    await service.downloadUpdateCandidate();
    expect(bridge.calls).toEqual(["readUpdateStatus", "requestUpdateCheck", "requestUpdateCandidateDownload"]);
  });

  it("exposes three argument-free operations and nothing else", () => {
    const { service } = bridged();
    for (const operation of ["refreshStatus", "checkForUpdate", "downloadUpdateCandidate"] as const) {
      expect(service[operation].length, operation).toBe(0);
    }
    expect(exposesForbiddenMember(service)).toBeNull();
    for (const forbidden of FORBIDDEN_UPDATE_SERVICE_MEMBERS) {
      expect(forbidden in service, forbidden).toBe(false);
    }
    expect(service.boundary).toBe(UPDATE_SERVICE_BOUNDARY);
  });

  it("admits the install-ready claim only with the accepted proof", async () => {
    const ready = { state: "ready", candidateVersion: "0.2.0", authenticityProof: ACCEPTED_PROOF } as const;
    const admitted = await bridged({ requestUpdateCandidateDownload: snapshot(ready) }).service.downloadUpdateCandidate();
    expect(admitted.state).toBe("ready");
    expect(admitted.authenticityProof).toEqual(ACCEPTED_PROOF);

    // The same snapshot, but the proof's scheme was never admitted.
    const unadmitted = await bridged({
      requestUpdateCandidateDownload: snapshot({ ...ready, authenticityProof: UNADMITTED_PROOF }),
    }).service.downloadUpdateCandidate();
    expect(unadmitted).toMatchObject(HONEST_FAULT);

    // And with no proof at all, which is the claim DEC-028 refuses.
    const bare = await bridged({
      requestUpdateCandidateDownload: snapshot({ ...ready, authenticityProof: null }),
    }).service.downloadUpdateCandidate();
    expect(bare).toMatchObject(HONEST_FAULT);
  });

  it("never lets install progress enter product state, whatever the backend claims", async () => {
    for (const state of ["installing", "success"] as const) {
      const { service } = bridged({
        readUpdateStatus: snapshot({
          state,
          candidateVersion: "0.2.0",
          authenticityProof: ACCEPTED_PROOF,
        }),
      });
      expect(await service.refreshStatus()).toMatchObject(HONEST_FAULT);
      expect(service.status().state).toBe("unavailable");
    }
  });

  it("refuses a snapshot that describes a different client", async () => {
    const cases: Array<[string, UpdateStatus]> = [
      ["another version", snapshot({ currentVersion: "9.9.9" })],
      ["another channel", snapshot({ channel: "beta", currentVersion: "0.1.0-beta.1" })],
      ["a beta release line", snapshot({ state: "available", candidateVersion: "0.2.0-beta.1", channel: "beta", currentVersion: "0.1.0-beta.1" })],
    ];
    for (const [name, reply] of cases) {
      const { service } = bridged({ requestUpdateCheck: reply });
      expect(await service.checkForUpdate(), name).toMatchObject(HONEST_FAULT);
      expect(service.availability().available, name).toBe(false);
    }
  });

  it("discards untrusted wire payloads rather than partially reading them", async () => {
    // Any key outside the admitted snapshot set is unreviewed material riding
    // along with a nominally valid snapshot, so the whole payload is refused.
    for (const key of ["url", "signature", "notAContractKey"]) {
      const payload = { ...snapshot({ state: "available", candidateVersion: "0.2.0" }), [key]: "untrusted" };
      const { service } = bridged({ readUpdateStatus: payload });
      expect(await service.refreshStatus(), key).toMatchObject(HONEST_FAULT);
    }
    for (const payload of [null, "idle", 7, [], {}, new SnapshotLike()]) {
      const { service } = bridged({ readUpdateStatus: payload });
      expect(await service.refreshStatus(), String(payload)).toMatchObject(HONEST_FAULT);
    }
  });

  it("replaces a cached claim with an honest fault when the backend goes away", async () => {
    const backend = new FakeUpdateBridge({ readUpdateStatus: snapshot({ state: "available", candidateVersion: "0.2.0" }) });
    const service = new BridgedUpdateService({ bridge: backend, currentVersion: "0.1.0" });
    expect((await service.refreshStatus()).state).toBe("available");
    expect(service.availability().available).toBe(true);
    backend.failures.readUpdateStatus = new Error("transport closed");
    expect(await service.refreshStatus()).toMatchObject(HONEST_FAULT);
    expect(service.status().state).toBe("unavailable");
    expect(service.status().candidateVersion).toBeNull();
    expect(service.availability()).toEqual({ available: false, reason: "bridge_unreachable" });
  });

  it("evaluates contract law without touching the backend at all", async () => {
    const { bridge, service } = bridged();
    expect(service.evaluateCandidate("0.1.1")).toEqual({ eligible: true, reason: "same_channel_upgrade" });
    expect(service.evaluateCandidate("0.0.9")).toEqual({ eligible: false, reason: "downgrade_not_permitted" });
    expect(service.evaluateTransition("ready", "installing", ACCEPTED_PROOF)).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
    expect(service.evaluateTransition("verifying", "ready", ACCEPTED_PROOF)).toEqual({
      ok: true,
      reason: "legal_transition",
    });
    expect(bridge.calls).toEqual([]);
    expect(service.status().state).toBe("unavailable");
  });

  it("reports a proof-bearing snapshot without leaking its material into identity", async () => {
    const { service } = bridged({
      readUpdateStatus: snapshot({ state: "ready", candidateVersion: "0.2.0", authenticityProof: ACCEPTED_PROOF }),
    });
    const admitted = await service.refreshStatus();
    // The canonical reconstruction keeps exactly the four proof keys.
    expect(Object.keys(admitted.authenticityProof ?? {}).sort()).toEqual([...AUTHENTICITY_PROOF_KEYS].sort());
    // A proof is evidence of authenticity, never authority to mutate: the service
    // surface is unchanged by holding one.
    expect(exposesForbiddenMember(service)).toBeNull();
    expect(service.evaluateTransition("ready", "installing", admitted.authenticityProof)).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
  });
});
