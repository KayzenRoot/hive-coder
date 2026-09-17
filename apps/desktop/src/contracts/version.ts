/**
 * Canonical Hive Coder product-version contract (HCODER-WO-0024 / HCODER-DIST-001A).
 *
 * Source-of-truth law: exactly one canonical version source exists —
 * `apps/desktop/src-tauri/tauri.conf.json` -> `version`. The Tauri application
 * version identifies the shipped product artifact and is the version a future
 * updater compares against. The Rust package version and the npm package version
 * are *mirrors*: they must equal the canonical value exactly and must never be
 * edited independently. `tools/desktop/version_drift.py` enforces that.
 *
 * This module is pure: no network, no filesystem, no process, no updater and no
 * side effect of any kind.
 */

export const VERSION_CONTRACT = "hive-version-v1" as const;

/** The single canonical product-version source of truth. */
export const CANONICAL_VERSION_SOURCE = "apps/desktop/src-tauri/tauri.conf.json" as const;

/** Manifests that mirror the canonical version and must never diverge. */
export const VERSION_MIRRORS = ["apps/desktop/src-tauri/Cargo.toml", "apps/desktop/package.json"] as const;

export const MAX_VERSION_CHARS = 128;

/**
 * Largest core identifier this profile accepts, as an exact decimal string.
 * Equal to JavaScript's `Number.MAX_SAFE_INTEGER`.
 *
 * The bound is a real toolchain constraint, not a stylistic choice: the canonical
 * version is mirrored into `Cargo.toml` and `package.json`, and the npm surface
 * (`node-semver`) rejects a core component above this value. Cargo's `u64` range
 * is wider, so npm is the narrowest declared consumer and therefore fixes the
 * profile. A version this product accepts must be a version every mirror
 * consumer can parse.
 */
export const MAX_CORE_IDENTIFIER = "9007199254740991";

/**
 * Declared acceptance profile: **toolchain-compatible bounded SemVer 2.0.0**.
 *
 * The accepted set is the SemVer 2.0.0 grammar restricted by two project bounds:
 * each core identifier must lie in `0..MAX_CORE_IDENTIFIER`, and the whole
 * version string must be at most `MAX_VERSION_CHARS` characters. Both bounds are
 * part of the law rather than implementation details; they are enforced
 * identically by this parser, by the Python drift gate and by the shared parity
 * vector file, and they are stated as a bounded profile so that no implementation
 * drifts into claiming unqualified SemVer acceptance.
 *
 * Numeric prerelease identifiers are *not* subject to the core bound: they are
 * compared and carried exactly, at any length, within the overall string bound.
 *
 * Official SemVer 2.0.0 pattern, anchored, ASCII digits only.
 */
const SEMVER_PATTERN =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;

export interface ParsedVersion {
  /**
   * Major identifier as an exact decimal string, already proven to lie within
   * `0..MAX_CORE_IDENTIFIER`. Core identifiers are kept as strings on purpose: a
   * core identifier is a decimal integer, and `Number()` would both round values
   * above 2^53 and blur the bound check into a platform-dependent coercion.
   */
  readonly major: string;
  /** Minor identifier as an exact decimal string, within the same bound. */
  readonly minor: string;
  /** Patch identifier as an exact decimal string, within the same bound. */
  readonly patch: string;
  /** Prerelease identifiers, or `null` when the version has no prerelease. */
  readonly prerelease: readonly string[] | null;
  /** Build metadata identifiers, or `null`. Never participates in precedence. */
  readonly build: readonly string[] | null;
}

export type VersionParseResult =
  | { readonly ok: true; readonly version: ParsedVersion }
  | { readonly ok: false; readonly reason: "malformed_version" };

/**
 * Strict SemVer 2.0.0 parse under the declared bounded profile. Malformed input
 * fails closed; it is never coerced, trimmed, defaulted or partially accepted.
 * The core bound is applied on the digit strings themselves, so no numeric
 * conversion and no platform-dependent integer coercion is involved.
 */
export function parseVersion(value: unknown): VersionParseResult {
  if (typeof value !== "string" || value.length === 0 || value.length > MAX_VERSION_CHARS) {
    return { ok: false, reason: "malformed_version" };
  }
  const match = SEMVER_PATTERN.exec(value);
  if (match === null) {
    return { ok: false, reason: "malformed_version" };
  }
  if (!isWithinCoreBound(match[1]) || !isWithinCoreBound(match[2]) || !isWithinCoreBound(match[3])) {
    return { ok: false, reason: "malformed_version" };
  }
  return {
    ok: true,
    version: {
      major: match[1],
      minor: match[2],
      patch: match[3],
      prerelease: match[4] === undefined ? null : match[4].split("."),
      build: match[5] === undefined ? null : match[5].split("."),
    },
  };
}

