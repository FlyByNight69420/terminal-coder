"""Frozen dataclass domain models for Terminal Coder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from tc.core.enums import (
    EventType,
    PhaseStatus,
    ProjectStatus,
    SessionStatus,
    SessionType,
    TaskStatus,
    TaskType,
)


@dataclass(frozen=True)
class Project:
    id: str
    name: str
    project_dir: str
    prd_path: str
    bootstrap_path: str | None
    claude_md_path: str | None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class Phase:
    id: str
    project_id: str
    sequence: int
    name: str
    description: str | None
    status: PhaseStatus
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class Task:
    id: str
    phase_id: str
    project_id: str
    sequence: int
    name: str
    description: str | None
    task_type: TaskType
    brief_path: str | None
    status: TaskStatus
    retry_count: int
    max_retries: int
    error_context: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class TaskDependency:
    task_id: str
    depends_on_id: str


@dataclass(frozen=True)
class Session:
    id: str
    task_id: str
    project_id: str
    session_type: SessionType
    tmux_pane: str | None
    pid: int | None
    status: SessionStatus
    exit_code: int | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_secs: int | None
    log_path: str | None
    error_output: str | None
    created_at: datetime


@dataclass(frozen=True)
class Event:
    id: int
    project_id: str
    entity_type: str
    entity_id: str
    event_type: EventType
    old_value: str | None
    new_value: str | None
    metadata: str | None
    created_at: datetime


@dataclass(frozen=True)
class BootstrapCheck:
    id: str
    project_id: str
    check_name: str
    check_type: str
    command: str
    expected: str | None
    actual_output: str | None
    passed: bool
    run_at: datetime
