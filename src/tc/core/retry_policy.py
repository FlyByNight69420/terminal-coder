"""Retry policy for failed tasks."""

from __future__ import annotations

from tc.core.models import Task


class RetryPolicy:
    """Determines whether a failed task should be retried."""

    def __init__(self, max_retries: int = 1) -> None:
        self._max_retries = max_retries

    def should_retry(self, task: Task) -> bool:
        """Check if a task is eligible for retry."""
        return task.retry_count < min(task.max_retries, self._max_retries)

    def prepare_retry_context(self, task: Task, error_output: str) -> str:
        """Format error context to include in the retry brief."""
        return (
            f"PREVIOUS ATTEMPT FAILED (attempt {task.retry_count + 1}):\n"
            f"Error: {error_output[:2000]}\n\n"
            f"Please address this error and try a different approach if needed."
        )
