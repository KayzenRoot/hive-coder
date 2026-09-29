import { describe, expect, it } from "vitest";

import {
  ADMITTED_AUTHENTICITY_SCHEMES,
  AUTHENTICITY_DEPENDENT_STATES,
  INSTALL_PROGRESS_STATES,
  LEGAL_TRANSITIONS,
  MAX_UPDATE_ERROR_DETAIL_CHARS,
  MAX_UPDATE_STATUS_EVENTS,
  PERSISTED_EVENT_OUTCOMES,
  PROOF_REFUSAL_OUTCOMES,
  TRANSITION_REASONS,
  UPDATE_ERROR_CODES,
  UPDATE_STATES,
  UPDATE_STATE_CONTRACT,
  UPDATE_STATUS_KEYS,
  evaluateAuthenticityProof,
  evaluatePersistedEvent,
  evaluateStatus,
  evaluateTransition,
  evaluateUpdateError,
  isAuthenticityDependentState,
  isInstallProgressState,
  isInstallReadyReachable,
  isPersistedEventOutcome,
  isTransitionReason,
  isUpdateState,
  requiresAuthenticityProof,
  type PersistedEventOutcome,
  type UpdateState,
} from "./updateState";

const VALID_HASH = "a".repeat(64);

/**
 * The strongest evidence this contract admits: the DEC-031 scheme, well formed.
 * Anything install-progress stays refused even against this proof, so a test that
 * passes here cannot be passing because the proof was weak.
 */
const ACCEPTED_PROOF = {
  scheme: "tauri-minisign-signed-version-v1",
  artifactSha256: VALID_HASH,
  metadataSha256: VALID_HASH,
  verifiedAtEpochMs: 1_700_000_000_000,
};

