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
    const verdict = buildAboutReadModel(input({ channel: "dev", status: status({ channel: "dev" }) }));
    expect(verdict.ok).toBe(true);
    if (!verdict.ok) return;
    expect(verdict.model.channelLabel).toBe("dev/internal");
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
