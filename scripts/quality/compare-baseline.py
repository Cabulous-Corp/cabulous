#!/usr/bin/env python3
"""Compare jscpd JSON report against committed baseline.

Ratchet: total duplicates, duplicated lines and percentage must not grow.
New duplicates and amplified known duplicates are also blocked.
Optionally validates security-suppressions and openapi-waivers YAML.

Exit 0 = pass, exit 1 = regressions found or invalid exceptions.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> Any:
    """Load YAML file; returns empty list on missing/empty file."""
    import yaml  # PyYAML -- already a project dependency
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    return yaml.safe_load(text) or []


def _parse_date(value: str) -> date:
    """Parse a date string in common ISO formats (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)."""
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {value}")


# ---------------------------------------------------------------------------
# Exception validators
# ---------------------------------------------------------------------------

def validate_exceptions(
    entries: list[dict[str, Any]],
    *,
    kind: str = "security",
) -> list[str]:
    """Return list of error strings for invalid/expired entries.

    kind="security"  -- rule_id, owner, reason, issue_url, expires (<=90 days)
    kind="openapi"   -- api_version, owner, justification,
                        compatibility_notes, expires
    """
    today = date.today()
    errors: list[str] = []

    if kind == "security":
        required = ("rule_id", "owner", "reason", "issue_url", "expires")
        max_days = 90
    elif kind == "openapi":
        required = ("api_version", "owner", "justification",
                    "compatibility_notes", "expires")
        max_days = None
    else:
        raise ValueError(f"Unknown exception kind: {kind}")

    for i, entry in enumerate(entries):
        prefix = f"[{kind} #{i + 1}]"

        # Missing required fields
        for field in required:
            if field not in entry or not entry[field]:
                errors.append(f"{prefix} missing required field: {field}")

        # Date validation
        if "expires" in entry and entry["expires"]:
            try:
                exp = _parse_date(str(entry["expires"]))
            except ValueError as exc:
                errors.append(f"{prefix} invalid expires date: {exc}")
                continue

            if exp < today:
                errors.append(f"{prefix} expired on {exp}")
            elif max_days is not None:
                max_allowed = today + timedelta(days=max_days)
                if exp > max_allowed:
                    errors.append(
                        f"{prefix} expires {exp}; maximum allowed is {max_days} days from today ({max_allowed})"
                    )

    return errors


# ---------------------------------------------------------------------------
# Baseline comparison
# ---------------------------------------------------------------------------

def compare_baseline(
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> tuple[bool, str]:
    """Compare current jscpd report against baseline.

    Returns (pass, message).  pass=True means ratchet held.
    """
    violations: list[str] = []

    b_total = baseline.get("total_duplicates", 0)
    c_total = current.get("total_duplicates", 0)
    if c_total > b_total:
        violations.append(
            f"total_duplicates grew: {b_total} -> {c_total}"
        )

    b_lines = baseline.get("total_duplicated_lines", 0)
    c_lines = current.get("total_duplicated_lines", 0)
    if c_lines > b_lines:
        violations.append(
            f"total_duplicated_lines grew: {b_lines} -> {c_lines}"
        )

    b_known = baseline.get("known_duplicates", [])

    # New duplicates in the changed file
    max_pct = baseline.get("max_new_lines_in_changed_file_pct", 3.0)
    for dup in current.get("new_duplicates", []):
        # Completely new clone not in baseline
        if b_known:
            b_files = {
                (d.get("first_file"), d.get("second_file"))
                for d in b_known
            }
            pair = (dup.get("first_file"), dup.get("second_file"))
            rev_pair = (dup.get("second_file"), dup.get("first_file"))
            if pair not in b_files and rev_pair not in b_files:
                violations.append(
                    f"new duplicate: {dup.get('first_file')} <-> {dup.get('second_file')} "
                    f"({dup.get('lines', '?')} lines)"
                )
        else:
            violations.append(
                f"new duplicate: {dup.get('first_file')} <-> {dup.get('second_file')} "
                f"({dup.get('lines', '?')} lines)"
            )

        # Exceeds changed-file threshold
        new_lines = dup.get("new_lines_in_changed_file")
        if new_lines is not None and max_pct:
            threshold = dup.get("total_lines_in_file", 0) * max_pct / 100
            if new_lines > threshold:
                violations.append(
                    f"new duplicate in changed file exceeds {max_pct}% threshold: "
                    f"{new_lines} new lines in {dup.get('first_file')}"
                )

    if violations:
        return False, "; ".join(violations)
    return True, ""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """CLI entry point.  Returns exit code."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compare jscpd report against baseline; validate exceptions."
    )
    parser.add_argument("baseline", help="Path to baseline JSON")
    parser.add_argument("report", help="Path to current jscpd report JSON")
    parser.add_argument(
        "--security-suppressions",
        dest="security_suppressions",
        help="Path to security-suppressions.yaml",
    )
    parser.add_argument(
        "--openapi-waivers",
        dest="openapi_waivers",
        help="Path to openapi-waivers.yaml",
    )
    args = parser.parse_args(argv)

    baseline = _load_json(Path(args.baseline))
    current = _load_json(Path(args.report))

    all_ok = True

    # Ratchet check
    ok, msg = compare_baseline(baseline, current)
    if not ok:
        print(f"FAIL ratchet: {msg}", file=sys.stderr)
        all_ok = False
    else:
        print("OK ratchet: no regressions")

    # Security suppressions
    if args.security_suppressions:
        sp = Path(args.security_suppressions)
        if sp.exists():
            entries = _load_yaml(sp)
            errors = validate_exceptions(entries, kind="security")
            for e in errors:
                print(f"FAIL security: {e}", file=sys.stderr)
            if errors:
                all_ok = False
            else:
                print("OK security suppressions: all valid")

    # OpenAPI waivers
    if args.openapi_waivers:
        wp = Path(args.openapi_waivers)
        if wp.exists():
            entries = _load_yaml(wp)
            errors = validate_exceptions(entries, kind="openapi")
            for e in errors:
                print(f"FAIL openapi: {e}", file=sys.stderr)
            if errors:
                all_ok = False
            else:
                print("OK openapi waivers: all valid")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
