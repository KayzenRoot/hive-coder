from __future__ import annotations

import hashlib
import os
import threading
import unicodedata
from dataclasses import dataclass
from typing import Mapping, Protocol

from .control_plane import PermissionControlPlane
from .control_types import ActionRequest, ActionTarget, Capability, SessionState, normalize_workspace
from .errors import ControlPlaneError, WorkspaceBoundaryError, WorkspaceMutationError

WRITE_CONTRACT = "hive-workspace-write-v1"
WRITE_ACTION = "write_file_v1"
DEFAULT_MAX_WRITE_BYTES = 1_048_576
MAX_RELATIVE_PATH_BYTES = 1024
MAX_COMPONENTS = 32
MAX_COMPONENT_BYTES = 255
_WINDOWS_RESERVED = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}
_RESERVED_COMPONENTS = {".git"}
_WINDOWS_FORBIDDEN_CHARS = set('<>"|?*')
_REJECTED_UNICODE_CATEGORIES = {"Cc", "Cf", "Cs", "Zl", "Zp"}


@dataclass(frozen=True)
class WorkspaceWriteReceipt:
    workspace: str
    relative_path: str
    parent_identity: str
    content_sha256: str
    content_bytes: int
    committed_state: str


class _PreparedCreate(Protocol):
    parent_identity: str

    def revalidate_absent(self) -> None: ...

    def publish(self, content: bytes, pre_publish_check) -> str: ...

    def close(self) -> None: ...


class _Backend(Protocol):
    canonical_root: str

    def prepare_create(self, relative_path: str) -> _PreparedCreate: ...

    def close(self) -> None: ...


def normalize_relative_file_path(value: str) -> str:
    if not isinstance(value, str):
        raise WorkspaceBoundaryError("relative path must be text")
    if not value or value != value.strip():
        raise WorkspaceBoundaryError("relative path is empty or padded")
    if unicodedata.normalize("NFC", value) != value:
        raise WorkspaceBoundaryError("relative path must be NFC-normalized")
    for character in value:
        if unicodedata.category(character) in _REJECTED_UNICODE_CATEGORIES:
            raise WorkspaceBoundaryError("relative path contains control or display-format characters")
        if character in _WINDOWS_FORBIDDEN_CHARS:
            raise WorkspaceBoundaryError("relative path contains non-portable filename characters")
    if "\\" in value:
        raise WorkspaceBoundaryError("backslash path syntax is not accepted")
    if value.startswith("/") or value.startswith("//"):
        raise WorkspaceBoundaryError("absolute paths are not accepted")
    try:
        encoded_value = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise WorkspaceBoundaryError("relative path is not valid UTF-8 text") from exc
    if len(encoded_value) > MAX_RELATIVE_PATH_BYTES:
        raise WorkspaceBoundaryError("relative path exceeds byte ceiling")

    parts = value.split("/")
    if not parts or len(parts) > MAX_COMPONENTS:
        raise WorkspaceBoundaryError("relative path has too many components")
    normalized: list[str] = []
    for part in parts:
        if part in {"", ".", ".."}:
            raise WorkspaceBoundaryError("relative path contains traversal or empty component")
        folded = part.casefold()
        if folded in _RESERVED_COMPONENTS:
            raise WorkspaceBoundaryError("VCS-internal path components are outside filesystem-write authority")
        if len(part.encode("utf-8")) > MAX_COMPONENT_BYTES:
            raise WorkspaceBoundaryError("path component exceeds byte ceiling")
        if ":" in part:
            raise WorkspaceBoundaryError("drive/device/alternate-stream syntax is not accepted")
        if part.endswith((" ", ".")):
            raise WorkspaceBoundaryError("ambiguous trailing dot/space component is not accepted")
        if part.split(".", 1)[0].casefold() in _WINDOWS_RESERVED:
            raise WorkspaceBoundaryError("reserved device filename is not accepted")
        normalized.append(part)
    return "/".join(normalized)


def _content_bytes(content: bytes | bytearray | memoryview) -> bytes:
    if not isinstance(content, (bytes, bytearray, memoryview)):
        raise WorkspaceBoundaryError("content must be bytes-like")
    return bytes(content)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_backend(workspace_root: str | os.PathLike[str]) -> _Backend:
    if os.name == "nt":
        from .workspace_files_windows import WindowsWorkspaceBackend

        return WindowsWorkspaceBackend(workspace_root)

    from .workspace_files_posix import PosixWorkspaceBackend

    return PosixWorkspaceBackend(workspace_root)


