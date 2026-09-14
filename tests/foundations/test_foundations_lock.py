import unittest
from copy import deepcopy

from tools.foundations.verify_lock import load_lock, validate_lock


class FoundationLockTests(unittest.TestCase):
    def test_repository_lock_is_valid(self) -> None:
        self.assertEqual(validate_lock(load_lock()), [])

    def test_unknown_license_fails_closed(self) -> None:
        data = deepcopy(load_lock())
        data["foundations"]["cuaDriver"]["license"] = "UNKNOWN"
        self.assertTrue(any("unapproved license" in e for e in validate_lock(data)))

    def test_auto_install_cannot_be_enabled(self) -> None:
        data = deepcopy(load_lock())
        data["policy"]["autoInstall"] = True
        self.assertIn("autoInstall must remain false", validate_lock(data))

    def test_unknown_versions_must_fail_closed(self) -> None:
        data = deepcopy(load_lock())
        data["policy"]["failOnUnknownVersion"] = False
        self.assertIn("failOnUnknownVersion must remain true", validate_lock(data))


if __name__ == "__main__":
    unittest.main()
