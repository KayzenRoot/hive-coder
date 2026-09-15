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
const STATUS_REQUEST: &str = "{\"op\":\"status.snapshot\",\"protocol\":\"hive-runtime-status-ipc-v1\",\"requestId\":\"desktop-runtime\"}";
const MAX_STATUS_RESPONSE_BYTES: u64 = 33_024;
const MAX_STATUS_WIRE_BYTES: u64 = MAX_STATUS_RESPONSE_BYTES + 1;
const SIDECAR_TIMEOUT: Duration = Duration::from_millis(1_500);

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
    let executable = std::env::current_exe()
        .map_err(|_| "desktop executable identity is unavailable".to_owned())?;
    let sidecar = sidecar_path_from_exe(&executable)?;
    let metadata = fs::symlink_metadata(&sidecar)
        .map_err(|_| "runtime status sidecar is not installed".to_owned())?;
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

fn validate_response_wire(bytes: Vec<u8>) -> Result<String, String> {
    if bytes.is_empty() || bytes.len() as u64 > MAX_STATUS_WIRE_BYTES {
        return Err("runtime status response exceeded byte bounds".to_owned());
    }
    if bytes.last() != Some(&b'\n') {
        return Err("runtime status response framing is invalid".to_owned());
    }
    let payload = &bytes[..bytes.len() - 1];
    if payload.is_empty()
        || payload.len() as u64 > MAX_STATUS_RESPONSE_BYTES
        || payload.contains(&b'\n')
        || payload.contains(&b'\r')
    {
        return Err("runtime status response framing is invalid".to_owned());
    }
    String::from_utf8(payload.to_vec())
        .map_err(|_| "runtime status response is not UTF-8".to_owned())
}

pub(crate) fn query_runtime_status_envelope() -> Result<String, String> {
    let sidecar = validated_sidecar_path()?;
    let sidecar_dir = sidecar
        .parent()
        .ok_or_else(|| "runtime status sidecar parent is unavailable".to_owned())?;
    let mut child = Command::new(&sidecar)
        .arg(SIDECAR_MODE)
        .env_clear()
        .current_dir(sidecar_dir)
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
            .take(MAX_STATUS_WIRE_BYTES.saturating_add(1))
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
    validate_response_wire(bytes)
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
    fn protocol_request_is_fixed_and_canonical() {
        assert_eq!(SIDECAR_MODE, "--stdio-status-v1");
        assert_eq!(
            STATUS_REQUEST,
            "{\"op\":\"status.snapshot\",\"protocol\":\"hive-runtime-status-ipc-v1\",\"requestId\":\"desktop-runtime\"}"
        );
        assert_eq!(MAX_STATUS_RESPONSE_BYTES, 33_024);
        assert!(!STATUS_REQUEST.contains("prompt"));
        assert!(!STATUS_REQUEST.contains("execute"));
        assert!(!STATUS_REQUEST.contains("permit"));
    }

    #[test]
    fn response_wire_requires_one_bounded_newline_frame() {
        assert_eq!(validate_response_wire(b"{}\n".to_vec()).unwrap(), "{}");
        assert!(validate_response_wire(b"{}".to_vec()).is_err());
        assert!(validate_response_wire(b"{}\n{}\n".to_vec()).is_err());
        assert!(validate_response_wire(vec![b'x'; (MAX_STATUS_WIRE_BYTES + 1) as usize]).is_err());
    }
}
