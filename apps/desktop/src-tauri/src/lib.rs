mod runtime_status_supervisor;

use rfd::FileDialog;
use serde::Serialize;
use std::fs::{self, File, Metadata};
use std::io::Read;
use std::path::{Component, Path, PathBuf};
use std::sync::Mutex;
use tauri::State;

const DESKTOP_WINDOW_LABEL: &str = "main";
const MAX_ROOT_CHARS: usize = 1024;
const MAX_TOP_LEVEL_ENTRIES: usize = 512;
const MAX_HEAD_BYTES: u64 = 4096;
const MAX_PACKED_REFS_BYTES: u64 = 256 * 1024;
const MAX_PACKED_REFS_LINES: usize = 4096;
const MAX_CHECKPOINT_BYTES: u64 = 64 * 1024;
const MAX_EVIDENCE_BUNDLES: usize = 128;

#[derive(Clone, Copy, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
enum OperationalState {
    Ready,
    Unknown,
    Disconnected,
    Degraded,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct StatusSignal {
    state: OperationalState,
    label: String,
    detail: String,
    provenance: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct ProductIdentity {
    name: &'static str,
    version: &'static str,
    baseline_checkpoint: &'static str,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct WorkspaceReadModel {
    signal: StatusSignal,
    selected: bool,
    workspace_id: Option<String>,
    name: Option<String>,
    root: Option<String>,
    project_markers: Vec<String>,
    top_level_entries: usize,
    truncated: bool,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct GitReadModel {
    signal: StatusSignal,
    repository: bool,
    branch: Option<String>,
    head: Option<String>,
    detached: bool,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct EvidenceReadModel {
    signal: StatusSignal,
    checkpoint: Option<String>,
    checkpoint_status: Option<String>,
    evidence_bundles: usize,
    truncated: bool,
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
    workspace: WorkspaceReadModel,
    runtime: StatusSignal,
    provider: StatusSignal,
    git: GitReadModel,
    evidence: EvidenceReadModel,
    permission: StatusSignal,
    safety: SafetyAvailability,
}

#[derive(Clone)]
struct WorkspaceSelection {
    root: PathBuf,
    generation: u64,
}

struct WorkspaceSlot {
    current: Option<WorkspaceSelection>,
    next_generation: u64,
}

impl Default for WorkspaceSlot {
    fn default() -> Self {
        Self {
            current: None,
            next_generation: 1,
        }
    }
}

#[derive(Default)]
struct DesktopState {
    workspace: Mutex<WorkspaceSlot>,
}

fn signal(state: OperationalState, label: &str, detail: &str, provenance: &str) -> StatusSignal {
    StatusSignal {
        state,
        label: label.to_owned(),
        detail: detail.to_owned(),
        provenance: provenance.to_owned(),
    }
}

fn unknown(label: &str) -> StatusSignal {
    signal(
        OperationalState::Unknown,
        label,
        "No trusted live observation is connected for this signal.",
        "tauri-read-model-v2",
    )
}

fn selected_workspace(state: &DesktopState) -> Result<Option<WorkspaceSelection>, String> {
    let slot = state
        .workspace
        .lock()
        .map_err(|_| "workspace state is unavailable".to_owned())?;
    Ok(slot.current.clone())
}

fn replace_workspace(state: &DesktopState, root: PathBuf) -> Result<WorkspaceSelection, String> {
    let mut slot = state
        .workspace
        .lock()
        .map_err(|_| "workspace state is unavailable".to_owned())?;
    let generation = slot.next_generation;
    slot.next_generation = generation
        .checked_add(1)
        .ok_or_else(|| "workspace generation exhausted".to_owned())?;
    let selection = WorkspaceSelection { root, generation };
    slot.current = Some(selection.clone());
    Ok(selection)
}

fn is_link_or_reparse(metadata: &Metadata) -> bool {
    if metadata.file_type().is_symlink() {
        return true;
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        const FILE_ATTRIBUTE_REPARSE_POINT: u32 = 0x400;
        return metadata.file_attributes() & FILE_ATTRIBUTE_REPARSE_POINT != 0;
    }
    #[cfg(not(windows))]
    {
        false
    }
}

fn validate_workspace_root(path: &Path) -> Result<PathBuf, String> {
    let metadata = fs::symlink_metadata(path).map_err(|_| "selected workspace is unreadable".to_owned())?;
    if is_link_or_reparse(&metadata) {
        return Err("selected workspace cannot be a symlink or reparse point".to_owned());
    }
    if !metadata.is_dir() {
        return Err("selected workspace must be a directory".to_owned());
    }
    let canonical = fs::canonicalize(path).map_err(|_| "selected workspace cannot be canonicalized".to_owned())?;
    let canonical_metadata = fs::metadata(&canonical).map_err(|_| "selected workspace is unavailable".to_owned())?;
    if !canonical_metadata.is_dir() {
        return Err("selected workspace must resolve to a directory".to_owned());
    }
    let display = canonical.to_string_lossy();
    if display.chars().count() > MAX_ROOT_CHARS {
        return Err("selected workspace path is too long".to_owned());
    }
    Ok(canonical)
}

fn safe_existing_path(root: &Path, relative: &Path) -> Result<Option<PathBuf>, String> {
    if relative.is_absolute() {
        return Err("absolute child paths are not allowed".to_owned());
    }
    let mut current = root.to_path_buf();
    for component in relative.components() {
        match component {
            Component::Normal(part) => current.push(part),
            _ => return Err("non-canonical child path rejected".to_owned()),
        }
        let metadata = match fs::symlink_metadata(&current) {
            Ok(metadata) => metadata,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
            Err(_) => return Err("workspace child metadata is unavailable".to_owned()),
        };
        if is_link_or_reparse(&metadata) {
            return Err("workspace child symlink or reparse point rejected".to_owned());
        }
    }
    let canonical = fs::canonicalize(&current).map_err(|_| "workspace child cannot be canonicalized".to_owned())?;
    if !canonical.starts_with(root) {
        return Err("workspace child escaped trusted root".to_owned());
    }
    Ok(Some(canonical))
}

fn read_bounded_text(path: &Path, max_bytes: u64) -> Result<String, String> {
    let metadata = fs::symlink_metadata(path).map_err(|_| "bounded file metadata unavailable".to_owned())?;
    if is_link_or_reparse(&metadata) || !metadata.is_file() || metadata.len() > max_bytes {
        return Err("bounded file is invalid or exceeds size limit".to_owned());
    }
    let file = File::open(path).map_err(|_| "bounded file is unreadable".to_owned())?;
    let mut bytes = Vec::new();
    file.take(max_bytes.saturating_add(1))
        .read_to_end(&mut bytes)
        .map_err(|_| "bounded file is unreadable".to_owned())?;
    if bytes.len() as u64 > max_bytes {
        return Err("bounded file exceeded size limit during read".to_owned());
    }
    String::from_utf8(bytes).map_err(|_| "bounded file is not valid UTF-8 text".to_owned())
}

fn workspace_model(selection: &WorkspaceSelection) -> WorkspaceReadModel {
    let root = &selection.root;
    let mut markers = Vec::new();
    let marker_paths = [
        ("Cargo.toml", "Cargo"),
        ("package.json", "Node"),
        ("pyproject.toml", "Python"),
        ("AGENTS.md", "Hive Agents"),
        (".git", "Git"),
        ("docs/project-brain/11-CHECKPOINT.md", "Hive Checkpoint"),
    ];
    let mut degraded = false;
    for (path, label) in marker_paths {
        match safe_existing_path(root, Path::new(path)) {
            Ok(Some(_)) => markers.push(label.to_owned()),
            Ok(None) => {}
            Err(_) => degraded = true,
        }
    }

    let mut entries = 0usize;
    let mut truncated = false;
    match fs::read_dir(root) {
        Ok(iter) => {
            for item in iter {
                if item.is_err() {
                    degraded = true;
                    continue;
                }
                if entries == MAX_TOP_LEVEL_ENTRIES {
                    truncated = true;
                    degraded = true;
                    break;
                }
                entries += 1;
            }
        }
        Err(_) => degraded = true,
    }

    let name = root
        .file_name()
        .and_then(|value| value.to_str())
        .filter(|value| !value.trim().is_empty())
        .unwrap_or("Workspace")
        .chars()
        .take(120)
        .collect::<String>();

    WorkspaceReadModel {
        signal: if degraded {
            signal(
                OperationalState::Degraded,
                "Workspace",
                "Workspace is selected, but one or more bounded read observations were rejected or truncated.",
                "trusted-workspace-read-v1",
            )
        } else {
            signal(
                OperationalState::Ready,
                "Workspace",
                "User-selected workspace root is canonicalized and available for bounded read-only observation.",
                "trusted-workspace-read-v1",
            )
        },
        selected: true,
        workspace_id: Some(format!("ws-{:016x}", selection.generation)),
        name: Some(name),
        root: Some(root.to_string_lossy().into_owned()),
        project_markers: markers,
        top_level_entries: entries,
        truncated,
    }
}

fn no_workspace_model() -> WorkspaceReadModel {
    WorkspaceReadModel {
        signal: signal(
            OperationalState::Disconnected,
            "Workspace",
            "No workspace is selected. Choose a folder explicitly to establish read-only workspace context.",
            "trusted-workspace-read-v1",
        ),
        selected: false,
        workspace_id: None,
        name: None,
        root: None,
        project_markers: Vec::new(),
        top_level_entries: 0,
        truncated: false,
    }
}

fn valid_oid(value: &str) -> bool {
    matches!(value.len(), 40 | 64) && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn packed_ref_oid(git_dir: &Path, reference: &str) -> Result<Option<String>, String> {
    let Some(path) = safe_existing_path(git_dir, Path::new("packed-refs"))? else {
        return Ok(None);
    };
    let text = read_bounded_text(&path, MAX_PACKED_REFS_BYTES)?;
    for (index, line) in text.lines().enumerate() {
        if index >= MAX_PACKED_REFS_LINES {
            return Err("packed refs exceeds line limit".to_owned());
        }
        if line.starts_with('#') || line.starts_with('^') || line.trim().is_empty() {
            continue;
        }
        let mut parts = line.split_whitespace();
        let Some(oid) = parts.next() else { continue };
        let Some(name) = parts.next() else { continue };
        if name == reference && valid_oid(oid) {
            return Ok(Some(oid.to_ascii_lowercase()));
        }
    }
    Ok(None)
}

fn git_model(root: &Path) -> GitReadModel {
    let git_path = match safe_existing_path(root, Path::new(".git")) {
        Ok(Some(path)) => path,
        Ok(None) => {
            return GitReadModel {
                signal: signal(
                    OperationalState::Unknown,
                    "Git",
                    "Selected workspace is not an observed Git repository root.",
                    "git-head-read-v1",
                ),
                repository: false,
                branch: None,
                head: None,
                detached: false,
            };
        }
        Err(reason) => {
            return GitReadModel {
                signal: signal(OperationalState::Degraded, "Git", &reason, "git-head-read-v1"),
                repository: false,
                branch: None,
                head: None,
                detached: false,
            };
        }
    };

    if !git_path.is_dir() {
        return GitReadModel {
            signal: signal(
                OperationalState::Degraded,
                "Git",
                "Linked-worktree gitdir files are intentionally unsupported by this bounded read surface.",
                "git-head-read-v1",
            ),
            repository: true,
            branch: None,
            head: None,
            detached: false,
        };
    }

    let head_path = match safe_existing_path(&git_path, Path::new("HEAD")) {
        Ok(Some(path)) => path,
        _ => {
            return GitReadModel {
                signal: signal(
                    OperationalState::Degraded,
                    "Git",
                    "Git HEAD is missing or unsafe to read.",
                    "git-head-read-v1",
                ),
                repository: true,
                branch: None,
                head: None,
                detached: false,
            };
        }
    };
    let head_text = match read_bounded_text(&head_path, MAX_HEAD_BYTES) {
        Ok(value) => value,
        Err(reason) => {
            return GitReadModel {
                signal: signal(OperationalState::Degraded, "Git", &reason, "git-head-read-v1"),
                repository: true,
                branch: None,
                head: None,
                detached: false,
            };
        }
    };
    let head_value = head_text.trim();

    if let Some(reference) = head_value.strip_prefix("ref: ") {
        if !reference.starts_with("refs/heads/") || reference == "refs/heads/" || reference.len() > 220 {
            return GitReadModel {
                signal: signal(
                    OperationalState::Degraded,
                    "Git",
                    "Git HEAD reference is outside the supported local-branch namespace.",
                    "git-head-read-v1",
                ),
                repository: true,
                branch: None,
                head: None,
                detached: false,
            };
        }
        let branch = reference.trim_start_matches("refs/heads/").to_owned();
        let loose = match safe_existing_path(&git_path, Path::new(reference)) {
            Ok(Some(path)) => read_bounded_text(&path, MAX_HEAD_BYTES)
                .ok()
                .map(|value| value.trim().to_owned())
                .filter(|value| valid_oid(value)),
            _ => None,
        };
        let oid = match loose {
            Some(value) => Some(value.to_ascii_lowercase()),
            None => packed_ref_oid(&git_path, reference).unwrap_or_default(),
        };
        return GitReadModel {
            signal: if oid.is_some() {
                signal(
                    OperationalState::Ready,
                    "Git",
                    "Local branch and HEAD identity were read directly from bounded Git metadata without process execution.",
                    "git-head-read-v1",
                )
            } else {
                signal(
                    OperationalState::Degraded,
                    "Git",
                    "Repository branch is present but no committed HEAD identity is available (for example, an unborn branch).",
                    "git-head-read-v1",
                )
            },
            repository: true,
            branch: Some(branch),
            head: oid,
            detached: false,
        };
    }

    if valid_oid(head_value) {
        return GitReadModel {
            signal: signal(
                OperationalState::Ready,
                "Git",
                "Detached HEAD identity was read directly from bounded Git metadata without process execution.",
                "git-head-read-v1",
            ),
            repository: true,
            branch: None,
            head: Some(head_value.to_ascii_lowercase()),
            detached: true,
        };
    }

    GitReadModel {
        signal: signal(
            OperationalState::Degraded,
            "Git",
            "Git HEAD metadata is malformed or unsupported.",
            "git-head-read-v1",
        ),
        repository: true,
        branch: None,
        head: None,
        detached: false,
    }
}

fn markdown_field(text: &str, prefix: &str, max: usize) -> Option<String> {
    text.lines()
        .find_map(|line| line.trim().strip_prefix(prefix).map(str::trim))
        .map(|value| value.trim_matches('`').trim_matches('*').trim().to_owned())
        .filter(|value| !value.is_empty() && value.chars().count() <= max)
}

fn evidence_model(root: &Path) -> EvidenceReadModel {
    let mut checkpoint = None;
    let mut checkpoint_status = None;
    let mut bundles = 0usize;
    let mut truncated = false;
    let mut degraded = false;

    match safe_existing_path(root, Path::new("docs/project-brain/11-CHECKPOINT.md")) {
        Ok(Some(path)) => match read_bounded_text(&path, MAX_CHECKPOINT_BYTES) {
            Ok(text) => {
                checkpoint = markdown_field(&text, "**Checkpoint:**", 80);
                checkpoint_status = markdown_field(&text, "**Status:**", 120);
                if checkpoint.is_none() {
                    degraded = true;
                }
            }
            Err(_) => degraded = true,
        },
        Ok(None) => {}
        Err(_) => degraded = true,
    }

    match safe_existing_path(root, Path::new(".engineering/evidence")) {
        Ok(Some(path)) if path.is_dir() => match fs::read_dir(path) {
            Ok(iter) => {
                for item in iter {
                    let Ok(item) = item else {
                        degraded = true;
                        continue;
                    };
                    let Ok(metadata) = fs::symlink_metadata(item.path()) else {
                        degraded = true;
                        continue;
                    };
                    if is_link_or_reparse(&metadata) {
                        degraded = true;
                        continue;
                    }
                    if metadata.is_file() && item.path().extension().and_then(|v| v.to_str()) == Some("md") {
                        if bundles == MAX_EVIDENCE_BUNDLES {
                            truncated = true;
                            degraded = true;
                            break;
                        }
                        bundles += 1;
                    }
                }
            }
            Err(_) => degraded = true,
        },
        Ok(Some(_)) => degraded = true,
        Ok(None) => {}
        Err(_) => degraded = true,
    }

    let found = checkpoint.is_some() || bundles > 0;
    EvidenceReadModel {
        signal: if degraded {
            signal(
                OperationalState::Degraded,
                "Evidence",
                "Hive evidence paths were found, but one or more bounded observations were rejected or truncated.",
                "hive-evidence-read-v1",
            )
        } else if found {
            signal(
                OperationalState::Ready,
                "Evidence",
                "Known Hive checkpoint/evidence paths were observed through bounded read-only access.",
                "hive-evidence-read-v1",
            )
        } else {
            signal(
                OperationalState::Unknown,
                "Evidence",
                "No known Hive checkpoint or evidence bundle is present in the selected workspace.",
                "hive-evidence-read-v1",
            )
        },
        checkpoint,
        checkpoint_status,
        evidence_bundles: bundles,
        truncated,
    }
}

fn desktop_snapshot(state: &DesktopState) -> Result<DesktopSnapshot, String> {
    let selection = selected_workspace(state)?;
    let (workspace, git, evidence) = match selection {
        Some(ref selection) => (
            workspace_model(selection),
            git_model(&selection.root),
            evidence_model(&selection.root),
        ),
        None => (
            no_workspace_model(),
            GitReadModel {
                signal: unknown("Git"),
                repository: false,
                branch: None,
                head: None,
                detached: false,
            },
            EvidenceReadModel {
                signal: unknown("Evidence"),
                checkpoint: None,
                checkpoint_status: None,
                evidence_bundles: 0,
                truncated: false,
            },
        ),
    };

    Ok(DesktopSnapshot {
        schema_version: 2,
        product: ProductIdentity {
            name: "Hive Coder",
            version: env!("CARGO_PKG_VERSION"),
            baseline_checkpoint: "HCODER-CP-0015",
        },
        shell: signal(
            OperationalState::Ready,
            "Desktop shell",
            "Native Hive application bridge is connected in bounded read-only mode.",
            "tauri-read-model-v2",
        ),
        workspace,
        runtime: signal(
            OperationalState::Disconnected,
            "Runtime",
            "Python agent runtime is not connected by WO-0016.",
            "tauri-read-model-v2",
        ),
        provider: unknown("Provider"),
        git,
        evidence,
        permission: signal(
            OperationalState::Unknown,
            "Permission plane",
            "No actionable permission session is exposed through this read-only workspace bridge.",
            "tauri-read-model-v2",
        ),
        safety: SafetyAvailability {
            actionable_session: false,
            pause: false,
            emergency_stop: false,
            take_control: false,
            detail: "No actionable trusted execution session is connected; mutation controls remain disabled.",
        },
    })
}

fn desktop_window_is_authorized(label: &str) -> bool {
    label == DESKTOP_WINDOW_LABEL
}

#[tauri::command]
fn get_desktop_snapshot(
    webview_window: tauri::WebviewWindow,
    state: State<'_, DesktopState>,
) -> Result<DesktopSnapshot, String> {
    if !desktop_window_is_authorized(webview_window.label()) {
        return Err("desktop snapshot is unavailable for this window".to_owned());
    }
    desktop_snapshot(&state)
}

#[tauri::command]
fn choose_workspace(
    webview_window: tauri::WebviewWindow,
    state: State<'_, DesktopState>,
) -> Result<DesktopSnapshot, String> {
    if !desktop_window_is_authorized(webview_window.label()) {
        return Err("workspace selection is unavailable for this window".to_owned());
    }
    let Some(selected) = FileDialog::new().set_title("Open Hive Coder workspace").pick_folder() else {
        return desktop_snapshot(&state);
    };
    let root = validate_workspace_root(&selected)?;
    replace_workspace(&state, root)?;
    desktop_snapshot(&state)
}

#[tauri::command]
fn get_runtime_status_envelope(webview_window: tauri::WebviewWindow) -> Result<String, String> {
    if !desktop_window_is_authorized(webview_window.label()) {
        return Err("runtime status is unavailable for this window".to_owned());
    }
    runtime_status_supervisor::query_runtime_status_envelope()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(DesktopState::default())
        .invoke_handler(tauri::generate_handler![get_desktop_snapshot, choose_workspace, get_runtime_status_envelope])
        .run(tauri::generate_context!())
        .expect("Hive Coder desktop runtime failed");
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};

    static NEXT_TEST: AtomicU64 = AtomicU64::new(1);

    fn temp_root(name: &str) -> PathBuf {
        let id = NEXT_TEST.fetch_add(1, Ordering::Relaxed);
        let root = std::env::temp_dir().join(format!("hive-coder-{name}-{}-{id}", std::process::id()));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).unwrap();
        root
    }

    fn cleanup(path: &Path) {
        let _ = fs::remove_dir_all(path);
    }

    #[test]
    fn snapshot_exposes_no_actionable_mutation_capability() {
        let state = DesktopState::default();
        let snapshot = desktop_snapshot(&state).unwrap();
        assert_eq!(snapshot.schema_version, 2);
        assert_eq!(snapshot.product.baseline_checkpoint, "HCODER-CP-0015");
        assert!(!snapshot.safety.actionable_session);
        assert!(!snapshot.safety.pause);
        assert!(!snapshot.safety.emergency_stop);
        assert!(!snapshot.safety.take_control);
    }

    #[test]
    fn unconnected_runtime_is_not_reported_ready() {
        let state = DesktopState::default();
        let snapshot = desktop_snapshot(&state).unwrap();
        assert!(matches!(snapshot.runtime.state, OperationalState::Disconnected));
    }

    #[test]
    fn read_commands_are_bound_to_main_window_label() {
        assert!(desktop_window_is_authorized("main"));
        assert!(!desktop_window_is_authorized("preview"));
        assert!(!desktop_window_is_authorized("*"));
        assert!(!desktop_window_is_authorized(""));
    }

    #[test]
    fn workspace_root_must_be_a_directory() {
        let root = temp_root("file-root");
        let file = root.join("not-a-workspace.txt");
        fs::write(&file, "data").unwrap();
        assert!(validate_workspace_root(&file).is_err());
        cleanup(&root);
    }

    #[test]
    fn child_paths_reject_parent_traversal() {
        let root = temp_root("traversal");
        let canonical = validate_workspace_root(&root).unwrap();
        assert!(safe_existing_path(&canonical, Path::new("../outside")).is_err());
        cleanup(&root);
    }

    #[test]
    fn git_branch_and_head_are_read_without_process_execution() {
        let root = temp_root("git-branch");
        fs::create_dir_all(root.join(".git/refs/heads")).unwrap();
        fs::write(root.join(".git/HEAD"), "ref: refs/heads/main\n").unwrap();
        let oid = "0123456789abcdef0123456789abcdef01234567";
        fs::write(root.join(".git/refs/heads/main"), format!("{oid}\n")).unwrap();
        let canonical = validate_workspace_root(&root).unwrap();
        let git = git_model(&canonical);
        assert!(git.repository);
        assert_eq!(git.branch.as_deref(), Some("main"));
        assert_eq!(git.head.as_deref(), Some(oid));
        assert!(!git.detached);
        assert!(matches!(git.signal.state, OperationalState::Ready));
        cleanup(&root);
    }

    #[test]
    fn detached_git_head_is_reported_truthfully() {
        let root = temp_root("git-detached");
        fs::create_dir_all(root.join(".git")).unwrap();
        let oid = "abcdef0123456789abcdef0123456789abcdef01";
        fs::write(root.join(".git/HEAD"), format!("{oid}\n")).unwrap();
        let canonical = validate_workspace_root(&root).unwrap();
        let git = git_model(&canonical);
        assert!(git.repository);
        assert!(git.detached);
        assert_eq!(git.head.as_deref(), Some(oid));
        cleanup(&root);
    }

    #[test]
    fn gitdir_pointer_file_fails_closed() {
        let root = temp_root("gitdir-pointer");
        fs::write(root.join(".git"), "gitdir: C:/outside\n").unwrap();
        let canonical = validate_workspace_root(&root).unwrap();
        let git = git_model(&canonical);
        assert!(git.repository);
        assert!(matches!(git.signal.state, OperationalState::Degraded));
        cleanup(&root);
    }

    #[test]
    fn hive_checkpoint_and_evidence_are_bounded_observations() {
        let root = temp_root("evidence");
        fs::create_dir_all(root.join("docs/project-brain")).unwrap();
        fs::create_dir_all(root.join(".engineering/evidence")).unwrap();
        fs::write(
            root.join("docs/project-brain/11-CHECKPOINT.md"),
            "# Checkpoint\n**Checkpoint:** `HCODER-CP-0015`  \n**Status:** APPROVED\n",
        )
        .unwrap();
        fs::write(root.join(".engineering/evidence/one.md"), "evidence").unwrap();
        let canonical = validate_workspace_root(&root).unwrap();
        let evidence = evidence_model(&canonical);
        assert_eq!(evidence.checkpoint.as_deref(), Some("HCODER-CP-0015"));
        assert_eq!(evidence.evidence_bundles, 1);
        assert!(matches!(evidence.signal.state, OperationalState::Ready));
        cleanup(&root);
    }

    #[test]
    fn empty_git_branch_reference_fails_closed() {
        let root = temp_root("git-empty-branch");
        fs::create_dir_all(root.join(".git")).unwrap();
        fs::write(root.join(".git/HEAD"), "ref: refs/heads/\n").unwrap();
        let canonical = validate_workspace_root(&root).unwrap();
        let git = git_model(&canonical);
        assert!(git.repository);
        assert!(git.branch.is_none());
        assert!(git.head.is_none());
        assert!(matches!(git.signal.state, OperationalState::Degraded));
        cleanup(&root);
    }

    #[cfg(unix)]
    #[test]
    fn dangling_symlink_is_rejected_as_unsafe_child() {
        use std::os::unix::fs::symlink;

        let root = temp_root("dangling-link");
        symlink(root.join("missing-target"), root.join("dangling")).unwrap();
        let canonical = validate_workspace_root(&root).unwrap();
        assert!(safe_existing_path(&canonical, Path::new("dangling")).is_err());
        cleanup(&root);
    }

    #[cfg(unix)]
    #[test]
    fn evidence_symlink_escape_is_not_counted() {
        use std::os::unix::fs::symlink;

        let root = temp_root("evidence-symlink");
        let outside = temp_root("evidence-outside");
        fs::create_dir_all(root.join(".engineering/evidence")).unwrap();
        let outside_file = outside.join("outside.md");
        fs::write(&outside_file, "outside evidence").unwrap();
        symlink(&outside_file, root.join(".engineering/evidence/linked.md")).unwrap();

        let canonical = validate_workspace_root(&root).unwrap();
        let evidence = evidence_model(&canonical);
        assert_eq!(evidence.evidence_bundles, 0);
        assert!(matches!(evidence.signal.state, OperationalState::Degraded));

        cleanup(&root);
        cleanup(&outside);
    }


    #[test]
    fn bounded_text_rejects_growth_beyond_physical_ceiling() {
        let root = temp_root("bounded-read");
        let file = root.join("bounded.txt");
        fs::write(&file, b"123456789").unwrap();
        assert!(read_bounded_text(&file, 8).is_err());
        assert_eq!(read_bounded_text(&file, 9).unwrap(), "123456789");
        cleanup(&root);
    }

}
