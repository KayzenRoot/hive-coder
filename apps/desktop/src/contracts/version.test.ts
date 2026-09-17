import { describe, expect, it } from "vitest";

import {
  CANONICAL_VERSION_SOURCE,
  MAX_VERSION_CHARS,
  VERSION_CONTRACT,
  VERSION_MIRRORS,
  compareVersions,
  evaluateVersionDrift,
  isValidVersion,
  isStrictlyNewer,
  parseVersion,
} from "./version";
import PARITY_VECTORS from "./semverParityVectors.json";

describe("version contract", () => {
  it("declares exactly one canonical source and its mirrors", () => {
    expect(VERSION_CONTRACT).toBe("hive-version-v1");
    expect(CANONICAL_VERSION_SOURCE).toBe("apps/desktop/src-tauri/tauri.conf.json");
    expect(VERSION_MIRRORS).toHaveLength(2);
    expect(VERSION_MIRRORS).toContain("apps/desktop/src-tauri/Cargo.toml");
    expect(VERSION_MIRRORS).toContain("apps/desktop/package.json");
  });

  it("parses strict SemVer into components", () => {
    const parsed = parseVersion("12.34.56-beta.2+build.7");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    // Core identifiers are exact decimal strings, never floating-point numbers.
    expect(parsed.version.major).toBe("12");
    expect(parsed.version.minor).toBe("34");
    expect(parsed.version.patch).toBe("56");
    expect(parsed.version.prerelease).toEqual(["beta", "2"]);
    expect(parsed.version.build).toEqual(["build", "7"]);
  });

  it("accepts core identifiers beyond the JavaScript safe-integer range", () => {
    // These are valid SemVer and are accepted by the Python drift gate; the
    // product parser must agree, so one canonical version law cannot have two
    // acceptance sets.
    for (const version of [
      "9007199254740991.0.0",
      "9007199254740992.0.0",
      "9007199254740993.0.0",
      "1.9007199254740993.0",
      "1.0.9007199254740993",
      "123456789012345678901234567890.0.0",
    ]) {
      expect(isValidVersion(version), version).toBe(true);
      expect(parseVersion(version).ok, version).toBe(true);
    }
    const parsed = parseVersion("9007199254740993.0.0");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.version.major).toBe("9007199254740993");
    // No precision is lost: the exact string survives, and ordering is exact.
    expect(compareVersions("9007199254740993.0.0", "9007199254740992.0.0")).toBe(1);
    expect(compareVersions("9007199254740992.0.0", "9007199254740993.0.0")).toBe(-1);
    expect(compareVersions("9007199254740992.0.0", "9007199254740992.0.0")).toBe(0);
    expect(
      compareVersions("123456789012345678901234567891.0.0", "123456789012345678901234567890.0.0"),
    ).toBe(1);
    expect(isStrictlyNewer("9007199254740993.0.0", "9007199254740992.0.0")).toBe(true);
    expect(isStrictlyNewer("9007199254740992.0.0", "9007199254740993.0.0")).toBe(false);
  });

  it("agrees with the shared cross-language parity vectors", () => {
    expect(PARITY_VECTORS.profile.maxVersionChars).toBe(MAX_VERSION_CHARS);
    expect(PARITY_VECTORS.profile.law).toBe("bounded SemVer 2.0.0");
    expect(PARITY_VECTORS.accepted.length).toBeGreaterThan(0);
    expect(PARITY_VECTORS.rejected.length).toBeGreaterThan(0);
    for (const version of PARITY_VECTORS.accepted) {
      expect(isValidVersion(version), `accepted: ${JSON.stringify(version)}`).toBe(true);
      expect(parseVersion(version).ok, `accepted: ${JSON.stringify(version)}`).toBe(true);
    }
    for (const version of PARITY_VECTORS.rejected) {
      expect(isValidVersion(version), `rejected: ${JSON.stringify(version)}`).toBe(false);
      expect(parseVersion(version).ok, `rejected: ${JSON.stringify(version)}`).toBe(false);
    }
  });

  it("rejects a version one character past the declared profile boundary", () => {
    const atBoundary = "1" + "0".repeat(123) + ".0.0";
    const overBoundary = "1" + "0".repeat(124) + ".0.0";
    expect(atBoundary.length).toBe(MAX_VERSION_CHARS);
    expect(overBoundary.length).toBe(MAX_VERSION_CHARS + 1);
    expect(isValidVersion(atBoundary)).toBe(true);
    expect(isValidVersion(overBoundary)).toBe(false);
  });

  it("rejects malformed versions rather than coercing them", () => {
    const malformed = [
      "",
      "1",
      "1.2",
      "1.2.3.4",
      "v1.2.3",
      "01.2.3",
      "1.02.3",
      "1.2.03",
      "1.2.3-",
      "1.2.3-01",
      "1.2.3-beta..1",
      "1.2.3 ",
      " 1.2.3",
      "1.2.3-β",
      "x".repeat(129),
    ];
    for (const value of malformed) {
      expect(isValidVersion(value), value.slice(0, 12)).toBe(false);
      expect(parseVersion(value).ok, value.slice(0, 12)).toBe(false);
    }
  });

  it("rejects non-string input", () => {
    for (const value of [null, undefined, 1, 1.5, ["1.2.3"], { version: "1.2.3" }]) {
      expect(isValidVersion(value)).toBe(false);
    }
  });

  it("implements SemVer precedence including prerelease ordering", () => {
    expect(compareVersions("1.0.0", "1.0.0")).toBe(0);
    expect(compareVersions("1.0.1", "1.0.0")).toBe(1);
    expect(compareVersions("1.0.0", "1.1.0")).toBe(-1);
    // Prerelease sorts below the release it precedes.
    expect(compareVersions("1.0.0-beta.1", "1.0.0")).toBe(-1);
    expect(compareVersions("1.0.0", "1.0.0-beta.1")).toBe(1);
    // Numeric identifiers compare numerically, not lexically.
    expect(compareVersions("1.0.0-beta.10", "1.0.0-beta.9")).toBe(1);
    // Fewer prerelease fields sort lower.
    expect(compareVersions("1.0.0-beta", "1.0.0-beta.1")).toBe(-1);
    // Build metadata never participates in precedence.
    expect(compareVersions("1.0.0+a", "1.0.0+b")).toBe(0);
  });

  it("fails closed on comparison of malformed input", () => {
    expect(compareVersions("1.0", "1.0.0")).toBeNull();
    expect(compareVersions("1.0.0", null)).toBeNull();
    expect(isStrictlyNewer("1.0", "0.9.0")).toBe(false);
  });

  it("compares very large numeric prerelease identifiers exactly", () => {
    // 2^53 is where JavaScript `Number()` stops distinguishing integers. These
    // are three distinct SemVer identifiers that a float comparison collapses.
    expect(compareVersions("1.0.0-beta.9007199254740993", "1.0.0-beta.9007199254740992")).toBe(1);
    expect(compareVersions("1.0.0-beta.9007199254740992", "1.0.0-beta.9007199254740993")).toBe(-1);
    expect(compareVersions("1.0.0-beta.9007199254740991", "1.0.0-beta.9007199254740992")).toBe(-1);
    expect(compareVersions("1.0.0-beta.9007199254740992", "1.0.0-beta.9007199254740992")).toBe(0);
    // A much longer identifier is a larger value, never a lexical accident.
    const huge = "1".repeat(40);
    expect(compareVersions(`1.0.0-beta.${huge}`, "1.0.0-beta.9007199254740991")).toBe(1);
    expect(compareVersions("1.0.0-beta.9007199254740991", `1.0.0-beta.${huge}`)).toBe(-1);
    // Equal-length huge identifiers still order exactly.
    const lower = `1${"0".repeat(30)}`;
    const higher = `1${"0".repeat(29)}1`;
    expect(compareVersions(`1.0.0-beta.${lower}`, `1.0.0-beta.${higher}`)).toBe(-1);
    expect(compareVersions(`1.0.0-beta.${higher}`, `1.0.0-beta.${lower}`)).toBe(1);
    // The exact order survives the eligibility helper too.
    expect(isStrictlyNewer("1.0.0-beta.9007199254740993", "1.0.0-beta.9007199254740992")).toBe(true);
    expect(isStrictlyNewer("1.0.0-beta.9007199254740992", "1.0.0-beta.9007199254740993")).toBe(false);
  });

  it("locks when canonical and mirrors agree exactly", () => {
    const verdict = evaluateVersionDrift("0.1.0", [
      { path: "a", version: "0.1.0" },
      { path: "b", version: "0.1.0" },
    ]);
    expect(verdict.ok).toBe(true);
  });

  it("detects missing, malformed and drifted mirrors", () => {
    expect(evaluateVersionDrift(null, [])).toMatchObject({ ok: false, reason: "missing_canonical_version" });
    expect(evaluateVersionDrift("v1", [])).toMatchObject({ ok: false, reason: "malformed_canonical_version" });
    expect(evaluateVersionDrift("0.1.0", [{ path: "a", version: null }])).toMatchObject({
      ok: false,
      reason: "missing_mirror_version",
    });
    expect(evaluateVersionDrift("0.1.0", [{ path: "a", version: "0.1" }])).toMatchObject({
      ok: false,
      reason: "malformed_mirror_version",
    });
    const drifted = evaluateVersionDrift("0.1.0", [{ path: "a", version: "0.2.0" }]);
    expect(drifted).toMatchObject({ ok: false, reason: "mirror_drift" });
    expect(drifted.ok === false && drifted.paths).toEqual(["a"]);
  });
});
