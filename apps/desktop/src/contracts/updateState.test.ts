import { describe, expect, it } from "vitest";

import {
  ADMITTED_AUTHENTICITY_SCHEMES,
  AUTHENTICITY_DEPENDENT_STATES,
  LEGAL_TRANSITIONS,
  MAX_UPDATE_ERROR_DETAIL_CHARS,
  MAX_UPDATE_STATUS_EVENTS,
  TRANSITION_REASONS,
  UPDATE_ERROR_CODES,
  UPDATE_STATES,
  UPDATE_STATE_CONTRACT,
  UPDATE_STATUS_KEYS,
  evaluateAuthenticityProof,
  evaluateStatus,
  evaluateTransition,
  evaluateUpdateError,
  isAuthenticityDependentState,
  isInstallReadyReachable,
  isTransitionReason,
  isUpdateState,
  requiresAuthenticityProof,
  type UpdateState,
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
    // Entering any authenticity-dependent state is gated: these edges are legal
    // in shape but refused without an accepted proof.
    expect(evaluateTransition("verifying", "ready")).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    expect(evaluateTransition("installing", "success")).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
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
    expect(AUTHENTICITY_DEPENDENT_STATES).toEqual(["ready", "installing", "success"]);
    for (const state of ["ready", "installing", "success"] as const) {
      expect(requiresAuthenticityProof(state), state).toBe(true);
      expect(isAuthenticityDependentState(state), state).toBe(true);
    }
    for (const state of ["idle", "checking", "available", "downloading", "verifying", "failure", "unavailable"] as const) {
      expect(requiresAuthenticityProof(state), state).toBe(false);
      expect(isAuthenticityDependentState(state), state).toBe(false);
    }
    for (const value of ["", "ready ", "SUCCESS", "installed", null, undefined, 7, {}]) {
      expect(isAuthenticityDependentState(value)).toBe(false);
    }
  });

  it("gates every edge that enters an authenticity-dependent state", () => {
    const wellFormed = {
      scheme: "invented-scheme-v1",
      artifactSha256: VALID_HASH,
      metadataSha256: VALID_HASH,
      verifiedAtEpochMs: 1_700_000_000_000,
    };
    const gatedEdges: ReadonlyArray<readonly [UpdateState, UpdateState]> = [
      ["verifying", "ready"],
      ["ready", "installing"],
      ["installing", "success"],
    ];
    // The gated set is exactly the legal edges whose destination is
    // authenticity-dependent: no such destination is left ungated.
    const legalAuthenticityDependentEdges: string[] = [];
    for (const from of UPDATE_STATES) {
      for (const to of LEGAL_TRANSITIONS[from]) {
        if (isAuthenticityDependentState(to)) legalAuthenticityDependentEdges.push(`${from}->${to}`);
      }
    }
    expect(legalAuthenticityDependentEdges.sort()).toEqual(gatedEdges.map(([from, to]) => `${from}->${to}`).sort());

    for (const [from, to] of gatedEdges) {
      const label = `${from}->${to}`;
      expect(evaluateTransition(from, to), label).toEqual({ ok: false, reason: "authenticity_proof_required" });
      expect(evaluateTransition(from, to, null), label).toEqual({
        ok: false,
        reason: "authenticity_proof_required",
      });
      expect(evaluateTransition(from, to, wellFormed), label).toEqual({
        ok: false,
        reason: "authenticity_proof_required",
      });
      expect(evaluateTransition(from, to, {}), label).toEqual({
        ok: false,
        reason: "malformed_authenticity_proof",
      });
    }
    // Ungated edges of the same source states remain legal without any proof.
    expect(evaluateTransition("verifying", "failure")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("ready", "idle")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("installing", "failure")).toEqual({ ok: true, reason: "legal_transition" });
  });

  it("makes the whole install path unreachable while no scheme is admitted", () => {
    expect(isInstallReadyReachable()).toBe(false);
    // Exhaustive over the whole state vocabulary: nothing reaches `ready`,
    // `installing` or `success`, with or without a well-formed but unadmitted
    // proof. This is the property the lifecycle claim rests on.
    const wellFormed = {
      scheme: "invented-scheme-v1",
      artifactSha256: VALID_HASH,
      metadataSha256: VALID_HASH,
      verifiedAtEpochMs: 1,
    };
    for (const from of UPDATE_STATES) {
      for (const to of AUTHENTICITY_DEPENDENT_STATES) {
        const label = `${from}->${to}`;
        expect(evaluateTransition(from, to).ok, label).toBe(false);
        expect(evaluateTransition(from, to, wellFormed).ok, label).toBe(false);
        expect(evaluateTransition(from, to, {}).ok, label).toBe(false);
      }
    }
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

  it("declares no transition into an undefined state", () => {
    for (const from of UPDATE_STATES) {
      for (const to of LEGAL_TRANSITIONS[from]) {
        expect(UPDATE_STATES, `${from}->${to}`).toContain(to);
      }
    }
  });

  it("closes the transition-reason vocabulary", () => {
    expect(new Set(TRANSITION_REASONS).size).toBe(TRANSITION_REASONS.length);
    for (const reason of TRANSITION_REASONS) {
      expect(isTransitionReason(reason)).toBe(true);
    }
    for (const value of ["", "legal", "LEGAL_TRANSITION", null, undefined, 3, {}]) {
      expect(isTransitionReason(value)).toBe(false);
    }
  });

  describe("status snapshot closure", () => {
    const INVALID = { ok: false, reason: "invalid_status" } as const;

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

    it("validates a bounded status snapshot into a reconstructed object", () => {
      const input = status();
      const verdict = evaluateStatus(input);
      expect(verdict.ok).toBe(true);
      if (!verdict.ok) return;
      expect(verdict.status).toEqual(input);
      // The canonical result is rebuilt from validated fields, never aliased:
      // an unvalidated reference must not be able to mutate validated state.
      expect(verdict.status).not.toBe(input);
      expect(verdict.status).not.toBe(input as unknown as object);
      expect(verdict.status.events).not.toBe((input as { events: unknown[] }).events);
    });

    it("refuses non-object and malformed status input", () => {
      expect(evaluateStatus(null)).toEqual(INVALID);
      expect(evaluateStatus(undefined)).toEqual(INVALID);
      expect(evaluateStatus("status")).toEqual(INVALID);
      expect(evaluateStatus(7)).toEqual(INVALID);
      expect(evaluateStatus([])).toEqual(INVALID);
      expect(evaluateStatus([status()])).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), contract: "other" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), state: "bogus" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), channel: "nightly" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), currentVersion: "0.1" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), candidateVersion: "nope" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), error: { code: "bogus", detail: "x" } })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), error: {} })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), error: "failed" })).toEqual(INVALID);
    });

    it("refuses unknown keys at the top level, the error object and every event", () => {
      expect(evaluateStatus({ ...status(), extra: "payload" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), __proto__: { polluted: true }, extra: 1 })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), error: { code: "service_inert", detail: "x", extra: 1 } })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), events: [{ from: "idle", to: "checking", reason: "legal_transition", extra: 1 }] })).toEqual(
        INVALID,
      );
      // An arbitrary unbounded payload cannot survive as a status snapshot.
      expect(evaluateStatus({ payload: "x".repeat(10_000) })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), events: [{ ...status(), payload: "x".repeat(1_000) }] })).toEqual(INVALID);
    });

    it("requires every declared status key", () => {
      for (const key of UPDATE_STATUS_KEYS) {
        const copy: Record<string, unknown> = { ...status() };
        delete copy[key];
        expect(evaluateStatus(copy), key).toEqual(INVALID);
      }
    });

    it("validates every recorded event, not only the event count", () => {
      const legal = { from: "idle", to: "checking", reason: "legal_transition" };
      expect(evaluateStatus({ ...status(), events: [legal] })).toMatchObject({ ok: true });

      const malformedEvents: unknown[] = [
        null,
        "event",
        7,
        [],
        {},
        { from: "idle", to: "checking" },
        { from: "idle", to: "bogus", reason: "legal_transition" },
        { from: "bogus", to: "checking", reason: "legal_transition" },
        { from: "idle", to: "checking", reason: "invented_reason" },
        { from: "idle", to: "checking", reason: "" },
        { from: "idle", to: "ready", reason: "legal_transition" },
        { from: "checking", to: "downloading", reason: "legal_transition" },
        { from: "success", to: "checking", reason: "legal_transition" },
      ];
      for (const event of malformedEvents) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toEqual(INVALID);
      }
      expect(
        evaluateStatus({
          ...status(),
          events: Array.from({ length: MAX_UPDATE_STATUS_EVENTS + 1 }, () => legal),
        }),
      ).toEqual({ ok: false, reason: "oversized_status" });
      expect(
        evaluateStatus({
          ...status(),
          events: Array.from({ length: 64 }, () => ({ from: "idle", to: "checking", reason: "legal_transition" })),
        }),
      ).toEqual({ ok: false, reason: "oversized_status" });
    });

    it("binds current version and channel as one identity", () => {
      // Individually valid, mutually incompatible.
      expect(evaluateStatus({ ...status(), currentVersion: "0.1.0", channel: "beta" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), currentVersion: "0.1.0", channel: "dev" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), currentVersion: "0.1.0-beta.1", channel: "stable" })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), currentVersion: "0.1.0-dev.1", channel: "beta" })).toEqual(INVALID);
      // The matching pairs are accepted.
      expect(evaluateStatus(status()).ok).toBe(true);
      expect(evaluateStatus({ ...status(), currentVersion: "0.1.0-beta.1", channel: "beta" }).ok).toBe(true);
      expect(evaluateStatus({ ...status(), currentVersion: "0.1.0-dev.1", channel: "dev" }).ok).toBe(true);
    });

    it("applies state-dependent candidate invariants", () => {
      // Candidate required states must carry one.
      for (const state of ["available", "downloading", "verifying", "ready", "installing", "success"] as const) {
        expect(evaluateStatus({ ...status(), state, error: null }), state).toEqual(INVALID);
      }
      // Candidate forbidden states must not.
      for (const state of ["idle", "checking", "unavailable"] as const) {
        expect(evaluateStatus({ ...status(), state, error: null, candidateVersion: "0.2.0" }), state).toEqual(INVALID);
      }
      // An available upgrade is coherent.
      const available = { ...status(), state: "available", error: null, candidateVersion: "0.2.0" };
      expect(evaluateStatus(available).ok).toBe(true);
      // A candidate that is not strictly newer is incoherent, and a mismatched
      // candidate is refused even when the current pair agrees.
      expect(evaluateStatus({ ...available, candidateVersion: "0.1.0" })).toEqual(INVALID);
      expect(evaluateStatus({ ...available, candidateVersion: "0.0.9" })).toEqual(INVALID);
      expect(evaluateStatus({ ...available, candidateVersion: "0.2.0-beta.1" })).toEqual(INVALID);
      expect(
        evaluateStatus({
          ...status(),
          state: "available",
          channel: "beta",
          currentVersion: "0.1.0-beta.1",
          candidateVersion: "0.2.0-beta.1",
          error: null,
        }).ok,
      ).toBe(true);
    });

    it("enforces error presence per state", () => {
      expect(evaluateStatus({ ...status(), state: "failure", error: null, candidateVersion: "0.2.0" })).toEqual(INVALID);
      expect(
        evaluateStatus({ ...status(), state: "failure", candidateVersion: "0.2.0", error: { code: "download_failed", detail: "ok" } }).ok,
      ).toBe(true);
      expect(
        evaluateStatus({ ...status(), state: "available", error: { code: "download_failed", detail: "ok" }, candidateVersion: "0.2.0" }),
      ).toEqual(INVALID);
      // `unavailable` may or may not carry a diagnostic.
      expect(evaluateStatus({ ...status(), error: null }).ok).toBe(true);
      expect(evaluateStatus(status()).ok).toBe(true);
    });

    it("refuses a snapshot that claims an authenticity-dependent state", () => {
      const proof = {
        scheme: "invented-scheme-v1",
        artifactSha256: VALID_HASH,
        metadataSha256: VALID_HASH,
        verifiedAtEpochMs: 1,
      };
      for (const state of AUTHENTICITY_DEPENDENT_STATES) {
        const claim = { ...status(), state, candidateVersion: "0.2.0", error: null };
        expect(evaluateStatus(claim), state).toEqual(INVALID);
        expect(evaluateStatus({ ...claim, authenticityProof: proof }), state).toEqual(INVALID);
        expect(evaluateStatus({ ...claim, authenticityProof: null }), state).toEqual(INVALID);
      }
      // `success` specifically: it is reachable only from `installing`, so a
      // direct install-completed snapshot asserts a proof-gated traversal.
      expect(evaluateStatus({ ...status(), state: "success", candidateVersion: "0.2.0", error: null })).toEqual(INVALID);
      expect(
        evaluateStatus({ ...status(), state: "success", candidateVersion: "0.2.0", error: null, authenticityProof: proof }),
      ).toEqual(INVALID);
      // Proof material is refused outside an authenticity-dependent state as
      // well, rather than being accepted and ignored.
      expect(evaluateStatus({ ...status(), authenticityProof: proof })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), authenticityProof: "proof" })).toEqual(INVALID);
      // The refusal is a live-policy refusal, not a vacuous one: the same proof
      // is structurally well formed and only refused for policy.
      expect(evaluateAuthenticityProof(proof)).toEqual({ ok: false, reason: "no_admitted_scheme" });
    });

    it("refuses proof-gated successful history while keeping pre-gate history legal", () => {
      // A history entry may not report a successful traversal of the proof-gated
      // install path in v1: the event schema carries no gate evidence that the
      // current validator could verify, and no scheme is admitted.
      const gatedSuccesses = [
        { from: "verifying", to: "ready", reason: "legal_transition" },
        { from: "ready", to: "installing", reason: "legal_transition" },
        { from: "installing", to: "success", reason: "legal_transition" },
      ];
      for (const event of gatedSuccesses) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toEqual(INVALID);
      }

      // Refusals on those same edges stay recordable: a recorded refusal is not
      // a claim that the gated transition succeeded.
      const recordedRefusals = [
        { from: "verifying", to: "ready", reason: "authenticity_proof_required" },
        { from: "verifying", to: "ready", reason: "malformed_authenticity_proof" },
        { from: "ready", to: "installing", reason: "authenticity_proof_required" },
        { from: "installing", to: "success", reason: "authenticity_proof_required" },
      ];
      for (const event of recordedRefusals) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toMatchObject({ ok: true });
      }

      // Failures anywhere on the path, and ordinary pre-gate progress, remain
      // valid history — verification is not globally banned.
      const legalHistory = [
        { from: "idle", to: "checking", reason: "legal_transition" },
        { from: "checking", to: "available", reason: "legal_transition" },
        { from: "available", to: "downloading", reason: "legal_transition" },
        { from: "downloading", to: "verifying", reason: "legal_transition" },
        { from: "verifying", to: "failure", reason: "legal_transition" },
        { from: "ready", to: "idle", reason: "legal_transition" },
        { from: "installing", to: "failure", reason: "legal_transition" },
        { from: "checking", to: "unavailable", reason: "legal_transition" },
      ];
      for (const event of legalHistory) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toMatchObject({ ok: true });
      }
      expect(
        evaluateStatus({
          ...status(),
          state: "failure",
          candidateVersion: "0.2.0",
          error: { code: "verification_failed", detail: "ok" },
          events: [
            { from: "idle", to: "checking", reason: "legal_transition" },
            { from: "downloading", to: "verifying", reason: "legal_transition" },
            { from: "verifying", to: "failure", reason: "legal_transition" },
          ],
        }),
      ).toMatchObject({ ok: true });
    });
  });

  describe("plain own-data record hardening", () => {
    const INVALID = { ok: false, reason: "invalid_status" } as const;

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

    /** A field name whose read is observable, so getter invocation is provable. */
    function accessorTracked(overrides: Record<string, unknown> = {}) {
      const reads: string[] = [];
      const record = {
        contract: UPDATE_STATE_CONTRACT,
        state: "unavailable",
        channel: "stable",
        currentVersion: "0.1.0",
        candidateVersion: null,
        authenticityProof: null,
        error: null,
        events: [] as unknown[],
        ...overrides,
      };
      const tracked: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(record)) {
        Object.defineProperty(tracked, key, {
          enumerable: true,
          configurable: true,
          get() {
            reads.push(key);
            return value;
          },
        });
      }
      return { tracked, reads };
    }

    it("accepts a plain own-data record, including a null-prototype record", () => {
      expect(evaluateStatus(status())).toMatchObject({ ok: true });
      const nullPrototype = Object.assign(Object.create(null) as Record<string, unknown>, status());
      expect(evaluateStatus(nullPrototype)).toMatchObject({ ok: true });
    });

    it("refuses inherited required fields from a custom prototype", () => {
      const inherited = Object.create(status()) as Record<string, unknown>;
      expect(evaluateStatus(inherited)).toEqual(INVALID);
      const mixed = Object.create({ channel: "stable" }) as Record<string, unknown>;
      for (const [key, value] of Object.entries(status())) {
        if (key !== "channel") mixed[key] = value;
      }
      expect(evaluateStatus(mixed)).toEqual(INVALID);
      // A custom prototype that is not Object.prototype is refused before any
      // field is read, so a valid-looking own field set cannot rescue it.
      const prototypeBacked = Object.create(status(), { state: { value: "available", enumerable: true } });
      expect(evaluateStatus(prototypeBacked)).toEqual(INVALID);
    });

    it("refuses class instances and other non-plain records", () => {
      class StatusRecord {
        public readonly contract = UPDATE_STATE_CONTRACT;
        public readonly state = "unavailable";
        public readonly channel = "stable";
        public readonly currentVersion = "0.1.0";
        public readonly candidateVersion = null;
        public readonly authenticityProof = null;
        public readonly error = null;
        public readonly events: unknown[] = [];
      }
      expect(evaluateStatus(new StatusRecord())).toEqual(INVALID);
      class Extended extends Map<string, unknown> {}
      expect(evaluateStatus(new Extended())).toEqual(INVALID);
      expect(evaluateStatus(new Date())).toEqual(INVALID);
      expect(evaluateStatus(/x/)).toEqual(INVALID);
    });

    it("refuses accessor-backed status records without invoking a single getter", () => {
      const { tracked, reads } = accessorTracked();
      expect(evaluateStatus(tracked)).toEqual(INVALID);
      expect(reads).toEqual([]);
    });

    it("refuses accessor-backed nested records without invoking a single getter", () => {
      const errorReads: string[] = [];
      const error = { code: "service_inert", detail: "ok" };
      const trackedError: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(error)) {
        Object.defineProperty(trackedError, key, {
          enumerable: true,
          get() {
            errorReads.push(key);
            return value;
          },
        });
      }
      expect(evaluateStatus(status({ error: trackedError }))).toEqual(INVALID);
      expect(errorReads).toEqual([]);

      const eventReads: string[] = [];
      const event = { from: "idle", to: "checking", reason: "legal_transition" };
      const trackedEvent: Record<string, unknown> = {};
      for (const [key, value] of Object.entries(event)) {
        Object.defineProperty(trackedEvent, key, {
          enumerable: true,
          get() {
            eventReads.push(key);
            return value;
          },
        });
      }
      expect(evaluateStatus(status({ events: [trackedEvent] }))).toEqual(INVALID);
      expect(eventReads).toEqual([]);
    });

    it("refuses accessor-backed proof objects and sparse event arrays without invoking getters", () => {
      const proofReads: string[] = [];
      const proof: Record<string, unknown> = {};
      for (const [key, value] of Object.entries({
        scheme: "invented-scheme-v1",
        artifactSha256: VALID_HASH,
        metadataSha256: VALID_HASH,
        verifiedAtEpochMs: 1,
      })) {
        Object.defineProperty(proof, key, {
          enumerable: true,
          get() {
            proofReads.push(key);
            return value;
          },
        });
      }
      expect(evaluateAuthenticityProof(proof)).toEqual({ ok: false, reason: "malformed_authenticity_proof" });
      expect(proofReads).toEqual([]);
      expect(evaluateStatus(status({ state: "ready", candidateVersion: "0.2.0", authenticityProof: proof }))).toEqual(
        INVALID,
      );
      expect(proofReads).toEqual([]);

      // Accessor-backed array indices are refused without invocation, and holes
      // are refused rather than skipped.
      const indexReads: string[] = [];
      const accessorArray: unknown[] = [];
      Object.defineProperty(accessorArray, "0", {
        enumerable: true,
        configurable: true,
        get() {
          indexReads.push("0");
          return { from: "idle", to: "checking", reason: "legal_transition" };
        },
      });
      accessorArray.length = 1;
      expect(evaluateStatus(status({ events: accessorArray }))).toEqual(INVALID);
      expect(indexReads).toEqual([]);

      const sparse: unknown[] = [];
      sparse.length = 1;
      expect(evaluateStatus(status({ events: sparse }))).toEqual(INVALID);
    });

    it("refuses non-enumerable and symbol-keyed fields", () => {
      const hidden = status();
      Object.defineProperty(hidden, "extra", { value: "hidden", enumerable: false });
      expect(evaluateStatus(hidden)).toEqual(INVALID);

      const symbolKeyed = status() as Record<PropertyKey, unknown>;
      symbolKeyed[Symbol("payload")] = "x";
      expect(evaluateStatus(symbolKeyed)).toEqual(INVALID);
    });

    it("still rejects unknown own keys and missing required keys", () => {
      expect(evaluateStatus({ ...status(), extra: "payload" })).toEqual(INVALID);
      for (const key of UPDATE_STATUS_KEYS) {
        const copy: Record<string, unknown> = { ...status() };
        delete copy[key];
        expect(evaluateStatus(copy), key).toEqual(INVALID);
      }
      expect(evaluateStatus({ ...status(), error: { code: "service_inert", detail: "ok", extra: 1 } })).toEqual(INVALID);
      expect(
        evaluateStatus({ ...status(), events: [{ from: "idle", to: "checking", reason: "legal_transition", extra: 1 }] }),
      ).toEqual(INVALID);
    });
  });
});
