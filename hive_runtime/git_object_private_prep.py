from __future__ import annotations

"""Private loose-object preparation for HCODER-WO-0023.

This module owns the private half of object publication: it materialises an
owned, bounded, no-follow temporary file inside a Hive-owned directory under the
repository's `.git`, verifies it, and removes it under identity-safe cleanup. It
**never** writes to `.git/objects` and never promotes a final object pathname.

The canonical promotion itself lives in `LooseObjectPublisher`, which links the
verified temporary into place with an atomic create-if-absent primitive. What
remains here is deliberately inert: `publish()` on the preparer is the
pre-authority placeholder and still fails closed, so the preparer can never be
mistaken for the publication authority.

The temporary directory is deliberately *not* inside `.git/objects` so that an
abandoned temporary can never be mistaken for a reachable or unreachable Git
object by Git itself.
"""

import hashlib
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path

from .git_loose_object_transaction import MAX_LOOSE_OBJECT_COMPRESSED_BYTES, GitLooseObjectPreparation
from .git_stage import GitStageUnavailableError, GitStageUnsupportedRepositoryError

PRIVATE_OBJECT_PREP_CONTRACT = "hive-git-private-object-prep-v1"
PRIVATE_TEMP_DIRNAME = "hive-object-tmp"
MAX_TEMP_NAME_ATTEMPTS = 32


@dataclass(frozen=True)
class PrivateObjectPlan:
    contract: str
    oid: str
    object_relative_path: str
    compressed_sha256: str
    compressed_bytes: int
    temp_name_prefix: str


@dataclass(frozen=True)
class PrivateObjectIdentity:
    """Filesystem identity of one capability-owned temporary object."""

    path: str
    dev: int
    ino: int
    mode: int

    def matches(self, st: os.stat_result) -> bool:
        return (int(st.st_dev), int(st.st_ino), int(st.st_mode)) == (self.dev, self.ino, self.mode)


@dataclass(frozen=True)
class PrivateObjectTemp:
    contract: str
    oid: str
    relative_path: str
    identity: PrivateObjectIdentity
    compressed_sha256: str
    compressed_bytes: int


def plan_private_object(prepared: GitLooseObjectPreparation, compressed: bytes) -> PrivateObjectPlan:
    digest = hashlib.sha256(compressed).hexdigest()
    if digest != prepared.compressed_sha256 or len(compressed) != prepared.compressed_bytes:
        raise ValueError("compressed blob no longer matches approved preparation")
    return PrivateObjectPlan(
        PRIVATE_OBJECT_PREP_CONTRACT,
        prepared.candidate.oid,
        prepared.relative_object_path,
        digest,
        len(compressed),
        f".hive-{prepared.candidate.oid}-",
    )


def _binary_flags(extra: int) -> int:
    # O_BINARY is mandatory on Windows: the CRT otherwise opens in text mode,
    # where os.write translates LF to CRLF and corrupts compressed object data.
    return extra | getattr(os, "O_BINARY", 0)



def _resolve_git_dir(workspace_root: str | os.PathLike[str]) -> Path:
    root = Path(workspace_root)
    try:
        canonical = root.resolve(strict=True)
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError("workspace root is unavailable") from exc
    git_dir = canonical / ".git"
    try:
        st = git_dir.lstat()
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError("workspace root has no provable Git directory") from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise GitStageUnsupportedRepositoryError("gitdir indirection/linked worktrees are unsupported")
    return git_dir


