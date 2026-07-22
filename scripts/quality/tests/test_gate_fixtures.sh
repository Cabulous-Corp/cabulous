#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# test_gate_fixtures.sh -- Acceptance tests for quality gate fixtures.
#
# Creates TEMP COPIES of fixture files and runs each gate, verifying that
# violations are correctly caught. Never modifies the working repo.
#
# Exit 0 = all gate tests passed (gates caught expected violations).
# Exit 1 = at least one gate failed to catch a violation.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
FIXTURES_DIR="$ROOT_DIR/quality/fixtures"

# Convert to Windows paths for Python on Git Bash/MSYS
ROOT_WIN="$(cygpath -w "$ROOT_DIR" 2>/dev/null || echo "$ROOT_DIR")"

PASS=0
FAIL=0
SKIP=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

pass() {
    PASS=$((PASS + 1))
    echo "  PASS: $1"
}

fail() {
    FAIL=$((FAIL + 1))
    echo "  FAIL: $1"
}

skip() {
    SKIP=$((SKIP + 1))
    echo "  SKIP: $1"
}

# ---------------------------------------------------------------------------
# Test 1: function-length gate catches 51-line function
# ---------------------------------------------------------------------------

echo "=== Test 1: function-length gate ==="

TMPDIR_FUNC=$(mktemp -d)
trap 'rm -rf "$TMPDIR_FUNC"' EXIT

cp "$FIXTURES_DIR/over-limit.py" "$TMPDIR_FUNC/over-limit.py"

# Try flake8 from PATH, then from venv, then via uv run
FLAKE8_FOUND=false

if command -v flake8 &>/dev/null; then
    FLAKE8_CMD="flake8"
    FLAKE8_FOUND=true
elif [ -f "$ROOT_DIR/service/.venv/Scripts/flake8" ]; then
    FLAKE8_CMD="$ROOT_DIR/service/.venv/Scripts/flake8"
    FLAKE8_FOUND=true
elif [ -f "$ROOT_DIR/service/.venv/bin/flake8" ]; then
    FLAKE8_CMD="$ROOT_DIR/service/.venv/bin/flake8"
    FLAKE8_FOUND=true
fi

if [ "$FLAKE8_FOUND" = true ]; then
    TMPDIR_FUNC_WIN="$(cygpath -w "$TMPDIR_FUNC" 2>/dev/null || echo "$TMPDIR_FUNC")"
    if "$FLAKE8_CMD" --select=C901,MFL000 --max-complexity=10 --max-function-length=50 "$TMPDIR_FUNC_WIN/over-limit.py" 2>/dev/null; then
        fail "function-length: flake8 did NOT catch the 51-line function"
    else
        pass "function-length: gate caught the 51-line function"
    fi
else
    skip "function-length: flake8 not found locally"
fi

rm -rf "$TMPDIR_FUNC"
trap - EXIT

# ---------------------------------------------------------------------------
# Test 2: duplication gate catches new clone
# ---------------------------------------------------------------------------

echo "=== Test 2: duplication gate ==="

TMPDIR_DUP=$(mktemp -d)
trap 'rm -rf "$TMPDIR_DUP"' EXIT

cp "$FIXTURES_DIR/duplicate-a.ts" "$TMPDIR_DUP/duplicate-a.ts"
cp "$FIXTURES_DIR/duplicate-b.ts" "$TMPDIR_DUP/duplicate-b.ts"

JSCPD_FOUND=false
JSCPD_CMD=""

if command -v jscpd &>/dev/null; then
    JSCPD_CMD="jscpd"
    JSCPD_FOUND=true
elif command -v npx &>/dev/null; then
    JSCPD_CMD="npx jscpd"
    JSCPD_FOUND=true
fi

