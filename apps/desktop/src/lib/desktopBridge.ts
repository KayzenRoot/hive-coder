import { invoke } from "@tauri-apps/api/core";
import {
  type DesktopSnapshot,
  disconnectedSnapshot,
  parseDesktopSnapshot,
} from "../contracts/desktopSnapshot";
import {
  decodeRuntimeStatusEnvelope,
  type RuntimeStatusEnvelope,
} from "../contracts/runtimeStatus";
import { evaluateStatus, type UpdateStatus } from "../contracts/updateState";

const SNAPSHOT_COMMAND = "get_desktop_snapshot" as const;
const CHOOSE_WORKSPACE_COMMAND = "choose_workspace" as const;
const RUNTIME_STATUS_COMMAND = "get_runtime_status_envelope" as const;
const UPDATE_STATUS_COMMAND = "get_update_status" as const;
const UPDATE_CHECK_COMMAND = "check_for_update" as const;
const UPDATE_DOWNLOAD_COMMAND = "download_update_candidate" as const;

/**
 * Bounded bridge failure. The reason vocabulary is closed and carries no remote
 * response body, URL, signature or credential, so a failure cannot smuggle
 * untrusted data into product state.
 */
export type UpdateBridgeFailureReason = "invoke_failed" | "invalid_status";

export class UpdateBridgeError extends Error {
  public readonly reason: UpdateBridgeFailureReason;

  public constructor(reason: UpdateBridgeFailureReason) {
    super(`update bridge failed: ${reason}`);
    this.name = "UpdateBridgeError";
    this.reason = reason;
  }
}

/**
 * Each update operation is its own named, argument-free call against its own
 * literal command name. A shared helper that took a command name would turn
 * these three bindings back into a generic invoke surface the caller controls.
 *
 * Every command answers with a `hive-update-state-v1` snapshot, and the only
 * route into product state is `evaluateStatus`: raw wire the contract refuses is
 * discarded, never partially read.
 */
export async function readUpdateStatus(): Promise<UpdateStatus> {
  let raw: unknown;
  try {
    raw = await invoke(UPDATE_STATUS_COMMAND);
  } catch {
    throw new UpdateBridgeError("invoke_failed");
  }
  return admitUpdateStatus(raw);
}

export async function requestUpdateCheck(): Promise<UpdateStatus> {
  let raw: unknown;
  try {
    raw = await invoke(UPDATE_CHECK_COMMAND);
  } catch {
    throw new UpdateBridgeError("invoke_failed");
  }
  return admitUpdateStatus(raw);
}

export async function requestUpdateCandidateDownload(): Promise<UpdateStatus> {
  let raw: unknown;
  try {
    raw = await invoke(UPDATE_DOWNLOAD_COMMAND);
  } catch {
    throw new UpdateBridgeError("invoke_failed");
  }
  return admitUpdateStatus(raw);
}

function admitUpdateStatus(raw: unknown): UpdateStatus {
  const verdict = evaluateStatus(raw);
  if (!verdict.ok) {
    throw new UpdateBridgeError("invalid_status");
  }
  return verdict.status;
}

export async function loadDesktopSnapshot(): Promise<DesktopSnapshot> {
  try {
    const raw: unknown = await invoke(SNAPSHOT_COMMAND);
    return parseDesktopSnapshot(raw);
  } catch {
    return disconnectedSnapshot();
  }
}

export async function chooseWorkspace(): Promise<DesktopSnapshot> {
  const raw: unknown = await invoke(CHOOSE_WORKSPACE_COMMAND);
  return parseDesktopSnapshot(raw);
}

export async function loadRuntimeStatusEnvelope(): Promise<RuntimeStatusEnvelope | null> {
  try {
    const raw: unknown = await invoke(RUNTIME_STATUS_COMMAND);
    if (typeof raw !== "string") return null;
    return decodeRuntimeStatusEnvelope(raw);
  } catch {
    return null;
  }
}
