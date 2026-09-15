import type { DesktopSnapshot, OperationalState, StatusSignal } from "../contracts/desktopSnapshot";
import type { RuntimeStatusEnvelope } from "../contracts/runtimeStatus";
import { HiveMark } from "./HiveMark";

const NAV_ITEMS = ["Workspace", "Tasks", "Code", "Computer", "Evidence"] as const;

function StateDot({ state }: { state: OperationalState }) {
  return <span className={`state-dot state-dot--${state.toLowerCase()}`} aria-hidden="true" />;
}

function StatusCard({ signal }: { signal: StatusSignal }) {
  return (
    <article className="status-card">
      <div className="status-card__head">
        <span>{signal.label}</span>
        <span className={`state-chip state-chip--${signal.state.toLowerCase()}`}>
          <StateDot state={signal.state} />
          {signal.state}
        </span>
      </div>
      <p>{signal.detail}</p>
      <span className="status-card__provenance">{signal.provenance}</span>
    </article>
  );
}

function SafetyButton({ label, enabled, kind = "default" }: { label: string; enabled: boolean; kind?: "default" | "danger" }) {
  return (
    <button className={`safety-button safety-button--${kind}`} type="button" disabled={!enabled} aria-disabled={!enabled}>
      {label}
    </button>
  );
}

interface ShellViewProps {
  snapshot: DesktopSnapshot;
  runtimeStatus?: RuntimeStatusEnvelope | null;
  choosingWorkspace?: boolean;
  workspaceError?: string | null;
  onChooseWorkspace?: () => void | Promise<void>;
}

function shortHead(head: string | null): string {
  return head ? head.slice(0, 12) : "Unavailable";
}

function providerStateFromRuntime(live: RuntimeStatusEnvelope["snapshot"]): OperationalState {
  if (live.runtime.state === "DISCONNECTED") return "DISCONNECTED";
  if (live.providers.some((provider) => provider.state === "DEGRADED")) return "DEGRADED";
  if (live.providers.some((provider) => provider.state === "READY")) return "READY";
  if (live.providers.some((provider) => provider.state === "UNKNOWN")) return "UNKNOWN";
  if (live.providers.some((provider) => provider.state === "DISCONNECTED")) return "DISCONNECTED";
  return "UNKNOWN";
}

function permissionDetailFromRuntime(permission: RuntimeStatusEnvelope["snapshot"]["permission"]): string {
  if (permission.state !== "READY") {
    return "No actionable permission authority is exposed through the runtime status channel.";
  }
  if (permission.activeSessions === null || permission.pendingApprovals === null) {
    return "Permission observer reports READY; session/approval counters are not exposed.";
  }
  return `Read-only status: ${permission.activeSessions} active session(s), ${permission.pendingApprovals} pending approval(s).`;
}

