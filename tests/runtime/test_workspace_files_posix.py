from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from hive_runtime.errors import WorkspaceBoundaryError
from hive_runtime.workspace_files import WorkspaceFileCapability
from tests.runtime.test_workspace_files import authorize_write, make_plane, write_policy


@unittest.skipIf(os.name == "nt", "POSIX-only HIGH_ASSURANCE workspace capability tests")
class PosixWorkspaceCapabilityTests(unittest.TestCase):
    def test_target_created_at_atomic_publication_is_preserved(self) -> None:
        import hive_runtime.workspace_files_posix as posix_backend

        with tempfile.TemporaryDirectory() as root_text:
            root = Path(root_text)
            (root / "src").mkdir()
            plane = make_plane()
            with WorkspaceFileCapability(root, plane) as capability:
                session = plane.create_session(write_policy(str(root)), duration_seconds=60)
                target = root / "src" / "race.txt"
                request, token = authorize_write(
                    plane,
                    capability,
                    session,
                    "src/race.txt",
                    b"approved-content",
                )
                original = os.link

                def race(src, dst, *args, **kwargs):
                    target.write_bytes(b"concurrent-owner")
                    return original(src, dst, *args, **kwargs)

                with mock.patch.object(posix_backend.os, "link", side_effect=race):
                    with self.assertRaises(WorkspaceBoundaryError):
                        capability.write_bytes(request, b"approved-content", permit_token=token)

                self.assertEqual(target.read_bytes(), b"concurrent-owner")
                self.assertEqual(list((root / "src").glob(".hive-create-*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