class WorkspaceFileCapability:
    """Permit-gated atomic create-only workspace mutation capability.

    WO-0021 deliberately does not overwrite, append, truncate, delete or rename
    existing user files. Approval/permit authority remains exclusively inside
    PermissionControlPlane and its trusted-UI boundary.
    """

    def __init__(
        self,
        workspace_root: str | os.PathLike[str],
        control_plane: PermissionControlPlane,
        *,
        max_write_bytes: int = DEFAULT_MAX_WRITE_BYTES,
    ) -> None:
        if not isinstance(control_plane, PermissionControlPlane):
            raise TypeError("control_plane must be PermissionControlPlane")
        ceiling = int(max_write_bytes)
        if ceiling <= 0 or ceiling > DEFAULT_MAX_WRITE_BYTES:
            raise ValueError("max_write_bytes outside governed ceiling")
        self._plane = control_plane
        self._max_write_bytes = ceiling
        self._lock = threading.RLock()
        self._closed = False
        self._backend = _build_backend(workspace_root)
        self.workspace = normalize_workspace(self._backend.canonical_root)

    def __enter__(self) -> "WorkspaceFileCapability":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._backend.close()
            self._closed = True

    def prepare_write_request(
        self,
        session_id: str,
        relative_path: str,
        content: bytes | bytearray | memoryview,
    ) -> ActionRequest:
        data = _content_bytes(content)
        self._validate_size(data)
        relative = normalize_relative_file_path(relative_path)
        with self._lock:
            self._require_open()
            prepared = self._backend.prepare_create(relative)
            try:
                prepared.revalidate_absent()
                parent_identity = prepared.parent_identity
            finally:
                prepared.close()
        return ActionRequest(
            session_id=str(session_id),
            capability=Capability.FILESYSTEM_WRITE,
            action=WRITE_ACTION,
            target=ActionTarget(workspace=self.workspace),
            arguments={
                "contract": WRITE_CONTRACT,
                "path": relative,
                "parent_identity": parent_identity,
                "target_state": "absent",
                "content_sha256": _sha256(data),
                "content_bytes": len(data),
            },
        )

    def write_bytes(
        self,
        request: ActionRequest,
        content: bytes | bytearray | memoryview,
        *,
        permit_token: str,
    ) -> WorkspaceWriteReceipt:
        data = _content_bytes(content)
        self._validate_size(data)
        relative, expected_parent = self._validate_request(request, data)

        with self._lock:
            self._require_open()
            prepared = self._backend.prepare_create(relative)
            try:
                if prepared.parent_identity != expected_parent:
                    raise WorkspaceBoundaryError("parent identity changed after approval request")
                prepared.revalidate_absent()

                # All read-only validation is complete. Permit consumption is the
                # final authorization operation immediately before the first OS
                # mutation (creation of a private same-parent temporary file).
                self._plane.consume_execution_permit(permit_token, request)
                self._require_active(request.session_id)

                def pre_publish_check() -> None:
                    self._require_active(request.session_id)
                    prepared.revalidate_absent()

                committed_state = prepared.publish(data, pre_publish_check)
            except WorkspaceBoundaryError:
                raise
            except ControlPlaneError as exc:
                raise WorkspaceMutationError("control-plane authorization rejected workspace create") from exc
            except WorkspaceMutationError:
                raise
            except Exception as exc:
                raise WorkspaceMutationError("workspace create failed closed") from exc
            finally:
                prepared.close()

        return WorkspaceWriteReceipt(
            workspace=self.workspace,
            relative_path=relative,
            parent_identity=expected_parent,
            content_sha256=_sha256(data),
            content_bytes=len(data),
            committed_state=committed_state,
        )

    def _validate_request(self, request: ActionRequest, data: bytes) -> tuple[str, str]:
        try:
            capability = Capability(request.capability)
        except (TypeError, ValueError) as exc:
            raise WorkspaceBoundaryError("request capability is invalid") from exc
        if capability is not Capability.FILESYSTEM_WRITE:
            raise WorkspaceBoundaryError("request capability is not filesystem.write")
        if str(request.action).strip() != WRITE_ACTION:
            raise WorkspaceBoundaryError("request action is not the governed create contract")
        canonical_target = request.target.canonical()
        if canonical_target.get("workspace") != self.workspace:
            raise WorkspaceBoundaryError("request workspace does not match capability workspace")
        args: Mapping[str, object] = request.arguments
        if not isinstance(args, Mapping):
            raise WorkspaceBoundaryError("request arguments must be a mapping")
        required = {"contract", "path", "parent_identity", "target_state", "content_sha256", "content_bytes"}
        if set(args) != required:
            raise WorkspaceBoundaryError("request arguments do not match create contract")
        if args.get("contract") != WRITE_CONTRACT:
            raise WorkspaceBoundaryError("write contract mismatch")
        relative = normalize_relative_file_path(args.get("path"))  # type: ignore[arg-type]
        parent_identity = args.get("parent_identity")
        if not isinstance(parent_identity, str) or not parent_identity:
            raise WorkspaceBoundaryError("parent identity is missing")
        if args.get("target_state") != "absent":
            raise WorkspaceBoundaryError("WO-0021 only authorizes creation of an absent target")
        if args.get("content_bytes") != len(data):
            raise WorkspaceBoundaryError("content length does not match approved request")
        if args.get("content_sha256") != _sha256(data):
            raise WorkspaceBoundaryError("content digest does not match approved request")
        return relative, parent_identity

    def _validate_size(self, data: bytes) -> None:
        if len(data) > self._max_write_bytes:
            raise WorkspaceBoundaryError("write payload exceeds governed byte ceiling")

    def _require_active(self, session_id: str) -> None:
        if self._plane.session_state(session_id) is not SessionState.ACTIVE:
            raise WorkspaceMutationError("control session is not active")

    def _require_open(self) -> None:
        if self._closed:
            raise WorkspaceBoundaryError("workspace capability is closed")
