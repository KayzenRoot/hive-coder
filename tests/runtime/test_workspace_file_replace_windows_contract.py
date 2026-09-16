from __future__ import annotations

import os
import unittest

from hive_runtime.workspace_replace_contract import WorkspaceReplaceObservedState


@unittest.skipUnless(os.name == "nt", "Windows replacement contract")
class WindowsReplaceContractTests(unittest.TestCase):
    def test_unproven_native_adapter_cannot_reach_mutation_ready(self) -> None:
        from hive_runtime.workspace_replace_windows import WindowsPreparedReplace

        observed = WorkspaceReplaceObservedState(
            parent_identity="win-id:1:10",
            target_identity="win-id:1:11",
            content_sha256="0" * 64,
            content_bytes=0,
        )
        prepared = WindowsPreparedReplace(observed=observed)
        try:
            with self.assertRaises(NotImplementedError):
                prepared.revalidate_expected(observed)
            with self.assertRaises(NotImplementedError):
                prepared.stage_replace(b"new", observed)
            with self.assertRaises(NotImplementedError):
                prepared.mutation_ready(observed)
            with self.assertRaises(NotImplementedError):
                prepared.publish_replace(observed, lambda: None)
        finally:
            prepared.close()

    def test_windows_contract_exposes_corrected_staging_protocol(self) -> None:
        from hive_runtime.workspace_replace_windows import WindowsPreparedReplace

        self.assertTrue(callable(getattr(WindowsPreparedReplace, "revalidate_expected")))
        self.assertTrue(callable(getattr(WindowsPreparedReplace, "stage_replace")))
        self.assertTrue(callable(getattr(WindowsPreparedReplace, "mutation_ready")))
        self.assertTrue(callable(getattr(WindowsPreparedReplace, "publish_replace")))
        self.assertTrue(callable(getattr(WindowsPreparedReplace, "close")))


if __name__ == "__main__":
    unittest.main()