export function ShellView({
  snapshot,
  runtimeStatus = null,
  choosingWorkspace = false,
  workspaceError = null,
  onChooseWorkspace,
}: ShellViewProps) {
  const live = runtimeStatus?.snapshot ?? null;
  const runtimeSignal: StatusSignal = live
    ? { state: live.runtime.state, label: "Runtime", detail: live.runtime.detail, provenance: live.runtime.provenance }
    : snapshot.runtime;
  const providerModels = live?.providers.reduce((total, provider) => total + provider.modelIds.length, 0) ?? 0;
  const providerSignal: StatusSignal = live
    ? {
        state: providerStateFromRuntime(live),
        label: "Provider",
        detail: live.providers.length > 0
          ? `${live.providers.length} provider${live.providers.length === 1 ? "" : "s"} / ${providerModels} observed model${providerModels === 1 ? "" : "s"}. Catalog observation is not reachability, authentication or VERIFIED capability evidence.`
          : "No provider catalog is connected through the runtime status channel.",
        provenance: live.providers[0]?.provenance ?? "hive-provider-catalog",
      }
    : snapshot.provider;
  const permissionSignal: StatusSignal = live
    ? {
        state: live.permission.state,
        label: "Permission plane",
        detail: permissionDetailFromRuntime(live.permission),
        provenance: live.permission.provenance,
      }
    : snapshot.permission;
  const statusSignals = [runtimeSignal, providerSignal, snapshot.git.signal, snapshot.evidence.signal, permissionSignal];
  const workspaceName = snapshot.workspace.name ?? "No workspace selected";
  const workspaceRoot = snapshot.workspace.root ?? "Choose a folder explicitly to establish trusted read-only project context.";
  const branch = snapshot.git.detached ? "Detached HEAD" : snapshot.git.branch ?? "Unavailable";

  return (
    <main className="app-shell">
      <aside className="rail" aria-label="Primary navigation">
        <div className="rail__brand"><HiveMark compact /></div>
        <nav className="rail__nav">
          {NAV_ITEMS.map((item, index) => {
            const active = index === 0;
            return (
              <button
                key={item}
                className={active ? "rail-button rail-button--active" : "rail-button"}
                type="button"
                disabled={!active}
                aria-disabled={!active}
                aria-current={active ? "page" : undefined}
              >
                <span className="rail-button__glyph" aria-hidden="true">{item.slice(0, 1)}</span>
                <span>{item}</span>
              </button>
            );
          })}
        </nav>
        <div className="rail__footer"><span className="avatar">K</span></div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <div className="eyebrow">HIVE WORKSPACE</div>
            <h1>{snapshot.product.name}</h1>
          </div>
          <div className="topbar__meta">
            <span className="read-only-pill"><span className="read-only-pill__dot" />TRUSTED READ MODE</span>
            <span className="checkpoint">BASE {snapshot.product.baselineCheckpoint}</span>
          </div>
        </header>

        <div className="content-grid">
          <section className="project-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">CURRENT WORKSPACE</span>
                <h2>{workspaceName}</h2>
              </div>
              <span className={`state-chip state-chip--${snapshot.workspace.signal.state.toLowerCase()}`}>
                <StateDot state={snapshot.workspace.signal.state} />
                {snapshot.workspace.signal.state}
              </span>
            </div>

            <div className="project-card">
              <div className="project-card__top">
                <HiveMark />
                <div className="project-card__identity">
                  <span className="project-card__label">{snapshot.workspace.selected ? "Trusted workspace" : "Workspace boundary"}</span>
                  <h3>{workspaceName}</h3>
                  <span className="workspace-root" title={snapshot.workspace.root ?? undefined}>{workspaceRoot}</span>
                </div>
                <button
                  className="workspace-open-button"
                  type="button"
                  disabled={choosingWorkspace || !onChooseWorkspace}
                  onClick={() => { void onChooseWorkspace?.(); }}
                >
                  {choosingWorkspace ? "Opening…" : snapshot.workspace.selected ? "Change workspace" : "Open workspace"}
                </button>
              </div>
              <p>{snapshot.workspace.signal.detail}</p>
              {workspaceError ? <div className="workspace-error" role="alert">{workspaceError}</div> : null}
              <div className="mini-grid">
                <div><span>Git branch</span><strong>{branch}</strong></div>
                <div><span>HEAD</span><strong>{shortHead(snapshot.git.head)}</strong></div>
                <div><span>Evidence</span><strong>{snapshot.evidence.evidenceBundles} bundle{snapshot.evidence.evidenceBundles === 1 ? "" : "s"}</strong></div>
              </div>
              {snapshot.workspace.projectMarkers.length > 0 ? (
                <div className="workspace-markers" aria-label="Detected project markers">
                  {snapshot.workspace.projectMarkers.map((marker) => <span key={marker}>{marker}</span>)}
                </div>
              ) : null}
            </div>

            <div className="task-surface">
              <div className="task-surface__glow" />
              <span className="section-kicker">TASK / CONVERSATION</span>
              <h3>{live?.task ? `${live.task.taskId} · ${live.task.state}` : "No execution session attached"}</h3>
              <p>
                {live?.task
                  ? `Read-only task progress: ${live.task.nodeSucceeded}/${live.task.nodeTotal} nodes succeeded, ${live.task.executions} execution(s), ${live.task.failures} failure(s). Mutation remains unavailable.`
                  : "Workspace, Git and runtime status observations are read-only. Task execution, shell commands, file mutation and computer input remain unavailable."}
              </p>
              <div className="composer" aria-label="Inactive task composer">
                <span>Execution input unavailable in trusted read mode</span>
                <button type="button" disabled>Run</button>
              </div>
            </div>
          </section>

          <aside className="inspector" aria-label="System inspector">
            <div className="inspector__heading">
              <div>
                <span className="section-kicker">SYSTEM TRUTH</span>
                <h2>Inspector</h2>
              </div>
              <span className="inspector__pulse" aria-hidden="true" />
            </div>
            <div className="status-stack">
              <StatusCard signal={snapshot.workspace.signal} />
              {statusSignals.map((signal) => <StatusCard key={signal.label} signal={signal} />)}
            </div>
          </aside>
        </div>

        <footer className="safety-bar" aria-label="Safety controls">
          <div className="safety-bar__copy">
            <span className={snapshot.safety.actionableSession ? "safety-orb safety-orb--live" : "safety-orb"} aria-hidden="true" />
            <div>
              <strong>Safety control plane</strong>
              <span>{snapshot.safety.detail}</span>
            </div>
          </div>
          <div className="safety-actions">
            <SafetyButton label="Pause" enabled={snapshot.safety.pause} />
            <SafetyButton label="Emergency stop" enabled={snapshot.safety.emergencyStop} kind="danger" />
            <SafetyButton label="Take control" enabled={snapshot.safety.takeControl} />
          </div>
        </footer>
      </section>
    </main>
  );
}