/** Structurally valid, but its scheme is not one this contract admits. */
const UNADMITTED_PROOF = { ...ACCEPTED_PROOF, scheme: "invented-scheme-v1" };

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
    // The two authenticity gates are different: entering `ready` is refused
    // without an accepted proof, and entering install progress is refused by an
    // authority this contract does not have.
    expect(evaluateTransition("verifying", "ready")).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    expect(evaluateTransition("installing", "success")).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
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

  it("admits exactly the scheme the Rust bridge produces", () => {
    // DEC-031 admits one scheme, and its name is the producer's constant in
    // `update_admission.rs`. A second name here would be a second cryptographic
    // authority that nobody granted.
    expect(ADMITTED_AUTHENTICITY_SCHEMES).toEqual(["tauri-minisign-signed-version-v1"]);
    expect(new Set(ADMITTED_AUTHENTICITY_SCHEMES).size).toBe(ADMITTED_AUTHENTICITY_SCHEMES.length);
    expect(evaluateAuthenticityProof(ACCEPTED_PROOF)).toEqual({ ok: true });
    expect(evaluateAuthenticityProof(UNADMITTED_PROOF)).toEqual({ ok: false, reason: "no_admitted_scheme" });
    expect(isInstallReadyReachable()).toBe(true);
  });

  it("separates install readiness from install progress", () => {
    expect(AUTHENTICITY_DEPENDENT_STATES).toEqual(["ready", "installing", "success"]);
    expect(INSTALL_PROGRESS_STATES).toEqual(["installing", "success"]);
    // The two vocabularies differ by exactly `ready`, the one authenticity claim
    // this slice is able to produce.
    expect(AUTHENTICITY_DEPENDENT_STATES.filter((state) => !isInstallProgressState(state))).toEqual(["ready"]);
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
    for (const value of ["", "installing ", "SUCCESS", "ready", null, undefined, 7, {}]) {
      expect(isInstallProgressState(value)).toBe(false);
    }
  });

  it("covers every edge into an authenticity-dependent state with exactly one gate", () => {
    const entering: string[] = [];
    for (const from of UPDATE_STATES) {
      for (const to of LEGAL_TRANSITIONS[from]) {
        if (isAuthenticityDependentState(to)) entering.push(`${from}->${to}`);
      }
    }
    // No authenticity-dependent destination is left ungated and no edge is gated
    // twice: `ready` by proof, install progress by authority.
    expect(entering.sort()).toEqual(["installing->success", "ready->installing", "verifying->ready"]);

    for (const [from, to] of [
      ["ready", "installing"],
      ["installing", "success"],
    ] as const) {
      const label = `${from}->${to}`;
      // The authority gate runs before the proof gate. These edges are not
      // refused for want of evidence, so no proof of any shape makes them legal.
      expect(evaluateTransition(from, to), label).toEqual({ ok: false, reason: "install_authority_not_governed" });
      expect(evaluateTransition(from, to, null), label).toEqual({
        ok: false,
        reason: "install_authority_not_governed",
      });
      expect(evaluateTransition(from, to, ACCEPTED_PROOF), label).toEqual({
        ok: false,
        reason: "install_authority_not_governed",
      });
      expect(evaluateTransition(from, to, {}), label).toEqual({ ok: false, reason: "install_authority_not_governed" });
    }

    const label = "verifying->ready";
    expect(evaluateTransition("verifying", "ready"), label).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    expect(evaluateTransition("verifying", "ready", null), label).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    // A well-formed proof whose scheme is not admitted is still no evidence.
    expect(evaluateTransition("verifying", "ready", UNADMITTED_PROOF), label).toEqual({
      ok: false,
      reason: "authenticity_proof_required",
    });
    expect(evaluateTransition("verifying", "ready", {}), label).toEqual({
      ok: false,
      reason: "malformed_authenticity_proof",
    });
    expect(evaluateTransition("verifying", "ready", ACCEPTED_PROOF), label).toEqual({
      ok: true,
      reason: "legal_transition",
    });

    // Ungated edges of the same source states remain legal without any proof.
    expect(evaluateTransition("verifying", "failure")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("ready", "idle")).toEqual({ ok: true, reason: "legal_transition" });
    expect(evaluateTransition("installing", "failure")).toEqual({ ok: true, reason: "legal_transition" });
  });

  it("admits no install-progress state from any source under any proof", () => {
    // Exhaustive over the whole edge and proof surface: even the strongest proof
    // this contract accepts never enters `installing` or `success`. `ready` is
    // admitted on exactly one edge, `verifying -> ready`.
    const proofs: readonly unknown[] = [undefined, null, {}, UNADMITTED_PROOF, ACCEPTED_PROOF];
    for (const from of UPDATE_STATES) {
      for (const to of AUTHENTICITY_DEPENDENT_STATES) {
        for (const [index, proof] of proofs.entries()) {
          const label = `${from}->${to}#${index}`;
          const expected = to === "ready" && from === "verifying" && proof === ACCEPTED_PROOF;
          expect(evaluateTransition(from, to, proof).ok, label).toBe(expected);
        }
      }
    }
  });

  it("refuses installation whatever evidence a caller presents", () => {
    // A proof describes what the Rust side already verified. It is never the
    // authority for a mutation of the running product.
    expect(evaluateTransition("ready", "installing")).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
    expect(evaluateAuthenticityProof(UNADMITTED_PROOF)).toEqual({ ok: false, reason: "no_admitted_scheme" });
    expect(evaluateTransition("ready", "installing", UNADMITTED_PROOF)).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
    expect(evaluateTransition("ready", "installing", ACCEPTED_PROOF)).toEqual({
      ok: false,
      reason: "install_authority_not_governed",
    });
    // The same accepted proof does admit the install-ready claim, so the refusals
    // above are the authority gate working and not a broken proof check.
    expect(evaluateTransition("verifying", "ready", ACCEPTED_PROOF)).toEqual({
      ok: true,
      reason: "legal_transition",
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
    expect(evaluateTransition("verifying", "ready", {})).toEqual({
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

    it("admits the install-ready claim only with an accepted proof, and never install progress", () => {
      const ready = { ...status(), state: "ready", candidateVersion: "0.2.0", error: null };
      // `ready` is assertable now that DEC-031 admits a scheme, but only together
      // with a proof under that scheme.
      expect(evaluateStatus({ ...ready, authenticityProof: ACCEPTED_PROOF }).ok).toBe(true);
      expect(evaluateStatus(ready)).toEqual(INVALID);
      expect(evaluateStatus({ ...ready, authenticityProof: null })).toEqual(INVALID);
      expect(evaluateStatus({ ...ready, authenticityProof: UNADMITTED_PROOF })).toEqual(INVALID);
      expect(evaluateStatus({ ...ready, authenticityProof: {} })).toEqual(INVALID);
      expect(evaluateStatus({ ...ready, authenticityProof: "proof" })).toEqual(INVALID);
      // Material the contract never declared is refused rather than quietly
      // dropped from a nominally valid proof.
      expect(evaluateStatus({ ...ready, authenticityProof: { ...ACCEPTED_PROOF, payload: "x".repeat(64) } })).toEqual(
        INVALID,
      );

      // Install progress is not assertable at all: admitting a proof scheme
      // authorises verification evidence, never an install or a restart.
      for (const state of INSTALL_PROGRESS_STATES) {
        const claim = { ...status(), state, candidateVersion: "0.2.0", error: null };
        expect(evaluateStatus(claim), state).toEqual(INVALID);
        expect(evaluateStatus({ ...claim, authenticityProof: ACCEPTED_PROOF }), state).toEqual(INVALID);
        expect(evaluateStatus({ ...claim, authenticityProof: UNADMITTED_PROOF }), state).toEqual(INVALID);
        expect(evaluateStatus({ ...claim, authenticityProof: null }), state).toEqual(INVALID);
      }
      // Proof material is refused outside an authenticity-dependent state as
      // well, rather than being accepted and ignored.
      expect(evaluateStatus({ ...status(), authenticityProof: ACCEPTED_PROOF })).toEqual(INVALID);
      expect(evaluateStatus({ ...status(), authenticityProof: "proof" })).toEqual(INVALID);
      // The refusal above is a live-policy refusal, not a vacuous one: the same
      // unadmitted proof shape is structurally well formed.
      expect(evaluateAuthenticityProof(UNADMITTED_PROOF)).toEqual({ ok: false, reason: "no_admitted_scheme" });
    });

    it("applies the persisted-event law to every recorded entry", () => {
      // Outcomes that this contract could actually have produced.
      const accepted: ReadonlyArray<readonly [UpdateState, UpdateState, PersistedEventOutcome]> = [
        ["verifying", "ready", "authenticity_proof_required"],
        ["verifying", "ready", "malformed_authenticity_proof"],
        ["verifying", "ready", "legal_transition"],
        ["ready", "idle", "legal_transition"],
        ["ready", "failure", "legal_transition"],
        ["idle", "checking", "legal_transition"],
        ["checking", "available", "legal_transition"],
        ["verifying", "failure", "legal_transition"],
      ];
      for (const [from, to, reason] of accepted) {
        expect(
          evaluateStatus({ ...status(), events: [{ from, to, reason }] }),
          `${from}->${to}/${reason}`,
        ).toMatchObject({ ok: true });
      }

      // A recorded entry may not assert an install-progress source state: getting
      // there needs an install authority this contract does not have, so no entry
      // naming it is one this contract could have written.
      const unreachableSources = [
        { from: "installing", to: "failure", reason: "legal_transition" },
        { from: "installing", to: "success", reason: "legal_transition" },
        { from: "success", to: "idle", reason: "legal_transition" },
      ];
      for (const event of unreachableSources) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toEqual(INVALID);
      }

      // Refusal outcomes are edge-specific: they are admissible only on the one
      // proof-gated attempt, never on an ordinary edge.
      for (const event of [
        { from: "idle", to: "checking", reason: "authenticity_proof_required" },
        { from: "idle", to: "checking", reason: "malformed_authenticity_proof" },
        { from: "checking", to: "available", reason: "authenticity_proof_required" },
      ]) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toEqual(INVALID);
      }

      // `illegal_transition` and `unknown_state` cannot ride on a validated legal
      // edge: the event shape already fixes both states and the declared edge.
      for (const event of [
        { from: "idle", to: "checking", reason: "illegal_transition" },
        { from: "idle", to: "checking", reason: "unknown_state" },
      ]) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toEqual(INVALID);
      }

      // No entry may name an install-progress destination, whatever its reason:
      // the recording itself would assert that an install happened.
      for (const event of [
        { from: "ready", to: "installing", reason: "authenticity_proof_required" },
        { from: "ready", to: "installing", reason: "legal_transition" },
        { from: "ready", to: "installing", reason: "malformed_authenticity_proof" },
        { from: "installing", to: "success", reason: "authenticity_proof_required" },
        { from: "installing", to: "failure", reason: "authenticity_proof_required" },
        { from: "ready", to: "idle", reason: "authenticity_proof_required" },
        { from: "success", to: "idle", reason: "legal_transition" },
      ]) {
        expect(evaluateStatus({ ...status(), events: [event] }), JSON.stringify(event)).toEqual(INVALID);
      }
    });

    it("keeps ordinary reachable history valid, including pre-install failure", () => {
      const legalHistory = [
        { from: "idle", to: "checking", reason: "legal_transition" },
        { from: "checking", to: "available", reason: "legal_transition" },
        { from: "available", to: "downloading", reason: "legal_transition" },
        { from: "downloading", to: "verifying", reason: "legal_transition" },
        { from: "verifying", to: "failure", reason: "legal_transition" },
        { from: "checking", to: "unavailable", reason: "legal_transition" },
        { from: "downloading", to: "failure", reason: "legal_transition" },
        { from: "checking", to: "idle", reason: "legal_transition" },
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

  describe("persisted event law", () => {
    it("rejects install-progress source states with a distinct reason", () => {
      for (const state of INSTALL_PROGRESS_STATES) {
        for (const to of UPDATE_STATES) {
          for (const reason of [...PERSISTED_EVENT_OUTCOMES, "illegal_transition", "invented"]) {
            const verdict = evaluatePersistedEvent(state, to, reason);
            expect(verdict, `${state}->${to}/${reason}`).toEqual({ ok: false, reason: "unreachable_source_state" });
          }
        }
      }
      // `ready` is no longer one of them: DEC-031 admits the claim it carries, so
      // a history entry leaving `ready` is recordable on its declared edges.
      expect(evaluatePersistedEvent("ready", "idle", "legal_transition")).toMatchObject({ ok: true });
      expect(evaluatePersistedEvent("ready", "failure", "legal_transition")).toMatchObject({ ok: true });
    });

    it("rejects undeclared edges, unknown states and inadmissible outcomes", () => {
      expect(evaluatePersistedEvent("idle", "ready", "legal_transition")).toEqual({
        ok: false,
        reason: "undeclared_edge",
      });
      expect(evaluatePersistedEvent("checking", "downloading", "legal_transition")).toEqual({
        ok: false,
        reason: "undeclared_edge",
      });
      expect(evaluatePersistedEvent("bogus", "checking", "legal_transition")).toEqual({
        ok: false,
        reason: "unknown_state",
      });
      expect(evaluatePersistedEvent("idle", "bogus", "legal_transition")).toEqual({
        ok: false,
        reason: "unknown_state",
      });
      expect(evaluatePersistedEvent("idle", "checking", "illegal_transition")).toEqual({
        ok: false,
        reason: "inadmissible_outcome",
      });
      expect(evaluatePersistedEvent("idle", "checking", "unknown_state")).toEqual({
        ok: false,
        reason: "inadmissible_outcome",
      });
      // A completed admission is now recordable, so the outcome vocabulary is
      // what refuses an impossible claim on this edge, not its reachability.
      expect(evaluatePersistedEvent("verifying", "ready", "legal_transition")).toEqual({
        ok: true,
        event: { from: "verifying", to: "ready", reason: "legal_transition" },
      });
      expect(evaluatePersistedEvent("verifying", "ready", "illegal_transition")).toEqual({
        ok: false,
        reason: "inadmissible_outcome",
      });
      // No outcome at all records an edge into install progress.
      for (const reason of [...PERSISTED_EVENT_OUTCOMES, "install_authority_not_governed", "invented"]) {
        expect(evaluatePersistedEvent("ready", "installing", reason)).toEqual({
          ok: false,
          reason: "inadmissible_outcome",
        });
      }
      expect(evaluatePersistedEvent("idle", "checking", "")).toEqual({
        ok: false,
        reason: "inadmissible_outcome",
      });
    });

    it("returns a reconstructed event for an admissible recording", () => {
      const verdict = evaluatePersistedEvent("verifying", "ready", "authenticity_proof_required");
      expect(verdict).toEqual({
        ok: true,
        event: { from: "verifying", to: "ready", reason: "authenticity_proof_required" },
      });
      expect(evaluatePersistedEvent("idle", "checking", "legal_transition")).toEqual({
        ok: true,
        event: { from: "idle", to: "checking", reason: "legal_transition" },
      });
    });

    it("keeps the persisted outcome vocabulary closed and coupled to the refusal set", () => {
      // `TransitionReason` is the live-evaluation vocabulary; the persisted
      // vocabulary is strictly narrower, and its non-success members are exactly
      // the bounded proof refusals.
      expect(PERSISTED_EVENT_OUTCOMES.filter((outcome) => outcome !== "legal_transition")).toEqual([
        ...PROOF_REFUSAL_OUTCOMES,
      ]);
      expect(TRANSITION_REASONS).toContain("illegal_transition");
      expect(TRANSITION_REASONS).toContain("unknown_state");
      expect(PERSISTED_EVENT_OUTCOMES).not.toContain("illegal_transition");
      expect(PERSISTED_EVENT_OUTCOMES).not.toContain("unknown_state");
      for (const outcome of PERSISTED_EVENT_OUTCOMES) {
        expect(isPersistedEventOutcome(outcome), outcome).toBe(true);
        expect(PERSISTED_EVENT_OUTCOMES.length).toBeLessThan(TRANSITION_REASONS.length);
      }
      for (const value of ["", "legal", "illegal_transition", "unknown_state", "invented", null, 3, {}]) {
        expect(isPersistedEventOutcome(value), String(value)).toBe(false);
      }
    });

    it("records the proof-gated attempt and nothing that names install progress", () => {
      // The proof refusal is recordable on the one edge that can produce it.
      expect(evaluatePersistedEvent("verifying", "ready", "authenticity_proof_required")).toEqual({
        ok: true,
        event: { from: "verifying", to: "ready", reason: "authenticity_proof_required" },
      });
      // On an edge into install progress the same reason is not an outcome this
      // contract could have written, and an `installing` source is impossible.
      expect(evaluatePersistedEvent("ready", "installing", "authenticity_proof_required")).toEqual({
        ok: false,
        reason: "inadmissible_outcome",
      });
      expect(evaluatePersistedEvent("installing", "success", "authenticity_proof_required")).toEqual({
        ok: false,
        reason: "unreachable_source_state",
      });
      // `install_authority_not_governed` is a live verdict reason only. It cannot
      // be persisted, because persisting it would mean naming an install-progress
      // destination, which the rule above already refuses for every outcome.
      expect(TRANSITION_REASONS).toContain("install_authority_not_governed");
      expect(PERSISTED_EVENT_OUTCOMES).not.toContain("install_authority_not_governed");
      expect(PROOF_REFUSAL_OUTCOMES).not.toContain("install_authority_not_governed");
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
