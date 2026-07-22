"""Tests for scripts/quality/compare-baseline.py -- baseline ratchet comparator."""

import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Import compare-baseline.py (hyphenated name requires importlib)
_MOD_PATH = Path(__file__).resolve().parent.parent / "compare-baseline.py"
_spec = importlib.util.spec_from_file_location("compare_baseline", _MOD_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

validate_exceptions = _mod.validate_exceptions
compare_baseline = _mod.compare_baseline
cli_main = _mod.main

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _write_json(tmp: Path, name: str, data: dict) -> Path:
    p = tmp / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _empty_baseline():
    return {
        "total_duplicates": 0,
        "total_duplicated_lines": 0,
        "total_duplicated_percentage": 0.0,
        "known_duplicates": [],
        "max_new_lines_in_changed_file_pct": 3.0,
        "updated": "2026-07-22",
    }


# ---------------------------------------------------------------------------
# validate_exceptions
# ---------------------------------------------------------------------------

class TestValidateSecuritySuppressions(unittest.TestCase):
    """Security suppressions must have all required fields and be <= 90 days."""

    def test_missing_owner(self):
        suppressions = [{"rule_id": "R1", "reason": "x", "issue_url": "https://x", "expires": "2026-12-31"}]
        errors = validate_exceptions(suppressions, kind="security")
        self.assertTrue(any("owner" in e for e in errors))

    def test_missing_issue_url(self):
        suppressions = [{"rule_id": "R1", "owner": "a@b.com", "reason": "x", "expires": "2026-12-31"}]
        errors = validate_exceptions(suppressions, kind="security")
        self.assertTrue(any("issue_url" in e for e in errors))

    def test_missing_expiration(self):
        suppressions = [{"rule_id": "R1", "owner": "a@b.com", "reason": "x", "issue_url": "https://x"}]
        errors = validate_exceptions(suppressions, kind="security")
        self.assertTrue(any("expires" in e for e in errors))

    def test_valid_suppression(self):
        suppressions = [{"rule_id": "R1", "owner": "a@b.com", "reason": "x", "issue_url": "https://x", "expires": "2026-10-01"}]
        errors = validate_exceptions(suppressions, kind="security")
        self.assertEqual(errors, [])


class TestValidateOpenAPIWaivers(unittest.TestCase):
    """OpenAPI waivers must have all required fields."""

    def test_missing_api_version(self):
        waivers = [{"owner": "a", "justification": "j", "compatibility_notes": "n", "expires": "2026-12-31"}]
        errors = validate_exceptions(waivers, kind="openapi")
        self.assertTrue(any("api_version" in e for e in errors))

    def test_missing_justification(self):
        waivers = [{"api_version": "v1", "owner": "a", "compatibility_notes": "n", "expires": "2026-12-31"}]
        errors = validate_exceptions(waivers, kind="openapi")
        self.assertTrue(any("justification" in e for e in errors))

    def test_valid_waiver(self):
        waivers = [{"api_version": "v1", "owner": "a", "justification": "j", "compatibility_notes": "n", "expires": "2026-10-01"}]
        errors = validate_exceptions(waivers, kind="openapi")
        self.assertEqual(errors, [])


class TestValidateExceptionsExpiration(unittest.TestCase):
    """Expired exceptions should produce errors."""

    def test_expired_security_suppression(self):
        suppressions = [{"rule_id": "R1", "owner": "a@b.com", "reason": "x", "issue_url": "https://x", "expires": "2020-01-01"}]
        errors = validate_exceptions(suppressions, kind="security")
        self.assertTrue(any("expired" in e.lower() or "past" in e.lower() for e in errors))

    def test_security_suppression_over_90_days(self):
        suppressions = [{"rule_id": "R1", "owner": "a@b.com", "reason": "x", "issue_url": "https://x", "expires": "2027-01-01"}]
        errors = validate_exceptions(suppressions, kind="security")
        self.assertTrue(any("90 days" in e.lower() for e in errors))

    def test_expired_openapi_waiver(self):
        waivers = [{"api_version": "v1", "owner": "a", "justification": "j", "compatibility_notes": "n", "expires": "2020-01-01"}]
        errors = validate_exceptions(waivers, kind="openapi")
        self.assertTrue(any("expired" in e.lower() or "past" in e.lower() for e in errors))


# ---------------------------------------------------------------------------
# compare_baseline -- core ratchet logic
# ---------------------------------------------------------------------------

class TestNewViolationFails(unittest.TestCase):
    """New duplicates that were not in baseline should fail."""

    def test_new_total_duplicates(self):
        baseline = _empty_baseline()
        current = {
            "total_duplicates": 3,
            "total_duplicated_lines": 15,
            "total_duplicated_percentage": 1.5,
            "new_duplicates": [],
        }
        ok, msg = compare_baseline(baseline, current)
        self.assertFalse(ok)
        self.assertIn("total_duplicates", msg)

    def test_new_duplicated_lines(self):
        baseline = _empty_baseline()
        baseline["total_duplicates"] = 5
        baseline["total_duplicated_lines"] = 25
        current = {
            "total_duplicates": 5,
            "total_duplicated_lines": 30,
            "total_duplicated_percentage": 3.0,
            "new_duplicates": [],
        }
        ok, msg = compare_baseline(baseline, current)
        self.assertFalse(ok)
        self.assertIn("total_duplicated_lines", msg)

    def test_new_known_duplicate(self):
        baseline = _empty_baseline()
        baseline["known_duplicates"] = [
            {"first_file": "a.py", "second_file": "b.py", "lines": 10}
        ]
        current = {
            "total_duplicates": 1,
            "total_duplicated_lines": 10,
            "total_duplicated_percentage": 1.0,
            "new_duplicates": [
                {"first_file": "c.py", "second_file": "d.py", "lines": 15}
            ],
        }
        ok, msg = compare_baseline(baseline, current)
        self.assertFalse(ok)
        self.assertIn("new duplicate", msg.lower())


class TestExistingViolationUnchangedPasses(unittest.TestCase):
    """Same violations as baseline should pass."""

    def test_identical(self):
        baseline = {
            "total_duplicates": 3,
            "total_duplicated_lines": 15,
            "total_duplicated_percentage": 1.5,
            "known_duplicates": [
                {"first_file": "a.py", "second_file": "b.py", "lines": 10}
            ],
            "max_new_lines_in_changed_file_pct": 3.0,
        }
        current = {
            "total_duplicates": 3,
            "total_duplicated_lines": 15,
            "total_duplicated_percentage": 1.5,
            "new_duplicates": [],
        }
        ok, msg = compare_baseline(baseline, current)
        self.assertTrue(ok)
        self.assertEqual(msg, "")

    def test_total_duplicates_reduced(self):
        baseline = {
            "total_duplicates": 5,
            "total_duplicated_lines": 25,
            "total_duplicated_percentage": 2.5,
            "known_duplicates": [],
            "max_new_lines_in_changed_file_pct": 3.0,
        }
        current = {
            "total_duplicates": 3,
            "total_duplicated_lines": 15,
            "total_duplicated_percentage": 1.5,
            "new_duplicates": [],
        }
        ok, msg = compare_baseline(baseline, current)
        self.assertTrue(ok)


class TestViolationGrowthFails(unittest.TestCase):
    """Violations that grew beyond baseline should fail."""

    def test_known_duplicate_amplified(self):
        baseline = _empty_baseline()
        baseline["known_duplicates"] = [
            {"first_file": "a.py", "second_file": "b.py", "lines": 10}
        ]
        current = {
            "total_duplicates": 1,
            "total_duplicated_lines": 20,
            "total_duplicated_percentage": 2.0,
            "new_duplicates": [],
        }
        ok, msg = compare_baseline(baseline, current)
        self.assertFalse(ok)
        self.assertIn("total_duplicated_lines", msg)

    def test_percentage_over_threshold(self):
        baseline = {
            "total_duplicates": 3,
            "total_duplicated_lines": 15,
            "total_duplicated_percentage": 1.5,
            "max_new_lines_in_changed_file_pct": 0.5,
            "known_duplicates": [],
        }
        current = {
            "total_duplicates": 3,
            "total_duplicated_lines": 15,
            "total_duplicated_percentage": 1.5,
            "new_duplicates": [
                {"first_file": "x.py", "second_file": "y.py", "lines": 10, "new_lines_in_changed_file": 50}
            ],
        }
        ok, msg = compare_baseline(baseline, current)
        self.assertFalse(ok)
        self.assertIn("changed file", msg.lower())


class TestExpiredExceptionFails(unittest.TestCase):
    """Expired security suppressions or openapi waivers should fail."""

    def test_expired_suppression_blocks(self):
        errors = validate_exceptions(
            [{"rule_id": "R1", "owner": "a@b.com", "reason": "x", "issue_url": "https://x", "expires": "2020-01-01"}],
            kind="security",
        )
        self.assertTrue(len(errors) > 0)

    def test_valid_suppression_passes(self):
        errors = validate_exceptions(
            [{"rule_id": "R1", "owner": "a@b.com", "reason": "x", "issue_url": "https://x", "expires": "2026-10-01"}],
            kind="security",
        )
        self.assertEqual(errors, [])


class TestCLI(unittest.TestCase):
    """CLI end-to-end with temp files."""

    def test_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            bl = _write_json(t, "baseline.json", {
                "total_duplicates": 2,
                "total_duplicated_lines": 10,
                "total_duplicated_percentage": 1.0,
                "known_duplicates": [],
                "max_new_lines_in_changed_file_pct": 3.0,
            })
            rpt = _write_json(t, "report.json", {
                "total_duplicates": 2,
                "total_duplicated_lines": 10,
                "total_duplicated_percentage": 1.0,
                "new_duplicates": [],
            })
            rc = cli_main([str(bl), str(rpt)])
            self.assertEqual(rc, 0)

    def test_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            bl = _write_json(t, "baseline.json", _empty_baseline())
            rpt = _write_json(t, "report.json", {
                "total_duplicates": 5,
                "total_duplicated_lines": 25,
                "total_duplicated_percentage": 2.5,
                "new_duplicates": [],
            })
            rc = cli_main([str(bl), str(rpt)])
            self.assertEqual(rc, 1)

    def test_with_exceptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            bl = _write_json(t, "baseline.json", _empty_baseline())
            rpt = _write_json(t, "report.json", {
                "total_duplicates": 5,
                "total_duplicated_lines": 25,
                "total_duplicated_percentage": 2.5,
                "new_duplicates": [],
            })
            exc = _write_json(t, "suppressions.yaml", "")  # empty file
            rc = cli_main([str(bl), str(rpt), "--security-suppressions", str(exc)])
            # empty file = no exceptions, still fails
            self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
