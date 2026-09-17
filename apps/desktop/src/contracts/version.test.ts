import { describe, expect, it } from "vitest";

import {
  CANONICAL_VERSION_SOURCE,
  MAX_CORE_IDENTIFIER,
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

  it("bounds core identifiers to the narrowest declared toolchain consumer", () => {
    // The canonical version is mirrored into Cargo.toml and package.json. Cargo's
    // Rust SemVer accepts core values up to u64::MAX, but npm's node-semver
    // rejects any core component above Number.MAX_SAFE_INTEGER, so npm fixes the
    // profile: every value the product accepts must be parseable by every mirror.
    expect(MAX_CORE_IDENTIFIER).toBe("9007199254740991");
    expect(MAX_CORE_IDENTIFIER).toBe(String(Number.MAX_SAFE_INTEGER));

    for (const version of [
      "9007199254740990.0.0",
      "9007199254740991.0.0",
      "0.9007199254740991.0",
      "0.0.9007199254740991",
      "9007199254740991.9007199254740991.9007199254740991",
    ]) {
      expect(isValidVersion(version), version).toBe(true);
      expect(parseVersion(version).ok, version).toBe(true);
    }

    // One past the bound, in every core position.
    for (const version of [
      "9007199254740992.0.0",
      "9007199254740993.0.0",
      "0.9007199254740992.0",
      "0.0.9007199254740992",
      "9007199254740992.9007199254740992.9007199254740992",
    ]) {
      expect(isValidVersion(version), version).toBe(false);
      expect(parseVersion(version).ok, version).toBe(false);
    }
  });

  it("rejects core values that only a wider consumer would accept", () => {
    // Cargo's u64 range is wider than npm's; the profile follows the narrower
    // consumer, so these are refused by the product contract.
    for (const version of [
      "18446744073709551615.0.0",
      "18446744073709551616.0.0",
      "123456789012345678901234567890.0.0",
      "1.123456789012345678901234567890.0",
      "1.0.123456789012345678901234567890",
    ]) {
      expect(isValidVersion(version), version).toBe(false);
      expect(parseVersion(version).ok, version).toBe(false);
    }
    // The former oversized-core boundary vector is a rejection case now.
    const formerBoundary = "1" + "0".repeat(123) + ".0.0";
    expect(formerBoundary.length).toBe(MAX_VERSION_CHARS);
    expect(isValidVersion(formerBoundary)).toBe(false);
  });

  it("orders accepted core values exactly, without precision collapse", () => {
    const parsed = parseVersion("9007199254740991.0.0");
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    // Exact decimal strings survive parsing; nothing was rounded.
    expect(parsed.version.major).toBe("9007199254740991");
    expect(compareVersions("9007199254740991.0.0", "9007199254740990.0.0")).toBe(1);
    expect(compareVersions("9007199254740990.0.0", "9007199254740991.0.0")).toBe(-1);
    expect(compareVersions("9007199254740991.0.0", "9007199254740991.0.0")).toBe(0);
    expect(compareVersions("9007199254740991.9007199254740991.0", "9007199254740991.9007199254740990.0")).toBe(1);
    expect(compareVersions("9007199254740991.0.9007199254740991", "9007199254740991.0.9007199254740990")).toBe(1);
    expect(isStrictlyNewer("9007199254740991.0.0", "9007199254740990.0.0")).toBe(true);
    expect(isStrictlyNewer("9007199254740990.0.0", "9007199254740991.0.0")).toBe(false);
    // Values beyond the bound are unparseable, so precedence fails closed.
    expect(compareVersions("9007199254740992.0.0", "9007199254740991.0.0")).toBeNull();
  });

  it("agrees with the shared cross-language parity vectors", () => {
    expect(PARITY_VECTORS.profile.maxVersionChars).toBe(MAX_VERSION_CHARS);
    expect(PARITY_VECTORS.profile.coreMax).toBe(MAX_CORE_IDENTIFIER);
    expect(PARITY_VECTORS.profile.law).toBe("toolchain-compatible bounded SemVer 2.0.0");
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

  it("enforces the declared profile length using legal non-core content", () => {
    const prefix = "1.0.0-alpha.";
    const atBoundary = prefix + "b".repeat(MAX_VERSION_CHARS - prefix.length);
    const overBoundary = prefix + "b".repeat(MAX_VERSION_CHARS + 1 - prefix.length);
    expect(atBoundary.length).toBe(MAX_VERSION_CHARS);
    expect(overBoundary.length).toBe(MAX_VERSION_CHARS + 1);
    expect(isValidVersion(atBoundary), atBoundary).toBe(true);
    expect(isValidVersion(overBoundary), overBoundary).toBe(false);
    // The bound is on the whole string, not on the identifier that fills it.
    expect(isValidVersion(prefix + "b".repeat(MAX_VERSION_CHARS - prefix.length - 1))).toBe(true);
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
