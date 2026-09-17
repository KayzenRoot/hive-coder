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

/** Official SemVer 2.0.0 pattern, anchored. */
const SEMVER_PATTERN =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$/;

export interface ParsedVersion {
  readonly major: number;
  readonly minor: number;
  readonly patch: number;
  /** Prerelease identifiers, or `null` when the version has no prerelease. */
  readonly prerelease: readonly string[] | null;
  /** Build metadata identifiers, or `null`. Never participates in precedence. */
  readonly build: readonly string[] | null;
}

export type VersionParseResult =
  | { readonly ok: true; readonly version: ParsedVersion }
  | { readonly ok: false; readonly reason: "malformed_version" };

/**
 * Strict SemVer 2.0.0 parse. Malformed input fails closed; it is never coerced,
 * trimmed, defaulted or partially accepted.
 */
export function parseVersion(value: unknown): VersionParseResult {
  if (typeof value !== "string" || value.length === 0 || value.length > MAX_VERSION_CHARS) {
    return { ok: false, reason: "malformed_version" };
  }
  const match = SEMVER_PATTERN.exec(value);
  if (match === null) {
    return { ok: false, reason: "malformed_version" };
  }
  const major = Number(match[1]);
  const minor = Number(match[2]);
  const patch = Number(match[3]);
  if (!Number.isSafeInteger(major) || !Number.isSafeInteger(minor) || !Number.isSafeInteger(patch)) {
    return { ok: false, reason: "malformed_version" };
  }
  return {
    ok: true,
    version: {
      major,
      minor,
      patch,
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
 * Exact numeric-identifier comparison.
 *
 * A SemVer numeric prerelease identifier is an arbitrary-precision unsigned
 * integer. Converting it with `Number()` collapses every value above 2^53 onto
 * the same double, so two distinct identifiers — for example `9007199254740993`
 * and `9007199254740992` — would compare equal and silently corrupt same-channel
 * upgrade/downgrade eligibility. The digit strings are therefore compared by
 * length and then lexically, which is exact because parsing admits no leading
 * zeros in a numeric identifier and therefore length is the value's magnitude.
 */
function compareNumericIdentifier(left: string, right: string): number {
  if (left.length !== right.length) return left.length < right.length ? -1 : 1;
  return left === right ? 0 : left < right ? -1 : 1;
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
    if (a.version[key] !== b.version[key]) return a.version[key] < b.version[key] ? -1 : 1;
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
