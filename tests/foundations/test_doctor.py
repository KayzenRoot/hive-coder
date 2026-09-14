import unittest
from unittest.mock import patch

from tools.foundations.doctor import _reports_exact_version, inspect
from tools.foundations.verify_lock import load_lock


class DoctorTests(unittest.TestCase):
    def test_inventory_is_side_effect_free(self) -> None:
        report = inspect(load_lock(), inventory_only=True)
        self.assertEqual(report["status"], "LOCKED")
        self.assertEqual(report["sideEffects"], "NONE")

    def test_normal_doctor_discloses_external_probe(self) -> None:
        with patch("tools.foundations.doctor._locate", return_value=None):
            report = inspect(load_lock())
        self.assertEqual(report["sideEffects"], "EXTERNAL_VERSION_PROBE")

    def test_exact_version_match_rejects_lookalikes(self) -> None:
        self.assertTrue(_reports_exact_version("interpreter 0.0.43", "0.0.43"))
        self.assertFalse(_reports_exact_version("interpreter 0.0.430", "0.0.43"))
        self.assertFalse(_reports_exact_version("interpreter 0.0.43-beta.1", "0.0.43"))
        self.assertFalse(_reports_exact_version("interpreter v0.0.43", "0.0.43"))

    @patch("tools.foundations.doctor._locate", return_value=None)
    def test_missing_binaries_fail_closed(self, _locate) -> None:
        report = inspect(load_lock())
        self.assertEqual(report["status"], "NOT_READY")
        self.assertTrue(all(v["status"] == "MISSING" for v in report["foundations"].values()))

    @patch("tools.foundations.doctor._probe", return_value={"status": "READY"})
    @patch("tools.foundations.doctor._locate", return_value="/fake/bin")
    def test_ready_only_when_every_foundation_probes_ready(self, _locate, _probe) -> None:
        report = inspect(load_lock())
        self.assertEqual(report["status"], "READY")

    @patch("tools.foundations.doctor._probe", return_value={"status": "VERSION_MISMATCH"})
    @patch("tools.foundations.doctor._locate", return_value="/fake/bin")
    def test_version_mismatch_fails_closed(self, _locate, _probe) -> None:
        report = inspect(load_lock())
        self.assertEqual(report["status"], "NOT_READY")
        self.assertTrue(all(v["status"] == "VERSION_MISMATCH" for v in report["foundations"].values()))


if __name__ == "__main__":
    unittest.main()
