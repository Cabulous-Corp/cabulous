#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# check-openapi.sh — Contract check: compare current OpenAPI schema against
# baseline using @openapi-contrib/openapi-diff for semantic breaking-change
# detection. Breaking changes require an active waiver in openapi-waivers.yaml.
# ---------------------------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_DIR="$ROOT_DIR/service"
BASELINE="$ROOT_DIR/quality/openapi/baseline.json"
WAIVERS="$ROOT_DIR/quality/exceptions/openapi-waivers.yaml"

cd "$SERVICE_DIR"

# 1. Export current schema to temp file
CURRENT="$(mktemp)"
trap 'rm -f "$CURRENT"' EXIT
uv run python scripts/export_openapi.py > "$CURRENT"

# 2. Check for breaking changes using openapi-diff (semantic, not byte-level)
if npx --yes @openapi-contrib/openapi-diff "$BASELINE" "$CURRENT" --fail-on-incompatible > /dev/null 2>&1; then
    echo "OK contract: no breaking changes detected."
    exit 0
fi

echo "INFO: breaking changes detected."

# 3. Check for active waivers
if [ ! -f "$WAIVERS" ]; then
    echo "FAIL contract: breaking change detected but no waivers file exists." >&2
    exit 1
fi

ACTIVE=$(uv run python -c "
import yaml
from datetime import date
with open('$WAIVERS') as f:
    data = yaml.safe_load(f) or []
count = sum(1 for e in data if e.get('expires') and date.fromisoformat(str(e['expires'])) >= date.today())
print(count)
")

if [ "$ACTIVE" -ge 1 ]; then
    echo "OK contract: $ACTIVE active waiver(s) accept the breaking change."
    exit 0
fi

echo "FAIL contract: breaking change detected without an active waiver." >&2
exit 1
