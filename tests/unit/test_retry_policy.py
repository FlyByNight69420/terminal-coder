"""Tests for the retry policy."""

from __future__ import annotations

from datetime import datetime

from tc.core.enums import TaskStatus, TaskType
from tc.core.models import Task
from tc.core.retry_policy import RetryPolicy


def _make_task(retry_count: int = 0, max_retries: int = 1) -> Task:
    return Task(
        id="t1", phase_id="p1", project_id="proj-1", sequence=1,
        name="Test Task", description="Test", task_type=TaskType.CODING,
        brief_path=None, status=TaskStatus.FAILED,
        retry_count=retry_count, max_retries=max_retries,
        error_context=None, started_at=None, completed_at=None,
        created_at=datetime.now(),
    )


class TestRetryPolicy:
    def test_should_retry_first_failure(self) -> None:
        policy = RetryPolicy(max_retries=1)
        task = _make_task(retry_count=0)
        assert policy.should_retry(task) is True

    def test_should_not_retry_after_max(self) -> None:
        policy = RetryPolicy(max_retries=1)
        task = _make_task(retry_count=1)
        assert policy.should_retry(task) is False

    def test_respects_task_max_retries(self) -> None:
        policy = RetryPolicy(max_retries=5)
        task = _make_task(retry_count=2, max_retries=3)
        assert policy.should_retry(task) is True

    def test_prepare_retry_context(self) -> None:
        policy = RetryPolicy()
        task = _make_task(retry_count=0)
        context = policy.prepare_retry_context(task, "Module not found: foo")
        assert "PREVIOUS ATTEMPT FAILED" in context
        assert "attempt 1" in context
        assert "Module not found: foo" in context

    def test_truncates_long_errors(self) -> None:
        policy = RetryPolicy()
        task = _make_task()
        long_error = "x" * 5000
        context = policy.prepare_retry_context(task, long_error)
        assert len(context) < 5000  # Should be truncated
