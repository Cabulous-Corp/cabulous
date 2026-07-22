"""Tests that verify backend quality Make targets are registered and runnable."""

import subprocess
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = SERVICE_DIR.parent


def run_make(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["make", "-C", str(cwd or SERVICE_DIR), *args],
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize(
    "target",
    ["lint", "format", "typecheck", "test-ci", "coverage", "function-length", "migration-check", "quality"],
)
def test_make_target_registered(target: str) -> None:
    result = run_make("-n", target)
    assert result.returncode == 0, (
        f"make -n {target} failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_quality_target_forwards_via_root() -> None:
    result = subprocess.run(
        ["make", "-n", "service", "quality"],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )
    assert result.returncode == 0, (
        f"make service quality failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_quality_targets_use_uv_run() -> None:
    result = run_make("-n", "quality")
    assert "uv run" in result.stdout, (
        f"quality target should use uv run:\nstdout: {result.stdout}"
    )
