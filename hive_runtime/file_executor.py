from __future__ import annotations

import hashlib
import re
import threading
from dataclasses import dataclass
from typing import Mapping, Protocol

from .control_plane import PermissionControlPlane
from .control_types import ActionRequest, ActionTarget, Capability, normalize_workspace
from .errors import AdapterStateError, AuthorizationDenied, RpcProtocolError

FILE_REPLACE_TEXT = "file.replace_text"
MAX_RELATIVE_PATH_CHARS = 512
MAX_PATH_COMPONENT_CHARS = 120
MAX_REPLACEMENT_BYTES = 256 * 1024
MAX_EXISTING_FILE_BYTES = 4 * 1024 * 1024

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTITY = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
_WINDOWS_RESERVED = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


@dataclass(frozen=True)
class FileMutationGuarantees:
    root_bound: bool
    no_follow: bool
    atomic_replace: bool


@dataclass(frozen=True)
class FileObservation:
    workspace_identity: str
    parent_identity: str
    target_identity: str
    relative_path: str
    content_sha256: str
    size_bytes: int
    exists: bool
    regular_file: bool
    root_bound: bool
    no_follow: bool


@dataclass(frozen=True)
class FileMutationReceipt:
    relative_path: str
    before_sha256: str
    after_sha256: str
    bytes_written: int
    target_identity: str
    root_bound: bool
    no_follow: bool
    atomic_replace: bool


class FileMutationPort(Protocol):
    def guarantees(self) -> FileMutationGuarantees: ...

    def observe(self, *, workspace: str, relative_path: str) -> FileObservation: ...

    def replace_text(
        self,
        *,
        workspace: str,
        relative_path: str,
        content: str,
        expected: FileObservation,
    ) -> FileMutationReceipt: ...


def canonical_relative_path(raw: str) -> str:
    if not isinstance(raw, str) or raw != raw.strip() or not raw or len(raw) > MAX_RELATIVE_PATH_CHARS:
        raise AuthorizationDenied("file_relative_path_invalid")
    if "\x00" in raw or "\\" in raw or raw.startswith("/") or ":" in raw:
        raise AuthorizationDenied("file_relative_path_invalid")
    parts = raw.split("/")
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise AuthorizationDenied("file_relative_path_invalid")
    for part in parts:
        if len(part) > MAX_PATH_COMPONENT_CHARS or part.endswith((".", " ")):
            raise AuthorizationDenied("file_relative_path_invalid")
        if any(ord(character) < 32 for character in part):
            raise AuthorizationDenied("file_relative_path_invalid")
        if part.split(".", 1)[0].upper() in _WINDOWS_RESERVED:
            raise AuthorizationDenied("file_relative_path_invalid")
    return "/".join(parts)


def _utf8_content(content: str) -> tuple[bytes, str]:
    if not isinstance(content, str) or not content or "\x00" in content:
        raise AuthorizationDenied("file_replacement_content_invalid")
    encoded = content.encode("utf-8")
    if len(encoded) > MAX_REPLACEMENT_BYTES:
        raise AuthorizationDenied("file_replacement_content_outside_bounds")
    return encoded, hashlib.sha256(encoded).hexdigest()


def _identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not _IDENTITY.fullmatch(value):
        raise AuthorizationDenied(f"file_{field}_identity_invalid")
    return value


def _sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise AuthorizationDenied(f"file_{field}_sha256_invalid")
    return value


