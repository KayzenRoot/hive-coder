import unittest

from hive_runtime.cua import CuaAdapter


class PrivilegedSurfaceTests(unittest.TestCase):
    def test_cua_adapter_still_has_no_tool_call_surface(self) -> None:
        self.assertFalse(hasattr(CuaAdapter, "call_tool"))


if __name__ == "__main__":
    unittest.main()
