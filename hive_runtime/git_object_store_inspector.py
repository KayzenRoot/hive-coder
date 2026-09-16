from __future__ import annotations

"""Read-only proof of the first supported Git object-store envelope.

No object bytes are created, compressed, written or published here. The first
WO-0023 slice accepts only an ordinary repository-local `.git/objects` store
with SHA-1 object format and no alternate/promisor/partial-clone signals.
"""

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .git_stage import GitStageUnsupportedRepositoryError

OBJECT_STORE_INSPECTOR_CONTRACT = "hive-git-object-store-inspector-v1"
SUPPORTED_OBJECT_FORMAT = "sha1"


@dataclass(frozen=True)
class GitObjectStoreEnvelope:
    contract: str
    object_format: str
    git_dir_identity: str
    objects_identity: str
    repository_local: bool


def _dir_identity(st: os.stat_result) -> str:
    return f"posix-dir:{int(st.st_dev)}:{int(st.st_ino)}:{int(st.st_mode)}"


def _lstat_directory(path: Path, label: str) -> os.stat_result:
    try:
        st = path.lstat()
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError(f"{label} is unavailable") from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise GitStageUnsupportedRepositoryError(f"{label} is not a proven local directory")
    return st


def _reject_if_present(path: Path, label: str) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError(f"cannot prove absence of {label}") from exc
    raise GitStageUnsupportedRepositoryError(f"unsupported Git object-store feature: {label}")


def _read_config_bytes(config_path: Path) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(config_path, flags)
    except FileNotFoundError:
        return b""
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError("Git config is not safely readable") from exc
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise GitStageUnsupportedRepositoryError("Git config is not a regular file")
        data = os.read(fd, 1024 * 1024 + 1)
        if len(data) > 1024 * 1024:
            raise GitStageUnsupportedRepositoryError("Git config exceeds governed ceiling")
        return data.lower()
    finally:
        os.close(fd)


def inspect_local_object_store(workspace_root: str | os.PathLike[str]) -> GitObjectStoreEnvelope:
    root = Path(workspace_root)
    try:
        canonical = root.resolve(strict=True)
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError("workspace root is unavailable") from exc
    if not canonical.is_dir():
        raise GitStageUnsupportedRepositoryError("workspace root is not a directory")

    git_dir = canonical / ".git"
    git_st = _lstat_directory(git_dir, "Git directory")
    objects = git_dir / "objects"
    objects_st = _lstat_directory(objects, "Git object store")

    # External/shared object databases are outside the first governed slice.
    _reject_if_present(objects / "info" / "alternates", "object alternates")
    _reject_if_present(git_dir / "objects" / "info" / "http-alternates", "HTTP object alternates")

    config = _read_config_bytes(git_dir / "config")
    compact = b"".join(config.split())
    if b"extensions.objectformat=sha256" in compact:
        raise GitStageUnsupportedRepositoryError("SHA-256 Git repositories are not yet proven")
    if b"extensions.partialclone=" in compact or b"promisor=true" in compact:
        raise GitStageUnsupportedRepositoryError("partial/promisor repositories are not yet proven")
    if b"extensions.worktreeconfig=true" in compact:
        raise GitStageUnsupportedRepositoryError("worktree config is outside the first object-store envelope")

    return GitObjectStoreEnvelope(
        contract=OBJECT_STORE_INSPECTOR_CONTRACT,
        object_format=SUPPORTED_OBJECT_FORMAT,
        git_dir_identity=_dir_identity(git_st),
        objects_identity=_dir_identity(objects_st),
        repository_local=True,
    )


__all__ = [
    "OBJECT_STORE_INSPECTOR_CONTRACT",
    "SUPPORTED_OBJECT_FORMAT",
    "GitObjectStoreEnvelope",
    "inspect_local_object_store",
]
