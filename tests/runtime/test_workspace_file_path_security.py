from __future__ import annotations

import unittest

from hive_runtime.errors import WorkspaceBoundaryError
from hive_runtime.workspace_files import normalize_relative_file_path


class WorkspaceFilePathSecurityTests(unittest.TestCase):
    def test_git_internal_components_are_outside_filesystem_write_authority(self) -> None:
        for value in (
            ".git/hooks/pre-commit",
            ".GIT/hooks/post-checkout",
            "nested/.git/config.lock",
        ):
            with self.subTest(value=value):
                with self.assertRaises(WorkspaceBoundaryError):
                    normalize_relative_file_path(value)

    def test_control_and_bidi_format_characters_are_rejected(self) -> None:
        for value in (
            "src/line\nbreak.txt",
            "src/tab\tname.txt",
            "src/reversed-\u202egnp.txt",
            "src/word-joiner-\u2060.txt",
            "src/line-separator-\u2028.txt",
            "src/paragraph-separator-\u2029.txt",
        ):
            with self.subTest(value=repr(value)):
                with self.assertRaises(WorkspaceBoundaryError):
                    normalize_relative_file_path(value)

    def test_windows_forbidden_filename_characters_are_rejected_portably(self) -> None:
        for value in (
            'src/quote"name.txt',
            "src/question?.txt",
            "src/star*.txt",
            "src/less<name.txt",
            "src/greater>name.txt",
            "src/pipe|name.txt",
        ):
            with self.subTest(value=value):
                with self.assertRaises(WorkspaceBoundaryError):
                    normalize_relative_file_path(value)


if __name__ == "__main__":
    unittest.main()
