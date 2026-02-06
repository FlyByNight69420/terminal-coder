"""Tests for the Jinja2 brief renderer."""

from __future__ import annotations

from datetime import datetime

from tc.core.enums import PhaseStatus, SessionType, TaskStatus, TaskType
from tc.core.models import Phase, Task
from tc.templates.renderer import BriefRenderer


def _make_task(
    name: str = "Test Task",
    task_type: TaskType = TaskType.CODING,
    description: str = "A test task",
    task_id: str = "task-1",
) -> Task:
    return Task(
        id=task_id, phase_id="phase-1", project_id="proj-1", sequence=1,
        name=name, description=description, task_type=task_type,
        brief_path=None, status=TaskStatus.PENDING, retry_count=0,
        max_retries=1, error_context=None, started_at=None,
        completed_at=None, created_at=datetime.now(),
    )


def _make_phase(
    name: str = "Phase 1",
    sequence: int = 1,
) -> Phase:
    return Phase(
        id="phase-1", project_id="proj-1", sequence=sequence,
        name=name, description="Test phase", status=PhaseStatus.PENDING,
        started_at=None, completed_at=None, created_at=datetime.now(),
    )


class TestBriefRenderer:
    def setup_method(self) -> None:
        self.renderer = BriefRenderer()

    def test_render_planning_brief(self) -> None:
        result = self.renderer.render_planning_brief("# My PRD\n\nBuild a REST API.")
        assert "My PRD" in result
        assert "Build a REST API" in result
        assert "JSON" in result
        assert "phases" in result

    def test_render_task_brief(self) -> None:
        task = _make_task()
        phase = _make_phase()
        result = self.renderer.render_task_brief(
            task=task, phase=phase, total_phases=3,
            project_overview="A todo API project",
            acceptance_criteria=["Tests pass", "Endpoint works"],
            relevant_files=["src/api.py"],
        )
        assert "Test Task" in result
        assert "task-1" in result
        assert "Phase 1" in result
        assert "A todo API project" in result
        assert "Tests pass" in result
        assert "src/api.py" in result
        assert "tc_report_completion" in result

    def test_render_task_brief_with_completed_tasks(self) -> None:
        task = _make_task()
        phase = _make_phase()
        completed = _make_task(name="Previous Task", task_id="task-0")
        result = self.renderer.render_task_brief(
            task=task, phase=phase, total_phases=2,
            project_overview="Overview",
            completed_tasks=[completed],
        )
        assert "Previous Task" in result
        assert "Previously Completed Work" in result

    def test_render_task_brief_with_review_findings(self) -> None:
        task = _make_task()
        phase = _make_phase()
        result = self.renderer.render_task_brief(
            task=task, phase=phase, total_phases=1,
            project_overview="Overview",
            review_findings=["Missing error handling", "Add input validation"],
        )
        assert "Missing error handling" in result
        assert "Review Findings" in result

    def test_render_review_brief(self) -> None:
        task = _make_task(name="Review: API", task_type=TaskType.REVIEW, task_id="review-1")
        source = _make_task(name="Build API")
        result = self.renderer.render_review_brief(
            task=task, source_task=source,
            files_changed=["src/api.py", "tests/test_api.py"],
        )
        assert "Review: API" in result
        assert "Build API" in result
        assert "src/api.py" in result
        assert "tc_report_review" in result
        assert "Code Quality" in result

    def test_render_security_brief(self) -> None:
        task = _make_task(
            name="Security: Auth", task_type=TaskType.SECURITY_REVIEW, task_id="sec-1"
        )
        source = _make_task(name="Auth endpoints")
        result = self.renderer.render_security_brief(
            task=task, source_task=source,
            files_changed=["src/auth.py"],
            security_concern="authentication",
        )
        assert "Security Review" in result
        assert "authentication" in result
        assert "OWASP" in result
        assert "critical_issues" in result

    def test_render_deploy_brief(self) -> None:
        task = _make_task(name="Deploy to prod", task_type=TaskType.DEPLOYMENT, task_id="dep-1")
        phase = _make_phase(name="Deployment")
        result = self.renderer.render_deploy_brief(
            task=task, phase=phase,
            deployment_steps=["Build Docker image", "Push to registry"],
            verification_steps=["Check health endpoint", "Verify API responds"],
        )
        assert "Deploy to prod" in result
        assert "Build Docker image" in result
        assert "Check health endpoint" in result
        assert "Rollback" in result
