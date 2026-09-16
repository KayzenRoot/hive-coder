from __future__ import annotations

import os
import secrets
import stat
from typing import Callable

from .errors import WorkspaceBoundaryError, WorkspaceMutationError

_TEMP_PREFIX = ".hive-create-"


class PosixWorkspaceBackend:
    def __init__(self, workspace_root: str | os.PathLike[str]) -> None:
        raw = os.fspath(workspace_root)
        if not raw:
            raise WorkspaceBoundaryError("workspace root is empty")
        try:
            lst = os.lstat(raw)
        except OSError as exc:
            raise WorkspaceBoundaryError("workspace root is unavailable") from exc
        if stat.S_ISLNK(lst.st_mode) or not stat.S_ISDIR(lst.st_mode):
            raise WorkspaceBoundaryError("workspace root must be a real directory")

        self.canonical_root = os.path.realpath(raw)
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            self._root_fd = os.open(self.canonical_root, flags)
        except OSError as exc:
            raise WorkspaceBoundaryError("workspace root could not be opened no-follow") from exc
        info = os.fstat(self._root_fd)
        if not stat.S_ISDIR(info.st_mode):
            os.close(self._root_fd)
            raise WorkspaceBoundaryError("workspace root handle is not a directory")
        self._root_identity = self._dir_identity(info)
        self._closed = False

    @staticmethod
    def _dir_identity(info: os.stat_result) -> str:
        return f"posix-dir:{info.st_dev}:{info.st_ino}"

    def close(self) -> None:
        if self._closed:
            return
        os.close(self._root_fd)
        self._closed = True

    def _open_parent(self, relative_path: str) -> tuple[int, tuple[str, ...], str]:
        if self._closed:
            raise WorkspaceBoundaryError("workspace backend is closed")
        self._revalidate_root_path()
        parts = relative_path.split("/")
        parent_fd = os.dup(self._root_fd)
        parent_parts: list[str] = []
        try:
            flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            for component in parts[:-1]:
                try:
                    next_fd = os.open(component, flags, dir_fd=parent_fd)
                except OSError as exc:
                    raise WorkspaceBoundaryError("parent component could not be opened no-follow") from exc
                info = os.fstat(next_fd)
                if not stat.S_ISDIR(info.st_mode):
                    os.close(next_fd)
                    raise WorkspaceBoundaryError("parent component is not a directory")
                os.close(parent_fd)
                parent_fd = next_fd
                parent_parts.append(component)
            return parent_fd, tuple(parent_parts), parts[-1]
        except Exception:
            os.close(parent_fd)
            raise

    def prepare_create(self, relative_path: str) -> "PosixPreparedCreate":
        parent_fd, parent_parts, leaf = self._open_parent(relative_path)
        try:
            return PosixPreparedCreate(self, parent_fd, parent_parts, leaf)
        except Exception:
            os.close(parent_fd)
            raise

    def prepare_replace(self, relative_path: str):
        """Read-only pinning of an existing regular target for WO-0022."""
        from .workspace_replace_posix import PosixPreparedReplace

        parent_fd, parent_parts, leaf = self._open_parent(relative_path)
        target_fd: int | None = None
        try:
            flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            try:
                target_fd = os.open(leaf, flags, dir_fd=parent_fd)
            except OSError as exc:
                raise WorkspaceBoundaryError("replacement target could not be opened no-follow") from exc
            info = os.fstat(target_fd)
            if not stat.S_ISREG(info.st_mode):
                raise WorkspaceBoundaryError("replacement target is not a regular file")
            prepared = PosixPreparedReplace(self, parent_fd, parent_parts, leaf, target_fd)
            parent_fd = -1
            target_fd = None
            return prepared
        finally:
            if target_fd is not None:
                os.close(target_fd)
            if parent_fd >= 0:
                os.close(parent_fd)

    def current_parent_identity(self, parent_parts: tuple[str, ...]) -> str:
        fd = os.dup(self._root_fd)
        try:
            flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            for component in parent_parts:
                try:
                    next_fd = os.open(component, flags, dir_fd=fd)
                except OSError as exc:
                    raise WorkspaceBoundaryError("current parent path could not be reopened no-follow") from exc
                info = os.fstat(next_fd)
                if not stat.S_ISDIR(info.st_mode):
                    os.close(next_fd)
                    raise WorkspaceBoundaryError("current parent component is not a directory")
                os.close(fd)
                fd = next_fd
            return self._dir_identity(os.fstat(fd))
        finally:
            os.close(fd)

    def _revalidate_root_path(self) -> None:
        try:
            info = os.stat(self.canonical_root, follow_symlinks=False)
        except OSError as exc:
            raise WorkspaceBoundaryError("workspace root path is no longer available") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise WorkspaceBoundaryError("workspace root path changed type")
        if self._dir_identity(info) != self._root_identity:
            raise WorkspaceBoundaryError("workspace root identity changed")