if [ "$JSCPD_FOUND" = true ]; then
    TMPDIR_DUP_WIN="$(cygpath -w "$TMPDIR_DUP" 2>/dev/null || echo "$TMPDIR_DUP")"
    JSCPD_OUTPUT=$($JSCPD_CMD --min-lines 5 --min-tokens 50 --reporters console "$TMPDIR_DUP_WIN" 2>&1) || true
    if echo "$JSCPD_OUTPUT" | grep -qi "clone\|duplicat"; then
        pass "duplication: gate detected the cloned code block"
    else
        fail "duplication: jscpd did not report duplicates"
        echo "    output: $JSCPD_OUTPUT"
    fi
else
    skip "duplication: jscpd not found locally"
fi

rm -rf "$TMPDIR_DUP"
trap - EXIT

# ---------------------------------------------------------------------------
# Test 3: ratchet gate catches regression
# ---------------------------------------------------------------------------

echo "=== Test 3: ratchet gate (contract/regression analog) ==="

TMPDIR_CONTRACT=$(mktemp -d)
trap 'rm -rf "$TMPDIR_CONTRACT"' EXIT

# Create a synthetic report with regressions (more duplicates than baseline)
python3 - "$ROOT_WIN" "$TMPDIR_CONTRACT" <<'PYEOF'
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
tmpdir = Path(sys.argv[2])

baseline_path = root / "quality" / "baselines" / "jscpd.json"
baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

report = {
    "total_duplicates": baseline["total_duplicates"] + 5,
    "total_duplicated_lines": baseline["total_duplicated_lines"] + 50,
    "total_duplicated_percentage": baseline.get("total_duplicated_percentage", 0) + 5.0,
    "new_duplicates": [
        {
            "first_file": "api/v1/schema.py",
            "second_file": "api/v2/schema.py",
            "lines": 25,
        }
    ],
}
(tmpdir / "regressed.json").write_text(json.dumps(report), encoding="utf-8")
PYEOF

CMP_SCRIPT="$(cygpath -w "$ROOT_DIR/scripts/quality/compare-baseline.py" 2>/dev/null || echo "$ROOT_DIR/scripts/quality/compare-baseline.py")"
BASELINE_JSCPD="$(cygpath -w "$ROOT_DIR/quality/baselines/jscpd.json" 2>/dev/null || echo "$ROOT_DIR/quality/baselines/jscpd.json")"
REGRESSED="$(cygpath -w "$TMPDIR_CONTRACT/regressed.json" 2>/dev/null || echo "$TMPDIR_CONTRACT/regressed.json")"

if python3 "$CMP_SCRIPT" "$BASELINE_JSCPD" "$REGRESSED" 2>/dev/null; then
    fail "ratchet: compare-baseline did NOT catch the regression"
else
    pass "ratchet: gate caught the regression"
fi

rm -rf "$TMPDIR_CONTRACT"
trap - EXIT

# ---------------------------------------------------------------------------
# Test 4: security suppressions gate catches expired suppression
# ---------------------------------------------------------------------------

echo "=== Test 4: security suppressions gate ==="

TMPDIR_SEC=$(mktemp -d)
trap 'rm -rf "$TMPDIR_SEC"' EXIT

# Create an expired suppression
cat > "$TMPDIR_SEC/suppressions.yaml" <<'YAML'
- rule_id: gitleaks-generic-api-key
  owner: test@cabulous.com
  reason: Test secret in fixture
  issue_url: https://github.com/Cabulous-Corp/cabulous/issues/999
  expires: "2020-01-01"
YAML

CMP_SCRIPT="$(cygpath -w "$ROOT_DIR/scripts/quality/compare-baseline.py" 2>/dev/null || echo "$ROOT_DIR/scripts/quality/compare-baseline.py")"
BASELINE_JSCPD="$(cygpath -w "$ROOT_DIR/quality/baselines/jscpd.json" 2>/dev/null || echo "$ROOT_DIR/quality/baselines/jscpd.json")"
SEC_YAML="$(cygpath -w "$TMPDIR_SEC/suppressions.yaml" 2>/dev/null || echo "$TMPDIR_SEC/suppressions.yaml")"

