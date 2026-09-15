use std::fs::{self, Metadata};
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

#[cfg(windows)]
const SIDECAR_BASENAME: &str = "hive-runtime-status-sidecar.exe";
#[cfg(not(windows))]
const SIDECAR_BASENAME: &str = "hive-runtime-status-sidecar";
const SIDECAR_MODE: &str = "--stdio-status-v1";
const STATUS_REQUEST: &str = "{\"protocol\":\"hive-runtime-status-ipc-v1\",\"requestId\":\"desktop-runtime\",\"op\":\"status.snapshot\"}";
const MAX_STATUS_RESPONSE_BYTES: u64 = 40_000;
const SIDECAR_TIMEOUT: Duration = Duration::from_millis(1500);

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

fn sidecar_path_from_exe(executable: &Path) -> Result<PathBuf, String> {
    let parent = executable
        .parent()
        .ok_or_else(|| "desktop executable parent is unavailable".to_owned())?;
    Ok(parent.join(SIDECAR_BASENAME))
}

fn validated_sidecar_path() -> Result<PathBuf, String> {
    let executable = std::env::current_exe().map_err(|_| "desktop executable identity is unavailable".to_owned())?;
    let sidecar = sidecar_path_from_exe(&executable)?;
    let metadata = fs::symlink_metadata(&sidecar).map_err(|_| "runtime status sidecar is not installed".to_owned())?;
    if is_link_or_reparse(&metadata) || !metadata.is_file() {
        return Err("runtime status sidecar identity is unsafe".to_owned());
    }
    Ok(sidecar)
}

fn terminate_child(child: &mut Child) {
    if matches!(child.try_wait(), Ok(None)) {
        let _ = child.kill();
    }
    let _ = child.wait();
}

pub(crate) fn query_runtime_status_envelope() -> Result<String, String> {
    let sidecar = validated_sidecar_path()?;
    let mut child = Command::new(&sidecar)
        .arg(SIDECAR_MODE)
        .env_clear()
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|_| "runtime status sidecar could not start".to_owned())?;

    let mut stdin = match child.stdin.take() {
        Some(stdin) => stdin,
        None => {
            terminate_child(&mut child);
            return Err("runtime status sidecar stdin is unavailable".to_owned());
        }
    };
    if write!(stdin, "{}\n", STATUS_REQUEST).is_err() {
        drop(stdin);
        terminate_child(&mut child);
        return Err("runtime status request could not be sent".to_owned());
    }
    if stdin.flush().is_err() {
        drop(stdin);
        terminate_child(&mut child);
        return Err("runtime status request could not be flushed".to_owned());
    }
    drop(stdin);

    let stdout = match child.stdout.take() {
        Some(stdout) => stdout,
        None => {
            terminate_child(&mut child);
            return Err("runtime status sidecar stdout is unavailable".to_owned());
        }
    };
    let reader = thread::spawn(move || {
        let mut bytes = Vec::new();
        stdout
            .take(MAX_STATUS_RESPONSE_BYTES.saturating_add(1))
            .read_to_end(&mut bytes)
            .map(|_| bytes)
    });

    let deadline = Instant::now() + SIDECAR_TIMEOUT;
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) if Instant::now() < deadline => thread::sleep(Duration::from_millis(10)),
            Ok(None) => {
                terminate_child(&mut child);
                let _ = reader.join();
                return Err("runtime status sidecar timed out".to_owned());
            }
            Err(_) => {
                terminate_child(&mut child);
                let _ = reader.join();
                return Err("runtime status sidecar state is unavailable".to_owned());
            }
        }
    };

    let bytes = reader
        .join()
        .map_err(|_| "runtime status reader failed".to_owned())?
        .map_err(|_| "runtime status response could not be read".to_owned())?;
    if !status.success() {
        return Err("runtime status sidecar rejected the request".to_owned());
    }
    if bytes.is_empty() || bytes.len() as u64 > MAX_STATUS_RESPONSE_BYTES {
        return Err("runtime status response exceeded byte bounds".to_owned());
    }
    let text = String::from_utf8(bytes).map_err(|_| "runtime status response is not UTF-8".to_owned())?;
    let framed = text.trim_end_matches(['\r', '\n']);
    if framed.is_empty() || framed.contains('\n') || framed.contains('\r') {
        return Err("runtime status response framing is invalid".to_owned());
    }
    if !framed.starts_with('{')
        || !framed.ends_with('}')
        || !framed.contains("\"protocol\":\"hive-runtime-status-ipc-v1\"")
        || !framed.contains("\"requestId\":\"desktop-runtime\"")
    {
        return Err("runtime status response identity is invalid".to_owned());
    }
    Ok(framed.to_owned())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sidecar_path_is_fixed_sibling_of_desktop_executable() {
        let executable = Path::new("C:/Hive/hive-coder-desktop.exe");
        let path = sidecar_path_from_exe(executable).unwrap();
        assert_eq!(path.file_name().and_then(|value| value.to_str()), Some(SIDECAR_BASENAME));
        assert_eq!(path.parent(), executable.parent());
    }

    #[test]
    fn protocol_request_is_fixed_and_non_mutating() {
        assert_eq!(SIDECAR_MODE, "--stdio-status-v1");
        assert!(STATUS_REQUEST.contains("hive-runtime-status-ipc-v1"));
        assert!(STATUS_REQUEST.contains("status.snapshot"));
        assert!(!STATUS_REQUEST.contains("prompt"));
        assert!(!STATUS_REQUEST.contains("execute"));
        assert!(!STATUS_REQUEST.contains("permit"));
    }
}
