"""Status enums for Terminal Coder domain model."""

from __future__ import annotations

from enum import StrEnum


class ProjectStatus(StrEnum):
    INITIALIZED = "initialized"
    PLANNING = "planning"
    PLANNED = "planned"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class PhaseStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TaskStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    PAUSED = "paused"
    SKIPPED = "skipped"


class TaskType(StrEnum):
    CODING = "coding"
    REVIEW = "review"
    SECURITY_REVIEW = "security_review"
    DEPLOYMENT = "deployment"
    VERIFICATION = "verification"
    PLANNING = "planning"


class SessionStatus(StrEnum):
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    KILLED = "killed"
    TIMED_OUT = "timed_out"


class SessionType(StrEnum):
    CODING = "coding"
    REVIEW = "review"
    SECURITY_REVIEW = "security_review"
    PLANNING = "planning"
    DEPLOYMENT = "deployment"
    VERIFICATION = "verification"


class EventType(StrEnum):
    STATUS_CHANGED = "status_changed"
    CREATED = "created"
    RETRIED = "retried"
    ERROR = "error"
    PAUSED = "paused"
    RESUMED = "resumed"
    REVIEW_SCHEDULED = "review_scheduled"
    DEPLOYMENT_STARTED = "deployment_started"
    VERIFICATION_RESULT = "verification_result"
    HUMAN_INPUT_REQUESTED = "human_input_requested"
