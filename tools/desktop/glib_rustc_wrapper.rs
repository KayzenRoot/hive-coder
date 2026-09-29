//! Build-only HCODER-SEC-0001 wrapper. No runtime or desktop process authority.
//! Local path glib 0.18.5 retains two known pre-existing lint warnings when
//! the pinned setup action passes -D warnings to every crate. Permit ONLY those
//! two names when rustc compiles the exact generated patched glib src/lib.rs.

use std::env;
use std::ffi::{OsStr, OsString};
use std::path::{Path, PathBuf};
use std::process::{Command, ExitCode};

fn is_exact_generated_glib(args: &[OsString], vendor_lib: &Path) -> bool {
    let name_matches = args.windows(2).any(|pair| {
        pair[0] == OsStr::new("--crate-name") && pair[1] == OsStr::new("glib")
    }) || args.iter().any(|arg| arg == OsStr::new("--crate-name=glib"));
    if !name_matches {
        return false;
    }
    let Ok(expected) = vendor_lib.canonicalize() else {
        return false;
    };
    args.iter().any(|arg| {
        let text = arg.to_string_lossy();
        if !text.ends_with("src/lib.rs") && !text.ends_with("src\\lib.rs") {
            return false;
        }
        let candidate = PathBuf::from(arg);
        candidate.canonicalize().is_ok_and(|actual| actual == expected)
    })
}

fn main() -> ExitCode {
    let mut args = env::args_os().skip(1);
    let Some(rustc) = args.next() else {
        eprintln!("HCODER_GLIB_RUSTC_WRAPPER=REJECTED_NO_COMPILER");
        return ExitCode::from(2);
    };
    let rustc_args: Vec<OsString> = args.collect();
    let glib = env::var_os("HCODER_GLIB_VENDOR_LIB")
        .is_some_and(|path| is_exact_generated_glib(&rustc_args, Path::new(&path)));
    let mut command = Command::new(rustc);
    command.args(&rustc_args);
    if glib {
        command.args([
            "-A", "unused_parens",
            "-A", "mismatched_lifetime_syntaxes",
        ]);
        eprintln!("HCODER_EXACT_GLIB_ONLY_LEGACY_LINT_ALLOWLIST=1");
    }
    match command.status() {
        Ok(status) if status.success() => ExitCode::SUCCESS,
        Ok(status) => ExitCode::from(u8::try_from(status.code().unwrap_or(1)).unwrap_or(1)),
        Err(_) => {
            eprintln!("HCODER_GLIB_RUSTC_WRAPPER=REJECTED_COMPILER_EXEC");
            ExitCode::from(1)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reject_any_missing_exact_vendor_path() {
        let args = vec![OsString::from("--crate-name"), OsString::from("glib"),
                        OsString::from("src/lib.rs")];
        assert!(!is_exact_generated_glib(&args, Path::new("/invalid/glib/src/lib.rs")));
    }

    #[test]
    fn reject_other_crate_even_when_source_looks_like_glib() {
        let args = vec![OsString::from("--crate-name"), OsString::from("hive_coder_desktop"),
                        OsString::from("src/lib.rs")];
        assert!(!is_exact_generated_glib(&args, Path::new("/invalid/glib/src/lib.rs")));
    }
}
