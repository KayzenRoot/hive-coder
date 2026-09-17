import { describe, expect, it } from "vitest";

import { ABOUT_READ_MODEL_SCHEMA, MAX_ABOUT_PRODUCT_NAME_CHARS, buildAboutReadModel } from "./aboutReadModel";
import { UPDATE_STATE_CONTRACT } from "./updateState";

function status(overrides: Record<string, unknown> = {}) {
  return {
    contract: UPDATE_STATE_CONTRACT,
    state: "unavailable",
    channel: "stable",
    currentVersion: "0.1.0",
    candidateVersion: null,
    authenticityProof: null,
    error: { code: "service_inert", detail: "updater is not enabled in this build" },
    events: [],
    ...overrides,
  };
}

function input(overrides: Record<string, unknown> = {}) {
  return { productName: "Hive Coder", version: "0.1.0", channel: "stable", status: status(), ...overrides };
}

describe("about read model", () => {
  it("builds a bounded, read-only model from valid input", () => {
    const verdict = buildAboutReadModel(input());
    expect(verdict.ok).toBe(true);
    if (!verdict.ok) return;
    expect(verdict.model.schema).toBe(ABOUT_READ_MODEL_SCHEMA);
    expect(verdict.model.productName).toBe("Hive Coder");
    expect(verdict.model.version).toBe("0.1.0");
    expect(verdict.model.channel).toBe("stable");
    expect(verdict.model.channelLabel).toBe("stable");
    expect(verdict.model.update.available).toBe(false);
    expect(verdict.model.update.state).toBe("unavailable");
  });

  it("labels the dev channel truthfully as dev/internal", () => {
    const verdict = buildAboutReadModel(
      input({
        version: "1.0.0-dev.1",
        channel: "dev",
        status: status({ channel: "dev", currentVersion: "1.0.0-dev.1" }),
      }),
    );
    expect(verdict.ok).toBe(true);
    if (!verdict.ok) return;
    expect(verdict.model.channelLabel).toBe("dev/internal");
    expect(verdict.model.version).toBe("1.0.0-dev.1");
  });

  it("requires the displayed version to belong to the displayed channel", () => {
    // Individually valid, mutually incompatible: `0.1.0` is not a beta version.
    expect(buildAboutReadModel(input({ version: "0.1.0", channel: "beta", status: status({ channel: "beta", currentVersion: "0.1.0" }) }))).toEqual({
      ok: false,
      reason: "invalid_about_model",
    });
    expect(
      buildAboutReadModel(input({ version: "0.1.0-beta.1", channel: "beta", status: status({ channel: "beta", currentVersion: "0.1.0-beta.1" }) })).ok,
    ).toBe(true);
    expect(buildAboutReadModel(input({ version: "0.1.0-beta.1", channel: "stable" }))).toEqual({
      ok: false,
      reason: "invalid_about_model",
    });
  });

  it("requires the read model to agree with the validated status snapshot", () => {
    // Version contradiction.
    expect(buildAboutReadModel(input({ version: "0.2.0" }))).toEqual({ ok: false, reason: "invalid_about_model" });
    // Channel contradiction: the status itself is valid, but it disagrees here.
    expect(
      buildAboutReadModel(
        input({
          version: "0.1.0-beta.1",
          channel: "beta",
          status: status({ channel: "dev", currentVersion: "0.1.0-dev.1" }),
        }),
      ),
    ).toEqual({ ok: false, reason: "invalid_about_model" });
    // A status the identity law rejects can never produce an about model.
    expect(buildAboutReadModel(input({ status: status({ channel: "beta", currentVersion: "0.1.0" }) }))).toEqual({
      ok: false,
      reason: "invalid_about_model",
    });
    // Proof material outside an install-ready state is refused upstream.
    expect(
      buildAboutReadModel(
        input({
          status: status({
            authenticityProof: { scheme: "invented-scheme-v1", artifactSha256: "a".repeat(64), metadataSha256: "a".repeat(64), verifiedAtEpochMs: 1 },
          }),
        }),
      ),
    ).toEqual({ ok: false, reason: "invalid_about_model" });
    // A status claiming an install-ready state is refused upstream.
    expect(
      buildAboutReadModel(input({ status: status({ state: "ready", candidateVersion: "0.2.0", error: null }) })),
    ).toEqual({ ok: false, reason: "invalid_about_model" });
  });

  it("fails closed on an unknown channel", () => {
    for (const channel of ["nightly", "STABLE", "", null, 3]) {
      expect(buildAboutReadModel(input({ channel }))).toEqual({ ok: false, reason: "invalid_about_model" });
    }
  });

  it("fails closed on a malformed or oversized product name", () => {
    expect(buildAboutReadModel(input({ productName: "" }))).toEqual({ ok: false, reason: "invalid_about_model" });
    expect(buildAboutReadModel(input({ productName: "x".repeat(MAX_ABOUT_PRODUCT_NAME_CHARS + 1) }))).toEqual({
      ok: false,
      reason: "invalid_about_model",
    });
    expect(buildAboutReadModel(input({ productName: 7 }))).toEqual({ ok: false, reason: "invalid_about_model" });
  });

  it("fails closed on a malformed version or status", () => {
    expect(buildAboutReadModel(input({ version: "0.1" }))).toEqual({ ok: false, reason: "invalid_about_model" });
    expect(buildAboutReadModel(input({ status: null }))).toEqual({ ok: false, reason: "invalid_about_model" });
    expect(buildAboutReadModel(input({ status: status({ state: "bogus" }) }))).toEqual({
      ok: false,
      reason: "invalid_about_model",
    });
  });

  it("never reports the updater as available in this slice", () => {
    const verdict = buildAboutReadModel(input());
    expect(verdict.ok).toBe(true);
    if (!verdict.ok) return;
    expect(verdict.model.update.available).toBe(false);
  });

  it("carries no authority or side-effect surface", () => {
    const verdict = buildAboutReadModel(input());
    expect(verdict.ok).toBe(true);
    if (!verdict.ok) return;
    const model = verdict.model as unknown as Record<string, unknown>;
    for (const forbidden of ["check", "download", "install", "restart", "apply", "request", "invoke"]) {
      expect(forbidden in model).toBe(false);
    }
  });
});
