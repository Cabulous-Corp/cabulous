"""Tests that verify backend quality Task targets are registered and runnable."""

import subprocess
import tempfile
from pathlib import Path

import pytest

SERVICE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = SERVICE_DIR.parent


def run_task(*args: str) -> subprocess.CompletedProcess:
    """Run a task command from the project root (uses root Taskfile with namespace includes)."""
    return subprocess.run(
        ["task", *args],
        capture_output=True,
        text=True,
        cwd=ROOT_DIR,
    )


@pytest.mark.parametrize(
    "target",
    [
        "lint",
        "format",
        "typecheck",
        "test-ci",
        "coverage",
        "function-length",
        "duplication",
        "migration-check",
        "contract-check",
        "quality",
    ],
)
def test_task_target_registered(target: str) -> None:
    result = run_task("-n", f"service:{target}")
    assert result.returncode == 0, (
        f"task -n service:{target} failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_quality_target_forwards_via_root() -> None:
    result = run_task("-n", "service:quality")
    assert result.returncode == 0, (
        f"task -n service:quality failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_quality_targets_use_docker_compose() -> None:
    """Quality targets that run inside Docker should use the Docker Compose pattern."""
    result = run_task("-n", "service:quality")
    output = result.stdout
    assert "docker compose" in output and "run --rm web uv run" in output, (
        f"quality target should use Docker Compose pattern:\nstdout: {output}"
    )
    # Allow-listed local-only targets (no Docker volume access to repo root)
    local_allowed = {"contract-check", "migration-check"}
    lines = [
        ln.strip()
        for ln in output.splitlines()
        if ln.strip()
        and not ln.strip().startswith("task")
        and not ln.strip().startswith("echo")
        and "Entering" not in ln
        and "Leaving" not in ln
    ]
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
    result = run_task("-n", "service:quality")
    assert "jscpd" in result.stdout, (
        f"quality target should include duplication (jscpd):\nstdout: {result.stdout}"
    )


def test_function_length_selects_mfl000() -> None:
    """The function-length target should use --select=C901,MFL000."""
    result = run_task("-n", "service:function-length")
    assert "MFL000" in result.stdout, (
        f"function-length target should include MFL000:\nstdout: {result.stdout}"
    )


def test_coverage_enables_branch() -> None:
    """The coverage target should include --branch."""
    result = run_task("-n", "service:coverage")
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
