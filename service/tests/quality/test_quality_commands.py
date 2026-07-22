"""Tests that verify backend quality Make targets are registered and runnable."""

import subprocess
import tempfile
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
    ["lint", "format", "typecheck", "test-ci", "coverage", "function-length", "duplication", "migration-check", "contract-check", "quality"],
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


def test_quality_targets_use_docker_compose() -> None:
    """Quality targets that run inside Docker should use the Docker Compose pattern."""
    result = run_make("-n", "quality")
    output = result.stdout
    assert "docker compose" in output and "run --rm web uv run" in output, (
        f"quality target should use Docker Compose pattern:\nstdout: {output}"
    )
    # Allow-listed local-only targets (no Docker volume access to repo root)
    local_allowed = {"contract-check", "migration-check"}
    lines = [l.strip() for l in output.splitlines() if l.strip() and not l.strip().startswith("make") and not l.strip().startswith("echo") and "Entering" not in l and "Leaving" not in l]
    for line in lines:
        if "echo" in line:
            continue
        if any(loc in line for loc in local_allowed) or "check-openapi.sh" in line:
            continue
        assert "docker compose" in line, (
            f"Target command should use Docker Compose, got bare command:\n{line}"
        )


def test_quality_targets_include_duplication() -> None:
    """The quality aggregate should run the duplication check."""
    result = run_make("-n", "quality")
    assert "jscpd" in result.stdout, (
        f"quality target should include duplication (jscpd):\nstdout: {result.stdout}"
    )


def test_function_length_selects_mfl000() -> None:
    """The function-length target should use --select=C901,MFL000."""
    result = run_make("-n", "function-length")
    assert "MFL000" in result.stdout, (
        f"function-length target should include MFL000:\nstdout: {result.stdout}"
    )


def test_coverage_enables_branch() -> None:
    """The coverage target should include --branch."""
    result = run_make("-n", "coverage")
    assert "--branch" in result.stdout, (
        f"coverage target should include --branch:\nstdout: {result.stdout}"
    )


def test_ruff_lints_clean_python_file() -> None:
    """Integration test: ruff lint actually runs on a valid Python file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        clean_file = tmpdir_path / "clean.py"
        clean_file.write_text('"""Clean module."""\n\nx = 1\n')
        result = subprocess.run(
            ["uv", "run", "ruff", "check", str(clean_file)],
            capture_output=True,
            text=True,
            cwd=SERVICE_DIR,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"ruff check failed on clean file:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
