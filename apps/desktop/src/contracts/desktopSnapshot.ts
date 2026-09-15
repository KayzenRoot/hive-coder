export const DESKTOP_SNAPSHOT_SCHEMA_VERSION = 1 as const;

export type OperationalState = "READY" | "UNKNOWN" | "DISCONNECTED" | "DEGRADED";

export interface StatusSignal {
  state: OperationalState;
  label: string;
  detail: string;
  provenance: string;
}

export interface SafetyAvailability {
  actionableSession: boolean;
  pause: boolean;
  emergencyStop: boolean;
  takeControl: boolean;
  detail: string;
}

export interface DesktopSnapshot {
  schemaVersion: typeof DESKTOP_SNAPSHOT_SCHEMA_VERSION;
  product: {
    name: string;
    version: string;
    checkpoint: string;
  };
  shell: StatusSignal;
  runtime: StatusSignal;
  provider: StatusSignal;
  git: StatusSignal;
  evidence: StatusSignal;
  permission: StatusSignal;
  safety: SafetyAvailability;
}

const STATES = new Set<OperationalState>([
  "READY",
  "UNKNOWN",
  "DISCONNECTED",
  "DEGRADED",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function boundedString(value: unknown, field: string, max = 240): string {
  if (typeof value !== "string") {
    throw new Error(`invalid ${field}`);
  }
  const normalized = value.trim();
  if (normalized.length === 0 || normalized.length > max) {
    throw new Error(`invalid ${field}`);
  }
  return normalized;
}

function booleanField(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new Error(`invalid ${field}`);
  }
  return value;
}

function statusSignal(value: unknown, field: string): StatusSignal {
  if (!isRecord(value)) {
    throw new Error(`invalid ${field}`);
  }
  const state = boundedString(value.state, `${field}.state`, 32) as OperationalState;
  if (!STATES.has(state)) {
    throw new Error(`invalid ${field}.state`);
  }
  return {
    state,
    label: boundedString(value.label, `${field}.label`, 80),
    detail: boundedString(value.detail, `${field}.detail`, 240),
    provenance: boundedString(value.provenance, `${field}.provenance`, 120),
  };
}

export function parseDesktopSnapshot(value: unknown): DesktopSnapshot {
  if (!isRecord(value)) {
    throw new Error("invalid desktop snapshot");
  }
  if (value.schemaVersion !== DESKTOP_SNAPSHOT_SCHEMA_VERSION) {
    throw new Error("unsupported desktop snapshot schema");
  }
  if (!isRecord(value.product) || !isRecord(value.safety)) {
    throw new Error("invalid desktop snapshot envelope");
  }

  const snapshot: DesktopSnapshot = {
    schemaVersion: DESKTOP_SNAPSHOT_SCHEMA_VERSION,
    product: {
      name: boundedString(value.product.name, "product.name", 80),
      version: boundedString(value.product.version, "product.version", 40),
      checkpoint: boundedString(value.product.checkpoint, "product.checkpoint", 80),
    },
    shell: statusSignal(value.shell, "shell"),
    runtime: statusSignal(value.runtime, "runtime"),
    provider: statusSignal(value.provider, "provider"),
    git: statusSignal(value.git, "git"),
    evidence: statusSignal(value.evidence, "evidence"),
    permission: statusSignal(value.permission, "permission"),
    safety: {
      actionableSession: booleanField(value.safety.actionableSession, "safety.actionableSession"),
      pause: booleanField(value.safety.pause, "safety.pause"),
      emergencyStop: booleanField(value.safety.emergencyStop, "safety.emergencyStop"),
      takeControl: booleanField(value.safety.takeControl, "safety.takeControl"),
      detail: boundedString(value.safety.detail, "safety.detail", 240),
    },
  };

  if (!snapshot.safety.actionableSession && (snapshot.safety.pause || snapshot.safety.emergencyStop || snapshot.safety.takeControl)) {
    throw new Error("safety actions cannot be available without an actionable session");
  }

  return snapshot;
}

export function disconnectedSnapshot(): DesktopSnapshot {
  const unavailable = (label: string, state: OperationalState = "UNKNOWN"): StatusSignal => ({
    state,
    label,
    detail: "No trusted live observation is available in this desktop session.",
    provenance: "local-fallback",
  });

  return {
    schemaVersion: DESKTOP_SNAPSHOT_SCHEMA_VERSION,
    product: {
      name: "Hive Coder",
      version: "0.1.0",
      checkpoint: "HCODER-CP-0014",
    },
    shell: {
      state: "DEGRADED",
      label: "Desktop bridge",
      detail: "The native read-model bridge is unavailable; privileged actions remain disabled.",
      provenance: "local-fallback",
    },
    runtime: unavailable("Runtime", "DISCONNECTED"),
    provider: unavailable("Provider"),
    git: unavailable("Git"),
    evidence: unavailable("Evidence"),
    permission: unavailable("Permission plane"),
    safety: {
      actionableSession: false,
      pause: false,
      emergencyStop: false,
      takeControl: false,
      detail: "No actionable trusted session is connected.",
    },
  };
}
