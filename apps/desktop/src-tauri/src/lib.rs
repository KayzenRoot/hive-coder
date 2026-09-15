use serde::Serialize;

const DESKTOP_WINDOW_LABEL: &str = "main";

#[derive(Clone, Copy, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
enum OperationalState {
    Ready,
    Unknown,
    Disconnected,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct StatusSignal {
    state: OperationalState,
    label: &'static str,
    detail: &'static str,
    provenance: &'static str,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ProductIdentity {
    name: &'static str,
    version: &'static str,
    checkpoint: &'static str,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct SafetyAvailability {
    actionable_session: bool,
    pause: bool,
    emergency_stop: bool,
    take_control: bool,
    detail: &'static str,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct DesktopSnapshot {
    schema_version: u8,
    product: ProductIdentity,
    shell: StatusSignal,
    runtime: StatusSignal,
    provider: StatusSignal,
    git: StatusSignal,
    evidence: StatusSignal,
    permission: StatusSignal,
    safety: SafetyAvailability,
}

fn unknown(label: &'static str) -> StatusSignal {
    StatusSignal {
        state: OperationalState::Unknown,
        label,
        detail: "No trusted live observation is connected to this read-only desktop shell.",
        provenance: "tauri-read-model-v1",
    }
}

fn desktop_snapshot() -> DesktopSnapshot {
    DesktopSnapshot {
        schema_version: 1,
        product: ProductIdentity {
            name: "Hive Coder",
            version: env!("CARGO_PKG_VERSION"),
            checkpoint: "HCODER-CP-0014",
        },
        shell: StatusSignal {
            state: OperationalState::Ready,
            label: "Desktop shell",
            detail: "Native read-only application bridge is connected.",
            provenance: "tauri-read-model-v1",
        },
        runtime: StatusSignal {
            state: OperationalState::Disconnected,
            label: "Runtime",
            detail: "Python agent runtime is not connected by WO-0015.",
            provenance: "tauri-read-model-v1",
        },
        provider: unknown("Provider"),
        git: unknown("Git"),
        evidence: StatusSignal {
            state: OperationalState::Unknown,
            label: "Evidence",
            detail: "No live evidence adapter is connected by WO-0015.",
            provenance: "tauri-read-model-v1",
        },
        permission: StatusSignal {
            state: OperationalState::Unknown,
            label: "Permission plane",
            detail: "No actionable permission session is exposed through this read-only bridge.",
            provenance: "tauri-read-model-v1",
        },
        safety: SafetyAvailability {
            actionable_session: false,
            pause: false,
            emergency_stop: false,
            take_control: false,
            detail: "No actionable trusted session is connected; all mutation controls are disabled.",
        },
    }
}

fn desktop_window_is_authorized(label: &str) -> bool {
    label == DESKTOP_WINDOW_LABEL
}

#[tauri::command]
fn get_desktop_snapshot(webview_window: tauri::WebviewWindow) -> Result<DesktopSnapshot, &'static str> {
    if !desktop_window_is_authorized(webview_window.label()) {
        return Err("desktop snapshot is unavailable for this window");
    }
    Ok(desktop_snapshot())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![get_desktop_snapshot])
        .run(tauri::generate_context!())
        .expect("Hive Coder desktop runtime failed");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn snapshot_exposes_no_actionable_mutation_capability() {
        let snapshot = desktop_snapshot();
        assert_eq!(snapshot.schema_version, 1);
        assert!(!snapshot.safety.actionable_session);
        assert!(!snapshot.safety.pause);
        assert!(!snapshot.safety.emergency_stop);
        assert!(!snapshot.safety.take_control);
    }

    #[test]
    fn unconnected_runtime_is_not_reported_ready() {
        let snapshot = desktop_snapshot();
        assert!(matches!(snapshot.runtime.state, OperationalState::Disconnected));
    }

    #[test]
    fn read_model_is_bound_to_main_window_label() {
        assert!(desktop_window_is_authorized("main"));
        assert!(!desktop_window_is_authorized("preview"));
        assert!(!desktop_window_is_authorized("*"));
        assert!(!desktop_window_is_authorized(""));
    }
}
