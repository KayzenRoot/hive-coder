export const DESKTOP_SNAPSHOT_SCHEMA_VERSION = 2 as const;

export type OperationalState = "READY" | "UNKNOWN" | "DISCONNECTED" | "DEGRADED";

export interface StatusSignal {
  state: OperationalState;
  label: string;
  detail: string;
  provenance: string;
}

export interface WorkspaceReadModel {
  signal: StatusSignal;
  selected: boolean;
  workspaceId: string | null;
  name: string | null;
  root: string | null;
  projectMarkers: string[];
  topLevelEntries: number;
  truncated: boolean;
}

export interface GitReadModel {
  signal: StatusSignal;
  repository: boolean;
  branch: string | null;
  head: string | null;
  detached: boolean;
}

export interface EvidenceReadModel {
  signal: StatusSignal;
  checkpoint: string | null;
  checkpointStatus: string | null;
  evidenceBundles: number;
  truncated: boolean;
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
    baselineCheckpoint: string;
  };
  shell: StatusSignal;
  workspace: WorkspaceReadModel;
  runtime: StatusSignal;
  provider: StatusSignal;
  git: GitReadModel;
  evidence: EvidenceReadModel;
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

function nullableString(value: unknown, field: string, max: number): string | null {
  if (value === null) return null;
  return boundedString(value, field, max);
}

function booleanField(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new Error(`invalid ${field}`);
  }
  return value;
}

function boundedInteger(value: unknown, field: string, max: number): number {
  if (!Number.isSafeInteger(value) || typeof value !== "number" || value < 0 || value > max) {
    throw new Error(`invalid ${field}`);
  }
  return value;
}

function stringList(value: unknown, field: string, maxItems: number, maxItemLength: number): string[] {
  if (!Array.isArray(value) || value.length > maxItems) {
    throw new Error(`invalid ${field}`);
  }
  return value.map((item, index) => boundedString(item, `${field}[${index}]`, maxItemLength));
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
    detail: boundedString(value.detail, `${field}.detail`, 320),
    provenance: boundedString(value.provenance, `${field}.provenance`, 120),
  };
}

function workspaceReadModel(value: unknown): WorkspaceReadModel {
  if (!isRecord(value)) throw new Error("invalid workspace");
  const selected = booleanField(value.selected, "workspace.selected");
  const workspace: WorkspaceReadModel = {
    signal: statusSignal(value.signal, "workspace.signal"),
    selected,
    workspaceId: nullableString(value.workspaceId, "workspace.workspaceId", 80),
    name: nullableString(value.name, "workspace.name", 120),
    root: nullableString(value.root, "workspace.root", 1024),
    projectMarkers: stringList(value.projectMarkers, "workspace.projectMarkers", 16, 80),
    topLevelEntries: boundedInteger(value.topLevelEntries, "workspace.topLevelEntries", 512),
    truncated: booleanField(value.truncated, "workspace.truncated"),
  };
  if (selected && (!workspace.workspaceId || !workspace.name || !workspace.root)) {
    throw new Error("selected workspace requires trusted identity and root");
  }
  if (!selected && (workspace.workspaceId !== null || workspace.name !== null || workspace.root !== null)) {
    throw new Error("unselected workspace cannot carry trusted identity");
  }
  return workspace;
}

function gitReadModel(value: unknown): GitReadModel {
  if (!isRecord(value)) throw new Error("invalid git");
  const model: GitReadModel = {
    signal: statusSignal(value.signal, "git.signal"),
    repository: booleanField(value.repository, "git.repository"),
    branch: nullableString(value.branch, "git.branch", 220),
    head: nullableString(value.head, "git.head", 64),
    detached: booleanField(value.detached, "git.detached"),
  };
  if (model.head !== null && !/^[0-9a-f]{40}([0-9a-f]{24})?$/.test(model.head)) {
    throw new Error("invalid git.head");
  }
  if (!model.repository && (model.branch !== null || model.head !== null || model.detached)) {
    throw new Error("non-repository Git state cannot carry repository identity");
  }
  if (model.detached && model.branch !== null) {
    throw new Error("detached Git state cannot carry a branch");
  }
  return model;
}

function evidenceReadModel(value: unknown): EvidenceReadModel {
  if (!isRecord(value)) throw new Error("invalid evidence");
  return {
    signal: statusSignal(value.signal, "evidence.signal"),
    checkpoint: nullableString(value.checkpoint, "evidence.checkpoint", 80),
    checkpointStatus: nullableString(value.checkpointStatus, "evidence.checkpointStatus", 120),
    evidenceBundles: boundedInteger(value.evidenceBundles, "evidence.evidenceBundles", 128),
    truncated: booleanField(value.truncated, "evidence.truncated"),
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
      baselineCheckpoint: boundedString(value.product.baselineCheckpoint, "product.baselineCheckpoint", 80),
    },
    shell: statusSignal(value.shell, "shell"),
    workspace: workspaceReadModel(value.workspace),
    runtime: statusSignal(value.runtime, "runtime"),
    provider: statusSignal(value.provider, "provider"),
    git: gitReadModel(value.git),
    evidence: evidenceReadModel(value.evidence),
    permission: statusSignal(value.permission, "permission"),
    safety: {
      actionableSession: booleanField(value.safety.actionableSession, "safety.actionableSession"),
      pause: booleanField(value.safety.pause, "safety.pause"),
      emergencyStop: booleanField(value.safety.emergencyStop, "safety.emergencyStop"),
      takeControl: booleanField(value.safety.takeControl, "safety.takeControl"),
      detail: boundedString(value.safety.detail, "safety.detail", 320),
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
      baselineCheckpoint: "HCODER-CP-0015",
    },
    shell: {
      state: "DEGRADED",
      label: "Desktop bridge",
      detail: "The native read-model bridge is unavailable; privileged actions remain disabled.",
      provenance: "local-fallback",
    },
    workspace: {
      signal: unavailable("Workspace", "DISCONNECTED"),
      selected: false,
      workspaceId: null,
      name: null,
      root: null,
      projectMarkers: [],
      topLevelEntries: 0,
      truncated: false,
    },
    runtime: unavailable("Runtime", "DISCONNECTED"),
    provider: unavailable("Provider"),
    git: {
      signal: unavailable("Git"),
      repository: false,
      branch: null,
      head: null,
      detached: false,
    },
    evidence: {
      signal: unavailable("Evidence"),
      checkpoint: null,
      checkpointStatus: null,
      evidenceBundles: 0,
      truncated: false,
    },
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
