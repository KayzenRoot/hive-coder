import { describe, expect, it } from "vitest";

import {
  ADMITTED_AUTHENTICITY_SCHEMES,
  LEGAL_TRANSITIONS,
  MAX_UPDATE_ERROR_DETAIL_CHARS,
  UPDATE_ERROR_CODES,
  UPDATE_STATES,
  UPDATE_STATE_CONTRACT,
  evaluateAuthenticityProof,
  evaluateStatus,
  evaluateTransition,
  evaluateUpdateError,
  isInstallReadyReachable,
  isUpdateState,
  requiresAuthenticityProof,
} from "./updateState";

const VALID_HASH = "a".repeat(64);

describe("update state contract", () => {
  it("defines the bounded state vocabulary", () => {
    expect(UPDATE_STATE_CONTRACT).toBe("hive-update-state-v1");
    expect(UPDATE_STATES).toEqual([
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
    ]);
  });

  it("fails closed on unknown states", () => {
    for (const value of ["", "IDLE", "update", null, undefined, 7, {}]) {
      expect(isUpdateState(value)).toBe(false);
      expect(evaluateTransition(value, "checking")).toEqual({ ok: false, reason: "unknown_state" });
      expect(evaluateTransition("idle", value)).toEqual({ ok: false, reason: "unknown_state" });
    }
  });

  it("permits only the declared transitions", () => {
    expect(evaluateTransition("idle", "checking")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("checking", "available")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("available", "downloading")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("downloading", "verifying")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("verifying", "ready")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("installing", "success")).toEqual({ ok: true, reason: "legal_transition" });
  });

  it("rejects illegal transitions", () => {
    const illegal: Array<[string, string]> = [
      ["idle", "ready"],
      ["idle", "installing"],
      ["checking", "downloading"],
      ["available", "ready"],
      ["downloading", "ready"],
      ["verifying", "installing"],
      ["success", "checking"],
      ["unavailable", "checking"],
    ];
    for (const [from, to] of illegal) {
      expect(evaluateTransition(from, to), `${from}->${to}`).toEqual({ ok: false, reason: "illegal_transition" });
    }
  });

  it("admits no cryptographic scheme in this slice", () => {
    expect(ADMITTED_AUTHENTICITY_SCHEMES).toEqual([]);
    expect(isInstallReadyReachable()).toBe(false);
    expect(requiresAuthenticityProof("installing")).toBe(true);
    expect(requiresAuthenticityProof("ready")).toBe(false);
  });

  it("refuses installation without an accepted authenticity proof", () => {
    // No proof at all.
    expect(evaluateTransition("ready", "installing")).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    // A well-formed proof is still refused because no scheme is admitted.
    const wellFormed = {
      scheme: "invented-scheme-v1",
      artifactSha256: VALID_HASH,
      metadataSha256: VALID_HASH,
      verifiedAtEpochMs: 1_700_000_000_000,
    };
    expect(evaluateAuthenticityProof(wellFormed)).toEqual({ ok: false, reason: "no_admitted_scheme" });
    expect(evaluateTransition("ready", "installing", wellFormed)).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
  });

  it("rejects malformed authenticity proofs before any policy question", () => {
    const malformed = [
      null,
      undefined,
      "proof",
      42,
      {},
      { scheme: "" },
      { scheme: "x", artifactSha256: "short", metadataSha256: VALID_HASH, verifiedAtEpochMs: 1 },
      { scheme: "x", artifactSha256: "A".repeat(64), metadataSha256: VALID_HASH, verifiedAtEpochMs: 1 },
      { scheme: "x", artifactSha256: VALID_HASH, metadataSha256: "zz", verifiedAtEpochMs: 1 },
      { scheme: "x", artifactSha256: VALID_HASH, metadataSha256: VALID_HASH, verifiedAtEpochMs: -1 },
      { scheme: "x", artifactSha256: VALID_HASH, metadataSha256: VALID_HASH, verifiedAtEpochMs: 1.5 },
    ];
    for (const proof of malformed) {
      expect(evaluateAuthenticityProof(proof)).toMatchObject({ ok: false });
    }
    expect(evaluateTransition("ready", "installing", {})).toEqual({
      ok: false,
      reason: "malformed_authenticity_proof",
    });
  });

  it("accepts a bounded, safe error and rejects everything else", () => {
    expect(evaluateUpdateError("service_inert", "updater is not enabled in this build")).toMatchObject({ ok: true });
    expect(evaluateUpdateError("service_inert", "")).toMatchObject({ ok: true });

    expect(evaluateUpdateError("invented_code", "x")).toEqual({ ok: false, reason: "unknown_error_code" });
    expect(evaluateUpdateError("service_inert", "x".repeat(MAX_UPDATE_ERROR_DETAIL_CHARS + 1))).toEqual({
      ok: false,
      reason: "oversized_error_detail",
    });
  });

  it("refuses error detail that could echo secrets, URLs or paths", () => {
    const unsafe = [
      "https://example.invalid/update?token=abc",
      "C:\\Users\\someone\\secret.txt",
      "/home/someone/.ssh/id_rsa",
      "Bearer abcdefghijklmnop",
      "MixedCase",
      "line\nbreak",
    ];
    for (const detail of unsafe) {
      expect(evaluateUpdateError("download_failed", detail), detail.slice(0, 20)).toMatchObject({ ok: false });
      expect(evaluateUpdateError("download_failed", detail), detail.slice(0, 20)).toEqual({
        ok: false,
        reason: "unsafe_error_detail",
      });
    }
  });

  it("refuses credential-shaped detail even when it satisfies the charset", () => {
    // These use only lowercase letters, digits and underscores, so the charset
    // rule alone would admit them; the credential-shape rule must catch them.
    const credentialShaped = ["ghp_abcdefghijklmnopqrstuv", "github_pat_abcdefghijklmnop"];
    for (const detail of credentialShaped) {
      expect(evaluateUpdateError("download_failed", detail), detail.slice(0, 12)).toEqual({
        ok: false,
        reason: "credential_shaped_detail",
      });
    }
    for (const detail of [
      "sk-abcdefghijklmnop",
      "xoxb-abcdefghijkl",
      "AKIAABCDEFGHIJKLMNOP",
      "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature",
      "api_key: abc",
      "QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo=",
    ]) {
      expect(evaluateUpdateError("download_failed", detail), detail.slice(0, 12)).toMatchObject({ ok: false });
    }
  });

  it("exposes a closed error-code vocabulary", () => {
    expect(UPDATE_ERROR_CODES.length).toBeGreaterThan(0);
    expect(new Set(UPDATE_ERROR_CODES).size).toBe(UPDATE_ERROR_CODES.length);
    for (const code of UPDATE_ERROR_CODES) {
      expect(evaluateUpdateError(code, "ok")).toMatchObject({ ok: true });
    }
  });

  it("validates a bounded status snapshot", () => {
    const status = {
      contract: UPDATE_STATE_CONTRACT,
      state: "unavailable",
      channel: "stable",
      currentVersion: "0.1.0",
      candidateVersion: null,
      error: { code: "service_inert", detail: "updater is not enabled in this build" },
      events: [],
    };
    expect(evaluateStatus(status)).toMatchObject({ ok: true });

    expect(evaluateStatus(null)).toEqual({ ok: false, reason: "invalid_status" });
    expect(evaluateStatus({ ...status, contract: "other" })).toEqual({ ok: false, reason: "invalid_status" });
    expect(evaluateStatus({ ...status, state: "bogus" })).toEqual({ ok: false, reason: "invalid_status" });
    expect(evaluateStatus({ ...status, channel: "nightly" })).toEqual({ ok: false, reason: "invalid_status" });
    expect(evaluateStatus({ ...status, currentVersion: "0.1" })).toEqual({ ok: false, reason: "invalid_status" });
    expect(evaluateStatus({ ...status, candidateVersion: "nope" })).toEqual({ ok: false, reason: "invalid_status" });
    expect(evaluateStatus({ ...status, error: { code: "bogus", detail: "x" } })).toEqual({
      ok: false,
      reason: "invalid_status",
    });
    expect(
      evaluateStatus({
        ...status,
        events: Array.from({ length: 64 }, () => ({ from: "idle", to: "checking", reason: "legal_transition" })),
      }),
    ).toEqual({ ok: false, reason: "oversized_status" });
  });

  it("declares no transition into an undefined state", () => {
    for (const from of UPDATE_STATES) {
      for (const to of LEGAL_TRANSITIONS[from]) {
        expect(UPDATE_STATES, `${from}->${to}`).toContain(to);
      }
    }
  });
});
