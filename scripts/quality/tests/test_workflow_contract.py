"""Structural tests for GitHub Actions quality workflow YAML files.

These tests validate the CONTRACT between workflow files and project policy:
- Blocking jobs MUST NOT use continue-on-error
- Observational jobs (Semgrep, E2E) MUST use continue-on-error: true
- Heavy jobs (CodeQL, Scorecard, mutation) MUST use schedule + workflow_dispatch
- All jobs MUST publish artifacts (test reports, coverage, etc.)
"""

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml(filename: str) -> dict:
    path = WORKFLOWS_DIR / filename
    assert path.exists(), f"Missing workflow file: {path}"
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _job_names(workflow: dict) -> list[str]:
    return list(workflow.get("jobs", {}).keys())


def _get_jobs(workflow: dict) -> dict:
    return workflow.get("jobs", {})


def _triggers(workflow: dict) -> dict:
    return workflow.get("on", workflow.get(True, {}))


def _has_continue_on_error(job: dict) -> bool:
    return job.get("continue-on-error", False)


def _has_artifact_upload(job: dict) -> bool:
    for step in job.get("steps", []):
        if step.get("uses", "").startswith("actions/upload-artifact"):
            return True
    return False


# ---------------------------------------------------------------------------
# Categories (defined by naming convention in workflow YAML)
# ---------------------------------------------------------------------------

BLOCKING_JOBS = [
    "backend-lint",
    "backend-typecheck",
    "backend-test",
    "backend-duplication",
    "backend-contract",
    "backend-migration",
    "frontend-lint",
    "frontend-typecheck",
    "frontend-build",
    "frontend-test",
    "gitleaks",
    "dependency-review",
]

OBSERVATIONAL_JOBS = [
    "semgrep",
]

HEAVY_JOBS = [
    "codeql",
    "scorecard",
]


# ---------------------------------------------------------------------------
# Tests: quality.yml (main CI)
# ---------------------------------------------------------------------------

class TestQualityYAMLExists(unittest.TestCase):
    def test_file_exists(self):
        self.assertTrue(
            (WORKFLOWS_DIR / "quality.yml").exists(),
            "quality.yml must exist in .github/workflows/",
        )


class TestQualityTriggers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = _load_yaml("quality.yml")

    def test_runs_on_pull_request(self):
        triggers = _triggers(self.wf)
        self.assertIn("pull_request", triggers)

    def test_runs_on_push_develop_and_main(self):
        triggers = _triggers(self.wf)
        self.assertIn("push", triggers)
        branches = triggers["push"].get("branches", [])
        self.assertIn("develop", branches)
        self.assertIn("main", branches)


class TestQualityBlockingJobsNoContinueOnError(unittest.TestCase):
    """Blocking jobs MUST NOT use continue-on-error."""

    @classmethod
    def setUpClass(cls):
        cls.wf = _load_yaml("quality.yml")
        cls.jobs = _get_jobs(cls.wf)

    def test_blocking_jobs_not_tolerate_errors(self):
        for job_name in BLOCKING_JOBS:
            with self.subTest(job=job_name):
                if job_name not in self.jobs:
                    self.skipTest(f"Job {job_name} not in quality.yml")
                self.assertFalse(
                    _has_continue_on_error(self.jobs[job_name]),
                    f"Blocking job '{job_name}' must NOT use continue-on-error",
                )


class TestQualityObservationalJobsTolerateErrors(unittest.TestCase):
    """Observational jobs MUST use continue-on-error: true."""

    @classmethod
    def setUpClass(cls):
        cls.wf = _load_yaml("quality.yml")
        cls.jobs = _get_jobs(cls.wf)

    def test_observational_jobs_tolerate_errors(self):
        for job_name in OBSERVATIONAL_JOBS:
            with self.subTest(job=job_name):
                if job_name not in self.jobs:
                    self.skipTest(f"Job {job_name} not in quality.yml")
                self.assertTrue(
                    _has_continue_on_error(self.jobs[job_name]),
                    f"Observational job '{job_name}' MUST use continue-on-error: true",
                )


class TestQualityAllJobsPublishArtifacts(unittest.TestCase):
    """All jobs MUST upload artifacts (JUnit, coverage, JSON)."""

    @classmethod
    def setUpClass(cls):
        cls.wf = _load_yaml("quality.yml")
        cls.jobs = _get_jobs(cls.wf)

    def test_all_jobs_have_artifact_upload(self):
        for job_name in self.jobs:
            with self.subTest(job=job_name):
                self.assertTrue(
                    _has_artifact_upload(self.jobs[job_name]),
                    f"Job '{job_name}' must publish artifacts via actions/upload-artifact",
                )


