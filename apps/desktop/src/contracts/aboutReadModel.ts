/**
 * Bounded Settings/About read model (HCODER-WO-0024 / HCODER-DIST-001A).
 *
 * Presentation-only, read-only state for a future Settings/About surface showing
 * the product version, the selected release channel and the current update
 * status. It carries no authority, triggers no side effect and performs no update
 * check, download, install, notification or redesign.
 *
 * Deliberately free of any UI framework import so it stays testable in isolation
 * and compatible with later UX/i18n work (Issue #71) without expanding into it.
 */

import {
  CHANNEL_PRODUCT_LABEL,
  isReleaseChannel,
  versionMatchesChannel,
  type ReleaseChannel,
} from "./releaseChannel";
import { evaluateStatus, type UpdateState, type UpdateStatus } from "./updateState";
import { isValidVersion } from "./version";

export const ABOUT_READ_MODEL_SCHEMA = "hive-about-v1" as const;

export const MAX_ABOUT_PRODUCT_NAME_CHARS = 64;

export interface AboutReadModel {
  readonly schema: typeof ABOUT_READ_MODEL_SCHEMA;
  readonly productName: string;
  readonly version: string;
  readonly channel: ReleaseChannel;
  readonly channelLabel: string;
  readonly update: {
    readonly available: boolean;
    readonly availabilityReason: string;
    readonly state: UpdateState;
  };
}

export type AboutVerdict =
  | { readonly ok: true; readonly model: AboutReadModel }
  | { readonly ok: false; readonly reason: "invalid_about_model" };

export interface AboutInput {
  readonly productName: unknown;
  readonly version: unknown;
  readonly channel: unknown;
  readonly status: unknown;
}

/**
 * Build and validate the bounded read model. Every field is bounded; an unknown
 * channel or malformed version fails closed rather than being displayed.
 *
 * The model carries one identity, so its own version and channel must agree with
 * each other *and* with the validated status snapshot. Displaying a version that
 * does not belong to the displayed channel, or a version the update status
 * contradicts, would misrepresent the installed product.
 */
export function buildAboutReadModel(input: AboutInput): AboutVerdict {
  const { productName, version, channel, status } = input;
  if (typeof productName !== "string" || productName.length === 0 || productName.length > MAX_ABOUT_PRODUCT_NAME_CHARS) {
    return { ok: false, reason: "invalid_about_model" };
  }
  if (!isValidVersion(version)) {
    return { ok: false, reason: "invalid_about_model" };
  }
  if (!isReleaseChannel(channel)) {
    return { ok: false, reason: "invalid_about_model" };
  }
  if (!versionMatchesChannel(version, channel)) {
    return { ok: false, reason: "invalid_about_model" };
  }
  const statusVerdict = evaluateStatus(status);
  if (!statusVerdict.ok) {
    return { ok: false, reason: "invalid_about_model" };
  }
  const typedStatus: UpdateStatus = statusVerdict.status;
  if (typedStatus.currentVersion !== version || typedStatus.channel !== channel) {
    return { ok: false, reason: "invalid_about_model" };
  }
  return {
    ok: true,
    model: {
      schema: ABOUT_READ_MODEL_SCHEMA,
      productName,
      version,
      channel,
      channelLabel: CHANNEL_PRODUCT_LABEL[channel],
      update: {
        available: false,
        availabilityReason: typedStatus.error === null ? "not_configured" : typedStatus.error.code,
        state: typedStatus.state,
      },
    },
  };
}
