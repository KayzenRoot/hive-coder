import type { DesktopSnapshot, OperationalState, StatusSignal } from "../contracts/desktopSnapshot";
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
  choosingWorkspace?: boolean;
  workspaceError?: string | null;
  onChooseWorkspace?: () => void | Promise<void>;
}

function shortHead(head: string | null): string {
  return head ? head.slice(0, 12) : "Unavailable";
}

export function ShellView({
  snapshot,
  choosingWorkspace = false,
  workspaceError = null,
  onChooseWorkspace,
}: ShellViewProps) {
  const statusSignals = [snapshot.runtime, snapshot.provider, snapshot.git.signal, snapshot.evidence.signal, snapshot.permission];
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
              <h3>No execution session attached</h3>
              <p>
                Workspace and Git observations are read-only. Task execution, shell commands, file mutation and
                computer input remain unavailable until later governed application boundaries are promoted.
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
