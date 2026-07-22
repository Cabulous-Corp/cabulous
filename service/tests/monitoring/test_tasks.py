"""Tests for monitoring tasks."""

from monitoring.tasks import monitoring_task


def test_monitoring_task_returns_ok() -> None:
    assert monitoring_task() == "monitoring ok"