/** Strict SemVer 2.0.0 acceptance. Malformed input fails closed. */
export function isValidVersion(value: unknown): value is string {
  return parseVersion(value).ok;
}

/**
 * Exact numeric-identifier comparison, used for both core identifiers
 * (`major`/`minor`/`patch`) and numeric prerelease identifiers.
 *
 * A SemVer numeric identifier is a decimal integer with no leading zeros. It is
 * compared on the digit strings themselves — first by length, then
 * lexicographically — which is exact at any magnitude and involves no
 * floating-point conversion. `Number()` would collapse distinct identifiers above
 * 2^53 onto the same double and silently corrupt ordering, and it would blur the
 * core bound check into a platform-dependent coercion.
 */
function compareNumericIdentifier(left: string, right: string): number {
  if (left.length !== right.length) return left.length < right.length ? -1 : 1;
  return left === right ? 0 : left < right ? -1 : 1;
}

/**
 * Core-bound check on the digit string, without numeric conversion. Parsing has
 * already rejected leading zeros, so a shorter digit string is always a smaller
 * value and equal-length strings compare lexically.
 */
function isWithinCoreBound(identifier: string): boolean {
  return compareNumericIdentifier(identifier, MAX_CORE_IDENTIFIER) <= 0;
}

function compareIdentifier(left: string, right: string): number {
  const leftNumeric = /^\d+$/.test(left);
  const rightNumeric = /^\d+$/.test(right);
  if (leftNumeric && rightNumeric) {
    return compareNumericIdentifier(left, right);
  }
  if (leftNumeric) return -1;
  if (rightNumeric) return 1;
  return left === right ? 0 : left < right ? -1 : 1;
}

/**
 * SemVer 2.0.0 precedence comparison. Build metadata is ignored. Both inputs
 * must already be valid; malformed input yields `null` so callers fail closed.
 */
export function compareVersions(left: unknown, right: unknown): number | null {
  const a = parseVersion(left);
  const b = parseVersion(right);
  if (!a.ok || !b.ok) return null;
  for (const key of ["major", "minor", "patch"] as const) {
    const coreResult = compareNumericIdentifier(a.version[key], b.version[key]);
    if (coreResult !== 0) return coreResult;
  }
  const ap = a.version.prerelease;
  const bp = b.version.prerelease;
  if (ap === null && bp === null) return 0;
  if (ap === null) return 1;
  if (bp === null) return -1;
  const length = Math.max(ap.length, bp.length);
  for (let index = 0; index < length; index += 1) {
    const leftIdentifier = ap[index];
    const rightIdentifier = bp[index];
    if (leftIdentifier === undefined) return -1;
    if (rightIdentifier === undefined) return 1;
    const result = compareIdentifier(leftIdentifier, rightIdentifier);
    if (result !== 0) return result;
  }
  return 0;
}

export function isStrictlyNewer(candidate: unknown, current: unknown): boolean {
  const comparison = compareVersions(candidate, current);
  return comparison !== null && comparison > 0;
}

export interface MirrorObservation {
  readonly path: string;
  readonly version: string | null;
}

export type DriftVerdict =
  | { readonly ok: true }
  | { readonly ok: false; readonly reason: DriftReason; readonly paths: readonly string[] };

export type DriftReason =
  | "malformed_canonical_version"
  | "missing_canonical_version"
  | "missing_mirror_version"
  | "malformed_mirror_version"
  | "mirror_drift";

/**
 * Deterministic drift law. A mirror is correct only when it parses as strict
 * SemVer and equals the canonical version exactly. Anything else is drift.
 */
export function evaluateVersionDrift(
  canonical: string | null,
  mirrors: readonly MirrorObservation[],
): DriftVerdict {
  if (canonical === null) {
    return { ok: false, reason: "missing_canonical_version", paths: [CANONICAL_VERSION_SOURCE] };
  }
  if (!isValidVersion(canonical)) {
    return { ok: false, reason: "malformed_canonical_version", paths: [CANONICAL_VERSION_SOURCE] };
  }
  const missing = mirrors.filter((mirror) => mirror.version === null).map((mirror) => mirror.path);
  if (missing.length > 0) {
    return { ok: false, reason: "missing_mirror_version", paths: missing };
  }
  const malformed = mirrors.filter((mirror) => !isValidVersion(mirror.version)).map((mirror) => mirror.path);
  if (malformed.length > 0) {
    return { ok: false, reason: "malformed_mirror_version", paths: malformed };
  }
  const drifted = mirrors.filter((mirror) => mirror.version !== canonical).map((mirror) => mirror.path);
  if (drifted.length > 0) {
    return { ok: false, reason: "mirror_drift", paths: drifted };
  }
  return { ok: true };
}
