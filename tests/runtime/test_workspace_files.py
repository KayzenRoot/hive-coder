from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from hive_runtime.control_plane import PermissionControlPlane
from hive_runtime.control_policy import CapabilityRule, ControlPolicy
from hive_runtime.control_types import ActionRequest, ActionTarget, Capability, DecisionKind, RiskClass
from hive_runtime.errors import AuthorizationDenied, PermitError, SessionStateError, WorkspaceBoundaryError, WorkspaceMutationError
from hive_runtime.workspace_files import (
    DEFAULT_MAX_WRITE_BYTES,
    WRITE_ACTION,
    WorkspaceFileCapability,
    normalize_relative_file_path,
)


class FakeClock:
    def __init__(self, value: float = 1000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def make_plane(clock: FakeClock | None = None) -> PermissionControlPlane:
    security = clock or FakeClock()
    return PermissionControlPlane(
        security_clock=security,
        audit_clock=security,
        token_key=b"w" * 32,
        max_session_seconds=600,
        max_approval_ttl=30,
        max_permit_ttl=2,
    )


def write_policy(root: str) -> ControlPolicy:
    return ControlPolicy.build(
        [
            CapabilityRule.build(
                Capability.FILESYSTEM_WRITE,
                allowed_actions={WRITE_ACTION},
                allowed_workspace_roots={root},
            )
        ]
    )


def authorize_write(
    plane: PermissionControlPlane,
    capability: WorkspaceFileCapability,
    session_id: str,
    path: str,
    content: bytes,
) -> tuple[ActionRequest, str]:
    request = capability.prepare_write_request(session_id, path, content)
    challenge = plane.create_approval_challenge(request)
    approval = plane.approve_challenge_from_trusted_ui(challenge.challenge_id, session_id=session_id)
    permit = plane.authorize(request, approval_token=approval)
    return request, permit.token


class PathContractTests(unittest.TestCase):
    def test_filesystem_write_remains_high_and_mandatory_approval(self) -> None:
        from hive_runtime.control_types import CAPABILITY_SPECS

        spec = CAPABILITY_SPECS[Capability.FILESYSTEM_WRITE]
        self.assertEqual(spec.risk, RiskClass.HIGH)
        self.assertTrue(spec.mandatory_approval)

    def test_accepts_narrow_portable_relative_path(self) -> None:
        self.assertEqual(normalize_relative_file_path("src/module/file.py"), "src/module/file.py")

    def test_rejects_escape_and_ambiguous_path_forms(self) -> None:
        rejected = [
            "",
            " ../x",
            "../x",
            "a/../x",
            "a//x",
            "/etc/passwd",
            "//server/share",
            "C:/Windows/system.ini",
            "C:\\Windows\\system.ini",
            "file.txt:stream",
            "CON",
            "aux.txt",
            "name. ",
            "name.",
            "a\\b.txt",
            "a/./b.txt",
            "a/",
            "\x00bad",
        ]
        for path in rejected:
            with self.subTest(path=repr(path)):
                with self.assertRaises(WorkspaceBoundaryError):
                    normalize_relative_file_path(path)


class WorkspaceCapabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = self.temp.name
        os.mkdir(os.path.join(self.root, "src"))
        self.plane = make_plane()
        self.capability = WorkspaceFileCapability(self.root, self.plane)
        self.session = self.plane.create_session(write_policy(self.root), duration_seconds=60)

    def tearDown(self) -> None:
        self.capability.close()
        self.temp.cleanup()

    def test_policy_requires_trusted_approval(self) -> None:
        request = self.capability.prepare_write_request(self.session, "src/a.txt", b"alpha")
        self.assertEqual(self.plane.evaluate(request).kind, DecisionKind.REQUIRE_APPROVAL)
        with self.assertRaises(AuthorizationDenied):
            self.plane.authorize(request)

    def test_create_file_with_matching_single_use_permit(self) -> None:
        content = b"hello capability\n"
        request, token = authorize_write(self.plane, self.capability, self.session, "src/new.txt", content)
        receipt = self.capability.write_bytes(request, content, permit_token=token)
        self.assertEqual(Path(self.root, "src", "new.txt").read_bytes(), content)
        self.assertEqual(receipt.relative_path, "src/new.txt")
        self.assertEqual(receipt.content_bytes, len(content))
        self.assertNotEqual(receipt.committed_state, "absent")

    def test_replace_existing_regular_file(self) -> None:
        path = Path(self.root, "src", "existing.txt")
        path.write_bytes(b"old")
        request, token = authorize_write(self.plane, self.capability, self.session, "src/existing.txt", b"new")
        self.capability.write_bytes(request, b"new", permit_token=token)
        self.assertEqual(path.read_bytes(), b"new")

    def test_raw_content_is_not_in_request_or_audit(self) -> None:
        secret = b"NEVER-LOG-THIS-CONTENT"
        request = self.capability.prepare_write_request(self.session, "src/redacted.txt", secret)
        self.assertNotIn(secret.decode(), repr(request.arguments))
        challenge = self.plane.create_approval_challenge(request)
        self.assertNotIn(secret.decode(), repr(challenge.display_arguments))
        self.assertNotIn(secret.decode(), repr(self.plane.audit_events()))

    def test_wrong_content_rejected_before_permit_consumption(self) -> None:
        request, token = authorize_write(self.plane, self.capability, self.session, "src/content.txt", b"approved")
        with self.assertRaises(WorkspaceBoundaryError):
            self.capability.write_bytes(request, b"different", permit_token=token)
        self.capability.write_bytes(request, b"approved", permit_token=token)
        self.assertEqual(Path(self.root, "src", "content.txt").read_bytes(), b"approved")

    def test_wrong_target_request_cannot_use_original_permit(self) -> None:
        request, token = authorize_write(self.plane, self.capability, self.session, "src/a.txt", b"same")
        changed = ActionRequest(
            session_id=request.session_id,
            capability=request.capability,
            action=request.action,
            target=request.target,
            arguments={**request.arguments, "path": "src/b.txt"},
        )
        with self.assertRaises(PermitError):
            self.capability.write_bytes(changed, b"same", permit_token=token)
        self.assertFalse(Path(self.root, "src", "a.txt").exists())
        self.assertFalse(Path(self.root, "src", "b.txt").exists())

    def test_wrong_workspace_request_fails_before_mutation(self) -> None:
        request, token = authorize_write(self.plane, self.capability, self.session, "src/a.txt", b"same")
        changed = ActionRequest(
            session_id=request.session_id,
            capability=request.capability,
            action=request.action,
            target=ActionTarget(workspace=os.path.join(self.root, "src")),
            arguments=request.arguments,
        )
        with self.assertRaises(WorkspaceBoundaryError):
            self.capability.write_bytes(changed, b"same", permit_token=token)
        self.assertFalse(Path(self.root, "src", "a.txt").exists())

    def test_target_swap_after_approval_fails_closed(self) -> None:
        target = Path(self.root, "src", "swap.txt")
        target.write_bytes(b"approved-state")
        request, token = authorize_write(self.plane, self.capability, self.session, "src/swap.txt", b"new")
        target.unlink()
        target.write_bytes(b"attacker-state")
        with self.assertRaises(WorkspaceBoundaryError):
            self.capability.write_bytes(request, b"new", permit_token=token)
        self.assertEqual(target.read_bytes(), b"attacker-state")

    def test_symlink_target_fails_closed(self) -> None:
        outside = Path(self.root).parent / f"{Path(self.root).name}-outside-target.txt"
        outside.write_bytes(b"outside")
        link = Path(self.root, "src", "link.txt")
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink fixture unavailable: {exc}")
        try:
            with self.assertRaises(WorkspaceBoundaryError):
                self.capability.prepare_write_request(self.session, "src/link.txt", b"blocked")
            self.assertEqual(outside.read_bytes(), b"outside")
        finally:
            try:
                link.unlink()
            except OSError:
                pass
            outside.unlink(missing_ok=True)

    def test_symlink_parent_fails_closed(self) -> None:
        outside_dir = Path(self.root).parent / f"{Path(self.root).name}-outside-dir"
        outside_dir.mkdir(exist_ok=True)
        link = Path(self.root, "linked")
        try:
            os.symlink(outside_dir, link, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            outside_dir.rmdir()
            self.skipTest(f"symlink fixture unavailable: {exc}")
        try:
            with self.assertRaises((WorkspaceBoundaryError, OSError)):
                self.capability.prepare_write_request(self.session, "linked/escape.txt", b"blocked")
            self.assertFalse((outside_dir / "escape.txt").exists())
        finally:
            try:
                link.unlink()
            except OSError:
                pass
            outside_dir.rmdir()

    def test_oversize_payload_rejected(self) -> None:
        with self.assertRaises(WorkspaceBoundaryError):
            self.capability.prepare_write_request(self.session, "src/large.bin", b"x" * (DEFAULT_MAX_WRITE_BYTES + 1))

    def test_consumed_permit_cannot_be_replayed(self) -> None:
        request, token = authorize_write(self.plane, self.capability, self.session, "src/replay.txt", b"data")
        self.plane.consume_execution_permit(token, request)
        with self.assertRaises(PermitError):
            self.capability.write_bytes(request, b"data", permit_token=token)
        self.assertFalse(Path(self.root, "src", "replay.txt").exists())

    def test_cancelled_session_blocks_before_mutation(self) -> None:
        request, token = authorize_write(self.plane, self.capability, self.session, "src/cancel.txt", b"data")
        self.plane.cancel_session(self.session)
        with self.assertRaises(SessionStateError):
            self.capability.write_bytes(request, b"data", permit_token=token)
        self.assertFalse(Path(self.root, "src", "cancel.txt").exists())

    def test_takeover_blocks_before_mutation(self) -> None:
        request, token = authorize_write(self.plane, self.capability, self.session, "src/takeover.txt", b"data")
        self.plane.user_takeover(self.session)
        with self.assertRaises(SessionStateError):
            self.capability.write_bytes(request, b"data", permit_token=token)
        self.assertFalse(Path(self.root, "src", "takeover.txt").exists())

    def test_emergency_stop_blocks_before_mutation(self) -> None:
        request, token = authorize_write(self.plane, self.capability, self.session, "src/stop.txt", b"data")
        self.plane.emergency_stop(session_id=self.session)
        with self.assertRaises(SessionStateError):
            self.capability.write_bytes(request, b"data", permit_token=token)
        self.assertFalse(Path(self.root, "src", "stop.txt").exists())

    @unittest.skipIf(os.name == "nt", "POSIX atomic-replace fault injection")
    def test_failed_atomic_replace_preserves_old_target_and_cleans_temp(self) -> None:
        target = Path(self.root, "src", "rollback.txt")
        target.write_bytes(b"old")
        request, token = authorize_write(self.plane, self.capability, self.session, "src/rollback.txt", b"new")
        with mock.patch("hive_runtime.workspace_files.os.replace", side_effect=OSError("injected")):
            with self.assertRaises(WorkspaceMutationError):
                self.capability.write_bytes(request, b"new", permit_token=token)
        self.assertEqual(target.read_bytes(), b"old")
        self.assertEqual(list(Path(self.root, "src").glob(".hive-write-*.tmp")), [])


class PermitExpiryTests(unittest.TestCase):
    def test_stale_permit_fails_closed(self) -> None:
        clock = FakeClock()
        plane = make_plane(clock)
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, "src"))
            with WorkspaceFileCapability(root, plane) as capability:
                session = plane.create_session(write_policy(root), duration_seconds=60)
                request, token = authorize_write(plane, capability, session, "src/stale.txt", b"data")
                clock.advance(3)
                with self.assertRaises(PermitError):
                    capability.write_bytes(request, b"data", permit_token=token)
                self.assertFalse(Path(root, "src", "stale.txt").exists())


class WorkspaceIdentityTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "Windows root handle intentionally denies rename/delete sharing")
    def test_workspace_path_replacement_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as parent:
            root = Path(parent, "workspace")
            moved = Path(parent, "workspace-old")
            root.mkdir()
            plane = make_plane()
            capability = WorkspaceFileCapability(root, plane)
            try:
                session = plane.create_session(write_policy(str(root)), duration_seconds=60)
                root.rename(moved)
                root.mkdir()
                with self.assertRaises(WorkspaceBoundaryError):
                    capability.prepare_write_request(session, "a.txt", b"blocked")
                self.assertFalse((root / "a.txt").exists())
                self.assertFalse((moved / "a.txt").exists())
            finally:
                capability.close()


if __name__ == "__main__":
    unittest.main()
