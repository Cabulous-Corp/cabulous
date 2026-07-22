"""Tests for OpenAPI schema export and contract-check tooling."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = SERVICE_DIR.parent
EXPORT_SCRIPT = SERVICE_DIR / "scripts" / "export_openapi.py"
BASELINE_PATH = ROOT_DIR / "quality" / "openapi" / "baseline.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_export() -> str:
    """Run the export script and return the JSON output."""
    result = subprocess.run(
        [sys.executable, str(EXPORT_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=SERVICE_DIR,
        env={**__import__("os").environ, "DJANGO_SETTINGS_MODULE": "cabulous.settings"},
    )
    assert result.returncode == 0, (
        f"export_openapi.py failed (rc={result.returncode}):\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    return result.stdout


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportScriptExists:
    def test_export_script_is_a_file(self):
        assert EXPORT_SCRIPT.is_file(), f"Missing {EXPORT_SCRIPT}"


class TestOpenAPIExport:
    def test_produces_valid_json(self):
        output = run_export()
        data = json.loads(output)
        assert isinstance(data, dict), "Output must be a JSON object"

    def test_has_openapi_version_key(self):
        data = json.loads(run_export())
        assert "openapi" in data, "Schema must contain 'openapi' version key"

    def test_openapi_version_is_3x(self):
        data = json.loads(run_export())
        version = data["openapi"]
        assert version.startswith("3."), f"Expected OpenAPI 3.x, got {version}"

    def test_has_info_block(self):
        data = json.loads(run_export())
        assert "info" in data, "Schema must contain 'info' block"
        info = data["info"]
        assert "title" in info and "version" in info, "info must have title and version"

    def test_has_paths(self):
        data = json.loads(run_export())
        assert "paths" in data, "Schema must contain 'paths'"

    def test_deterministic_output(self):
        """Running the exporter twice must produce identical output."""
        first = run_export()
        second = run_export()
        assert first == second, "Export is not deterministic: outputs differ"


class TestBaselineExists:
    def test_baseline_file_exists(self):
        assert BASELINE_PATH.is_file(), f"Missing baseline {BASELINE_PATH}"

    def test_baseline_is_valid_json(self):
        data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        assert "openapi" in data, "Baseline must contain 'openapi' key"