class PosixPreparedCreate:
    def __init__(
        self,
        backend: PosixWorkspaceBackend,
        parent_fd: int,
        parent_parts: tuple[str, ...],
        leaf: str,
    ) -> None:
        self._backend = backend
        self._parent_fd = parent_fd
        self._parent_parts = parent_parts
        self._leaf = leaf
        self._closed = False
        self.parent_identity = backend._dir_identity(os.fstat(parent_fd))
        self.revalidate_absent()

    def close(self) -> None:
        if not self._closed:
            os.close(self._parent_fd)
            self._closed = True

    def revalidate_absent(self) -> None:
        if self._closed:
            raise WorkspaceBoundaryError("prepared target is closed")
        self._backend._revalidate_root_path()
        if self._backend.current_parent_identity(self._parent_parts) != self.parent_identity:
            raise WorkspaceBoundaryError("parent path identity changed")
        if self._backend._dir_identity(os.fstat(self._parent_fd)) != self.parent_identity:
            raise WorkspaceBoundaryError("pinned parent identity changed")
        try:
            os.stat(self._leaf, dir_fd=self._parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise WorkspaceBoundaryError("target absence could not be proven") from exc
        raise WorkspaceBoundaryError("WO-0021 create-only target already exists")

    def publish(self, content: bytes, pre_publish_check: Callable[[], None]) -> str:
        temp_name = f"{_TEMP_PREFIX}{secrets.token_hex(16)}.tmp"
        fd: int | None = None
        temp_identity: tuple[int, int] | None = None
        temp_exists = False
        published = False
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(temp_name, flags, 0o600, dir_fd=self._parent_fd)
            temp_exists = True
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise WorkspaceBoundaryError("temporary target is not a regular file")
            temp_identity = (info.st_dev, info.st_ino)

            view = memoryview(content)
            offset = 0
            while offset < len(view):
                written = os.write(fd, view[offset:])
                if written <= 0:
                    raise OSError("short workspace write")
                offset += written
            os.fsync(fd)

            pre_publish_check()
            try:
                os.link(
                    temp_name,
                    self._leaf,
                    src_dir_fd=self._parent_fd,
                    dst_dir_fd=self._parent_fd,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise WorkspaceBoundaryError("target appeared before atomic no-clobber publication") from exc
            published = True
            committed = self._read_committed_state()

            try:
                os.unlink(temp_name, dir_fd=self._parent_fd)
                temp_exists = False
            except OSError:
                pass
            try:
                os.fsync(self._parent_fd)
            except OSError:
                pass
            return committed
        except WorkspaceBoundaryError:
            raise
        except OSError as exc:
            raise WorkspaceMutationError("atomic create-only publication failed") from exc
        finally:
            if fd is not None:
                os.close(fd)
            if temp_exists and not published and temp_identity is not None:
                self._unlink_temp_if_same(temp_name, temp_identity)

    def _read_committed_state(self) -> str:
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(self._leaf, flags, dir_fd=self._parent_fd)
        except OSError as exc:
            raise WorkspaceMutationError("published target cannot be reopened no-follow") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise WorkspaceMutationError("published target is not a regular file")
            return f"posix-file:{info.st_dev}:{info.st_ino}:{info.st_size}:{info.st_mtime_ns}"
        finally:
            os.close(fd)

    def _unlink_temp_if_same(self, temp_name: str, identity: tuple[int, int]) -> None:
        try:
            info = os.stat(temp_name, dir_fd=self._parent_fd, follow_symlinks=False)
            if stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == identity:
                os.unlink(temp_name, dir_fd=self._parent_fd)
        except OSError:
            pass