def _owned_temp_dir(git_dir: Path) -> Path:
    """Return the Hive-owned temporary directory, creating it if absent.

    The directory is created with mode 0700 where the platform honours POSIX
    permission bits. On Windows the mode is advisory only and the effective
    access control is the inherited ACL of the repository's `.git` directory, so
    the ownership claim here is "Hive-created, Hive-named, and never inside
    `.git/objects`" rather than "unreachable by other same-user processes".
    """
    temp_dir = git_dir / PRIVATE_TEMP_DIRNAME
    try:
        st = temp_dir.lstat()
    except FileNotFoundError:
        try:
            os.mkdir(temp_dir, 0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise GitStageUnsupportedRepositoryError("cannot create the Hive-owned temporary directory") from exc
        try:
            st = temp_dir.lstat()
        except OSError as exc:
            raise GitStageUnsupportedRepositoryError("Hive-owned temporary directory is unprovable") from exc
    except OSError as exc:
        raise GitStageUnsupportedRepositoryError("Hive-owned temporary directory is unprovable") from exc
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        raise GitStageUnsupportedRepositoryError("Hive-owned temporary directory is not a real directory")
    return temp_dir


class PrivateObjectPreparer:
    """Owns Hive-private temporary object material. Cannot publish a final object."""

    mutation_authority_enabled = False

    def __init__(self, workspace_root: str | os.PathLike[str] | None = None) -> None:
        self.workspace_root = None if workspace_root is None else Path(workspace_root)

    def plan(self, prepared: GitLooseObjectPreparation, compressed: bytes) -> PrivateObjectPlan:
        return plan_private_object(prepared, compressed)

    def materialize_private_temp(self, plan: PrivateObjectPlan, compressed: bytes) -> PrivateObjectTemp:
        """Create one owned, bounded, no-follow temporary file inside `.git`.

        This is pre-authority preparation, not publication: the bytes never reach
        `.git/objects`, nothing becomes reachable, and abandoning the temporary is
        safe. The returned identity is the only handle that may later remove it.
        """
        if not isinstance(compressed, bytes):
            raise TypeError("private object payload must be bytes")
        if len(compressed) > MAX_LOOSE_OBJECT_COMPRESSED_BYTES:
            raise GitStageUnsupportedRepositoryError("private object payload exceeds governed ceiling")
        digest = hashlib.sha256(compressed).hexdigest()
        if digest != plan.compressed_sha256 or len(compressed) != plan.compressed_bytes:
            raise ValueError("compressed blob no longer matches approved plan")
        if plan.contract != PRIVATE_OBJECT_PREP_CONTRACT:
            raise ValueError("unexpected private object plan contract")
        if self.workspace_root is None:
            raise GitStageUnavailableError("private object materialization requires a repository workspace root")

        git_dir = _resolve_git_dir(self.workspace_root)
        temp_dir = _owned_temp_dir(git_dir)

        flags = _binary_flags(os.O_RDWR | os.O_CREAT | os.O_EXCL) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        for _ in range(MAX_TEMP_NAME_ATTEMPTS):
            name = f"{plan.temp_name_prefix}{secrets.token_hex(8)}.tmp"
            path = temp_dir / name
            try:
                fd = os.open(path, flags, 0o600)
            except FileExistsError:
                continue
            except OSError as exc:
                raise GitStageUnsupportedRepositoryError("cannot create a private object temporary") from exc
            identity: PrivateObjectIdentity | None = None
            try:
                st = os.fstat(fd)
                if not stat.S_ISREG(st.st_mode):
                    raise GitStageUnsupportedRepositoryError("private object temporary is not a regular file")
                identity = PrivateObjectIdentity(str(path), int(st.st_dev), int(st.st_ino), int(st.st_mode))
                view = memoryview(compressed)
                while view:
                    written = os.write(fd, view)
                    if written <= 0:
                        raise GitStageUnsupportedRepositoryError("short write while materialising a private object")
                    view = view[written:]
                os.fsync(fd)
                os.lseek(fd, 0, os.SEEK_SET)
                reread = _read_exact(fd, len(compressed))
                if hashlib.sha256(reread).hexdigest() != plan.compressed_sha256:
                    raise GitStageUnsupportedRepositoryError("private object temporary failed its own digest proof")
            except BaseException:
                _close_and_discard_owned(fd, path, identity)
                raise
            else:
                os.close(fd)
            return PrivateObjectTemp(
                PRIVATE_OBJECT_PREP_CONTRACT,
                plan.oid,
                f"{PRIVATE_TEMP_DIRNAME}/{name}",
                identity,
                plan.compressed_sha256,
                plan.compressed_bytes,
            )
        raise GitStageUnsupportedRepositoryError("could not allocate a unique private object temporary")

    def cleanup_private_temp(self, temp: PrivateObjectTemp) -> None:
        """Remove the owned temporary when its identity is provably unchanged.

        **Bounded-race boundary, stated explicitly rather than implied.** The
        identity check and the name-based unlink are two separate operations, and
        none of the supported platforms exposes a portable delete-by-identity
        primitive for this path. A concurrent same-user process that replaces this
        pathname inside that window is outside the supported threat model of this
        pre-authority temporary, in the same way that CP-0022 records its own
        bounded-race replacement contract instead of claiming strict CAS.

        What this method does guarantee, and what is tested: a temporary whose
        identity has *already* changed, or whose ownership cannot be read, is never
        deleted. Only a regular file whose device, inode and mode still match the
        recorded identity is removed.
        """
        path = Path(temp.identity.path)
        try:
            live = path.lstat()
        except FileNotFoundError:
            return
        except OSError:
            return
        if not temp.identity.matches(live):
            # Identity changed: someone else owns this pathname now. Never remove it.
            return
        try:
            os.unlink(path)
        except OSError:
            return

    def publish(self, plan: PrivateObjectPlan) -> None:
        del plan
        raise GitStageUnavailableError("Git object publication authority is unavailable")


def _read_exact(fd: int, expected: int) -> bytes:
    chunks: list[bytes] = []
    remaining = expected
    while remaining > 0:
        chunk = os.read(fd, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _close_and_discard_owned(fd: int, path: Path, identity: PrivateObjectIdentity | None) -> None:
    """Close the handle and remove the temporary only when ownership is provable.

    Without a proven identity the file is deliberately left in place. An abandoned
    temporary inside the Hive-owned directory is inert, and leaving it is safer
    than deleting a pathname this capability cannot prove it owns.
    """
    try:
        os.close(fd)
    except OSError:
        pass
    if identity is None:
        return
    try:
        live = path.lstat()
    except OSError:
        return
    if not identity.matches(live):
        return
    try:
        os.unlink(path)
    except OSError:
        return


__all__ = [
    "MAX_TEMP_NAME_ATTEMPTS",
    "PRIVATE_OBJECT_PREP_CONTRACT",
    "PRIVATE_TEMP_DIRNAME",
    "PrivateObjectIdentity",
    "PrivateObjectPlan",
    "PrivateObjectPreparer",
    "PrivateObjectTemp",
    "plan_private_object",
]