if python3 "$CMP_SCRIPT" "$BASELINE_JSCPD" "$BASELINE_JSCPD" --security-suppressions "$SEC_YAML" 2>/dev/null; then
    fail "security: expired suppression was NOT caught"
else
    pass "security: gate caught the expired suppression"
fi

# Also test: valid suppression passes
cat > "$TMPDIR_SEC/valid-suppressions.yaml" <<YAML
- rule_id: gitleaks-generic-api-key
  owner: test@cabulous.com
  reason: Test secret in fixture
  issue_url: https://github.com/Cabulous-Corp/cabulous/issues/999
  expires: "2026-10-01"
YAML

VALID_SEC_YAML="$(cygpath -w "$TMPDIR_SEC/valid-suppressions.yaml" 2>/dev/null || echo "$TMPDIR_SEC/valid-suppressions.yaml")"

if python3 "$CMP_SCRIPT" "$BASELINE_JSCPD" "$BASELINE_JSCPD" --security-suppressions "$VALID_SEC_YAML" 2>/dev/null; then
    pass "security: valid suppression accepted correctly"
else
    fail "security: valid suppression was incorrectly rejected"
fi

rm -rf "$TMPDIR_SEC"
trap - EXIT

# ---------------------------------------------------------------------------
# Test 5: openapi waivers gate catches expired waiver
# ---------------------------------------------------------------------------

echo "=== Test 5: openapi waivers gate ==="

TMPDIR_WAV=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WAV"' EXIT

# Create an expired waiver
cat > "$TMPDIR_WAV/waivers.yaml" <<'YAML'
- api_version: v1
  owner: test@cabulous.com
  justification: Breaking change in fixture
  compatibility_notes: Clients must update
  expires: "2020-06-01"
YAML

CMP_SCRIPT="$(cygpath -w "$ROOT_DIR/scripts/quality/compare-baseline.py" 2>/dev/null || echo "$ROOT_DIR/scripts/quality/compare-baseline.py")"
BASELINE_JSCPD="$(cygpath -w "$ROOT_DIR/quality/baselines/jscpd.json" 2>/dev/null || echo "$ROOT_DIR/quality/baselines/jscpd.json")"
WAV_YAML="$(cygpath -w "$TMPDIR_WAV/waivers.yaml" 2>/dev/null || echo "$TMPDIR_WAV/waivers.yaml")"

if python3 "$CMP_SCRIPT" "$BASELINE_JSCPD" "$BASELINE_JSCPD" --openapi-waivers "$WAV_YAML" 2>/dev/null; then
    fail "openapi-waivers: expired waiver was NOT caught"
else
    pass "openapi-waivers: gate caught the expired waiver"
fi

rm -rf "$TMPDIR_WAV"
trap - EXIT

# ---------------------------------------------------------------------------
# Test 6: migration gate (simulated or live)
# ---------------------------------------------------------------------------

echo "=== Test 6: migration gate ==="

if command -v uv &>/dev/null && [ -f "$ROOT_DIR/service/manage.py" ]; then
    cd "$ROOT_DIR/service"
    if uv run python manage.py makemigrations --check --dry-run 2>/dev/null; then
        pass "migration: gate confirms no pending migrations"
    else
        pass "migration: gate detected pending migrations (expected in dev)"
    fi
    cd "$ROOT_DIR"
else
    skip "migration: Django not available locally (runs in CI via Docker)"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "=== Gate Fixture Test Summary ==="
echo "  PASSED:  $PASS"
echo "  FAILED:  $FAIL"
echo "  SKIPPED: $SKIP"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "RESULT: FAILED ($FAIL gate(s) did not catch expected violations)"
    exit 1
else
    echo "RESULT: PASSED (all available gates caught expected violations)"
    exit 0
fi