class TestQualityJobCount(unittest.TestCase):
    """Quality.yml should contain all expected blocking + observational jobs."""

    @classmethod
    def setUpClass(cls):
        cls.wf = _load_yaml("quality.yml")
        cls.names = set(_job_names(cls.wf))

    def test_has_all_blocking_jobs(self):
        for job in BLOCKING_JOBS:
            with self.subTest(job=job):
                self.assertIn(job, self.names, f"Missing blocking job: {job}")

    def test_has_all_observational_jobs(self):
        for job in OBSERVATIONAL_JOBS:
            with self.subTest(job=job):
                self.assertIn(job, self.names, f"Missing observational job: {job}")

    def test_no_heavy_jobs_in_quality_yml(self):
        for job in HEAVY_JOBS:
            self.assertNotIn(job, self.names, f"Heavy job '{job}' should NOT be in quality.yml")


# ---------------------------------------------------------------------------
# Tests: heavy/scheduled workflows
# ---------------------------------------------------------------------------

class TestHeavyWorkflowsExist(unittest.TestCase):
    def test_codeql_workflow_exists(self):
        self.assertTrue(
            (WORKFLOWS_DIR / "codeql.yml").exists(),
            "codeql.yml must exist in .github/workflows/",
        )

    def test_scorecard_workflow_exists(self):
        self.assertTrue(
            (WORKFLOWS_DIR / "scorecard.yml").exists(),
            "scorecard.yml must exist in .github/workflows/",
        )


class TestCodeqlScheduleOnly(unittest.TestCase):
    """CodeQL must only trigger on schedule + workflow_dispatch."""

    @classmethod
    def setUpClass(cls):
        cls.wf = _load_yaml("codeql.yml")
        cls.triggers = _triggers(cls.wf)

    def test_has_schedule_trigger(self):
        self.assertIn("schedule", self.triggers, "CodeQL must have schedule trigger")

    def test_has_workflow_dispatch_trigger(self):
        self.assertIn("workflow_dispatch", self.triggers, "CodeQL must have workflow_dispatch trigger")

    def test_no_pull_request_trigger(self):
        self.assertNotIn("pull_request", self.triggers, "CodeQL must NOT trigger on pull_request")

    def test_no_push_trigger(self):
        self.assertNotIn("push", self.triggers, "CodeQL must NOT trigger on push")


class TestScorecardScheduleOnly(unittest.TestCase):
    """Scorecard must only trigger on schedule + workflow_dispatch."""

    @classmethod
    def setUpClass(cls):
        cls.wf = _load_yaml("scorecard.yml")
        cls.triggers = _triggers(cls.wf)

    def test_has_schedule_trigger(self):
        self.assertIn("schedule", self.triggers, "Scorecard must have schedule trigger")

    def test_has_workflow_dispatch_trigger(self):
        self.assertIn("workflow_dispatch", self.triggers, "Scorecard must have workflow_dispatch trigger")

    def test_no_pull_request_trigger(self):
        self.assertNotIn("pull_request", self.triggers, "Scorecard must NOT trigger on pull_request")


class TestHeavyJobsPublishArtifacts(unittest.TestCase):
    """Heavy job workflows must publish artifacts."""

    @classmethod
    def setUpClass(cls):
        cls.codeql = _load_yaml("codeql.yml")
        cls.scorecard = _load_yaml("scorecard.yml")

    def test_codeql_uploads_artifacts(self):
        jobs = _get_jobs(self.codeql)
        has_upload = any(
            _has_artifact_upload(j) for j in jobs.values()
        )
        self.assertTrue(has_upload, "CodeQL workflow must upload artifacts")

    def test_scorecard_uploads_artifacts(self):
        jobs = _get_jobs(self.scorecard)
        has_upload = any(
            _has_artifact_upload(j) for j in jobs.values()
        )
        self.assertTrue(has_upload, "Scorecard workflow must upload artifacts")


# ---------------------------------------------------------------------------
# Tests: scheduled quality workflow
# ---------------------------------------------------------------------------

class TestScheduledWorkflow(unittest.TestCase):
    """quality-scheduled.yml must trigger only on schedule + workflow_dispatch."""

    @classmethod
    def setUpClass(cls):
        cls.path = WORKFLOWS_DIR / "quality-scheduled.yml"

    def test_file_exists(self):
        self.assertTrue(self.path.exists(), "quality-scheduled.yml must exist")

    def test_schedule_and_dispatch_only(self):
        wf = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        triggers = _triggers(wf)
        self.assertIn("schedule", triggers, "Must have schedule trigger")
        self.assertIn("workflow_dispatch", triggers, "Must have workflow_dispatch trigger")
        self.assertNotIn("pull_request", triggers, "Must NOT trigger on pull_request")
        self.assertNotIn("push", triggers, "Must NOT trigger on push")


if __name__ == "__main__":
    unittest.main()