def _count(value: object, field: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > maximum:
        raise AuthorizationDenied(f"file_{field}_invalid")
    return value


class GatedFileActionExecutor:
    """Permit-gated contract for one safe file mutation action.

    This executor intentionally owns no production filesystem backend. The trusted
    host injects a FileMutationPort whose root-bound/no-follow/atomic guarantees
    are independently governed. Model/tool surfaces must never select the port.
    """

    _ARGUMENT_KEYS = frozenset(
        {
            "relative_path",
            "content_sha256",
            "content_bytes",
            "expected_workspace_identity",
            "expected_parent_identity",
            "expected_target_identity",
            "expected_content_sha256",
            "expected_size_bytes",
        }
    )

    def __init__(self, *, control_plane: PermissionControlPlane, port: FileMutationPort) -> None:
        self.control_plane = control_plane
        self.port = port
        self._lock = threading.RLock()
        self._cancelled_sessions: set[str] = set()
        self._inflight: set[str] = set()

    def cancellation_callback(self, session_id: str, reason: str) -> None:
        del reason
        with self._lock:
            self._cancelled_sessions.add(session_id)

    def prepare_replace_request(
        self,
        *,
        session_id: str,
        workspace: str,
        relative_path: str,
        content: str,
    ) -> ActionRequest:
        self._require_port_guarantees()
        normalized_workspace = normalize_workspace(workspace)
        normalized_path = canonical_relative_path(relative_path)
        encoded, content_digest = _utf8_content(content)
        observed = self._validated_observation(
            self.port.observe(workspace=normalized_workspace, relative_path=normalized_path),
            normalized_path,
        )
        return ActionRequest(
            session_id=session_id,
            capability=Capability.FILESYSTEM_WRITE,
            action=FILE_REPLACE_TEXT,
            target=ActionTarget(workspace=normalized_workspace),
            arguments={
                "relative_path": normalized_path,
                "content_sha256": content_digest,
                "content_bytes": len(encoded),
                "expected_workspace_identity": observed.workspace_identity,
                "expected_parent_identity": observed.parent_identity,
                "expected_target_identity": observed.target_identity,
                "expected_content_sha256": observed.content_sha256,
                "expected_size_bytes": observed.size_bytes,
            },
        )

    def execute(self, request: ActionRequest, *, permit_token: str, content: str) -> FileMutationReceipt:
        workspace, relative_path, expected = self._validated_request(request)
        encoded, digest = _utf8_content(content)
        if digest != expected["content_sha256"] or len(encoded) != expected["content_bytes"]:
            raise AuthorizationDenied("file_replacement_content_fingerprint_mismatch")
        self._require_port_guarantees()

        with self._lock:
            if request.session_id in self._cancelled_sessions:
                raise AuthorizationDenied("control_session_cancelled_before_execution")
            if request.session_id in self._inflight:
                raise AuthorizationDenied("parallel_file_mutation_for_session_denied")
            self._inflight.add(request.session_id)

        try:
            self.control_plane.consume_execution_permit(permit_token, request)
            self._deny_if_cancelled(request.session_id, "control_session_cancelled_before_revalidation")
            live = self._validated_observation(
                self.port.observe(workspace=workspace, relative_path=relative_path),
                relative_path,
            )
            self._require_expected_observation(live, expected)
            self._deny_if_cancelled(request.session_id, "control_session_cancelled_before_dispatch")
            try:
                receipt = self.port.replace_text(
                    workspace=workspace,
                    relative_path=relative_path,
                    content=content,
                    expected=live,
                )
            except Exception as exc:
                raise AdapterStateError("file mutation backend failed") from None
            return self._validated_receipt(receipt, live, digest, len(encoded), relative_path)
        finally:
            with self._lock:
                self._inflight.discard(request.session_id)

    def _deny_if_cancelled(self, session_id: str, reason: str) -> None:
        with self._lock:
            if session_id in self._cancelled_sessions:
                raise AuthorizationDenied(reason)

    def _require_port_guarantees(self) -> None:
        try:
            guarantees = self.port.guarantees()
        except Exception:
            raise AdapterStateError("file mutation backend guarantees unavailable") from None
        if not isinstance(guarantees, FileMutationGuarantees):
            raise AdapterStateError("file mutation backend guarantees invalid")
        if not (guarantees.root_bound and guarantees.no_follow and guarantees.atomic_replace):
            raise AdapterStateError("file mutation backend is not HIGH_ASSURANCE capable")

    @classmethod
    def _validated_request(cls, request: ActionRequest) -> tuple[str, str, dict[str, object]]:
        capability = request.capability.value if isinstance(request.capability, Capability) else str(request.capability)
        if capability != Capability.FILESYSTEM_WRITE.value:
            raise AuthorizationDenied("file_action_capability_mismatch")
        if str(request.action) != FILE_REPLACE_TEXT:
            raise AuthorizationDenied("file_action_not_allowlisted")
        workspace = request.target.canonical().get("workspace")
        if not workspace:
            raise AuthorizationDenied("file_workspace_target_missing")
        if not isinstance(request.arguments, Mapping) or set(request.arguments) != cls._ARGUMENT_KEYS:
            raise AuthorizationDenied("file_arguments_not_allowlisted")
        args = dict(request.arguments)
        relative_path = canonical_relative_path(args["relative_path"])
        expected: dict[str, object] = {
            "content_sha256": _sha256(args["content_sha256"], "replacement"),
            "content_bytes": _count(args["content_bytes"], "replacement_size", MAX_REPLACEMENT_BYTES),
            "workspace_identity": _identity(args["expected_workspace_identity"], "workspace"),
            "parent_identity": _identity(args["expected_parent_identity"], "parent"),
            "target_identity": _identity(args["expected_target_identity"], "target"),
            "content_before_sha256": _sha256(args["expected_content_sha256"], "existing_content"),
            "size_before_bytes": _count(args["expected_size_bytes"], "existing_size", MAX_EXISTING_FILE_BYTES),
        }
        return workspace, relative_path, expected

    @staticmethod
    def _validated_observation(observed: FileObservation, relative_path: str) -> FileObservation:
        if not isinstance(observed, FileObservation):
            raise AdapterStateError("file mutation backend observation invalid")
        if observed.relative_path != relative_path:
            raise AuthorizationDenied("file_live_relative_path_mismatch")
        _identity(observed.workspace_identity, "workspace")
        _identity(observed.parent_identity, "parent")
        _identity(observed.target_identity, "target")
        _sha256(observed.content_sha256, "existing_content")
        _count(observed.size_bytes, "existing_size", MAX_EXISTING_FILE_BYTES)
        if not (observed.exists and observed.regular_file and observed.root_bound and observed.no_follow):
            raise AuthorizationDenied("file_live_target_not_safe_regular_file")
        return observed

    @staticmethod
    def _require_expected_observation(live: FileObservation, expected: Mapping[str, object]) -> None:
        checks = {
            "workspace_identity": live.workspace_identity,
            "parent_identity": live.parent_identity,
            "target_identity": live.target_identity,
            "content_before_sha256": live.content_sha256,
            "size_before_bytes": live.size_bytes,
        }
        for key, actual in checks.items():
            if actual != expected[key]:
                raise AuthorizationDenied(f"file_live_{key}_mismatch")

    @staticmethod
    def _validated_receipt(
        receipt: FileMutationReceipt,
        before: FileObservation,
        after_sha256: str,
        bytes_written: int,
        relative_path: str,
    ) -> FileMutationReceipt:
        if not isinstance(receipt, FileMutationReceipt):
            raise RpcProtocolError("file mutation backend receipt invalid")
        if receipt.relative_path != relative_path:
            raise RpcProtocolError("file mutation receipt path mismatch")
        if receipt.before_sha256 != before.content_sha256 or receipt.after_sha256 != after_sha256:
            raise RpcProtocolError("file mutation receipt digest mismatch")
        if receipt.bytes_written != bytes_written:
            raise RpcProtocolError("file mutation receipt byte count mismatch")
        _identity(receipt.target_identity, "receipt_target")
        if not (receipt.root_bound and receipt.no_follow and receipt.atomic_replace):
            raise RpcProtocolError("file mutation receipt lacks HIGH_ASSURANCE guarantees")
        return receipt
