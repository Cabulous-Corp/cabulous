"""Tests that verify backend quality Task targets are registered with correct commands."""

import tempfile
from pathlib import Path

import pytest
import yaml

SERVICE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = SERVICE_DIR.parent
TASKFILE = SERVICE_DIR / "Taskfile.service.yml"


def _load_tasks() -> dict:
    """Load and return the tasks dict from Taskfile.service.yml."""
    with TASKFILE.open() as f:
        data = yaml.safe_load(f)
    return data.get("tasks", {})


TASKS = _load_tasks()


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
    assert target in TASKS, f"Task '{target}' not found in {TASKFILE.name}"


def test_quality_target_forwards_via_root() -> None:
    """The root Taskfile includes service:Taskfile.service.yml with namespace."""
    root_taskfile = ROOT_DIR / "Taskfile.yml"
    assert root_taskfile.exists(), f"Root Taskfile not found: {root_taskfile}"
    with root_taskfile.open() as f:
        data = yaml.safe_load(f)
    includes = data.get("includes", {})
    assert "service" in includes, f"Root Taskfile does not include service namespace:\n{includes}"


def test_quality_targets_use_docker_compose() -> None:
    """Quality targets that run inside Docker should use the Docker Compose pattern."""
    quality_task = TASKS["quality"]
    # quality uses deps — check each dep task
    deps = quality_task.get("deps", [])
    local_allowed = {"contract-check", "migration-check"}
    compose_indicators = ("{{.DEV_COMPOSE}}", "{{.PROD_COMPOSE}}", "docker compose")
    for dep in deps:
        if dep in local_allowed:
            continue
        task_data = TASKS[dep]
        cmd = task_data.get("cmd", "")
        cmds = task_data.get("cmds", [])
        all_cmds = ([cmd] if cmd else []) + cmds
        for c in all_cmds:
            if isinstance(c, dict):
                c = c.get("cmd", "")
            if not c or "check-openapi.sh" in c or "echo" in c:
                continue
            assert any(ind in c for ind in compose_indicators), (
                f"Task '{dep}' should use Docker Compose, got:\n{c}"
            )


def test_quality_targets_include_duplication() -> None:
    """The quality aggregate should include the duplication check."""
    quality_task = TASKS["quality"]
    deps = quality_task.get("deps", [])
    assert "duplication" in deps, f"quality deps should include 'duplication':\n{deps}"


def test_function_length_selects_mfl000() -> None:
    """The function-length target should use --select=C901,MFL000."""
    cmd = TASKS["function-length"].get("cmd", "")
    assert "MFL000" in cmd, f"function-length cmd should include MFL000:\n{cmd}"


def test_coverage_enables_branch() -> None:
    """The coverage target should include --branch."""
    cmd = TASKS["coverage"].get("cmd", "")
    assert "--branch" in cmd, f"coverage cmd should include --branch:\n{cmd}"


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
