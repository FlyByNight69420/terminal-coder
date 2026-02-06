"""Repository pattern for Terminal Coder database operations."""

from __future__ import annotations

import sqlite3
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
from tc.core.models import (
    BootstrapCheck,
    Event,
    Phase,
    Project,
    Session,
    Task,
    TaskDependency,
)
from tc.db import queries


def _parse_dt(val: object) -> datetime:
    """Parse a datetime string from SQLite."""
    if val is None:
        return datetime.min
    return datetime.fromisoformat(str(val))


def _parse_dt_opt(val: object) -> datetime | None:
    """Parse an optional datetime string from SQLite."""
    if val is None:
        return None
    return datetime.fromisoformat(str(val))


def _bool_from_int(val: object) -> bool:
    return bool(val)


def _project_from_row(row: dict[str, object]) -> Project:
    return Project(
        id=str(row["id"]),
        name=str(row["name"]),
        project_dir=str(row["project_dir"]),
        prd_path=str(row["prd_path"]),
        bootstrap_path=str(row["bootstrap_path"]) if row["bootstrap_path"] else None,
        claude_md_path=str(row["claude_md_path"]) if row["claude_md_path"] else None,
        status=ProjectStatus(str(row["status"])),
        created_at=_parse_dt(row["created_at"]),
        updated_at=_parse_dt(row["updated_at"]),
    )


def _phase_from_row(row: dict[str, object]) -> Phase:
    return Phase(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        sequence=int(row["sequence"]),  # type: ignore[arg-type]
        name=str(row["name"]),
        description=str(row["description"]) if row["description"] else None,
        status=PhaseStatus(str(row["status"])),
        started_at=_parse_dt_opt(row["started_at"]),
        completed_at=_parse_dt_opt(row["completed_at"]),
        created_at=_parse_dt(row["created_at"]),
    )


def _task_from_row(row: dict[str, object]) -> Task:
    return Task(
        id=str(row["id"]),
        phase_id=str(row["phase_id"]),
        project_id=str(row["project_id"]),
        sequence=int(row["sequence"]),  # type: ignore[arg-type]
        name=str(row["name"]),
        description=str(row["description"]) if row["description"] else None,
        task_type=TaskType(str(row["task_type"])),
        brief_path=str(row["brief_path"]) if row["brief_path"] else None,
        status=TaskStatus(str(row["status"])),
        retry_count=int(row["retry_count"]),  # type: ignore[arg-type]
        max_retries=int(row["max_retries"]),  # type: ignore[arg-type]
        error_context=str(row["error_context"]) if row["error_context"] else None,
        started_at=_parse_dt_opt(row["started_at"]),
        completed_at=_parse_dt_opt(row["completed_at"]),
        created_at=_parse_dt(row["created_at"]),
    )


def _session_from_row(row: dict[str, object]) -> Session:
    return Session(
        id=str(row["id"]),
        task_id=str(row["task_id"]),
        project_id=str(row["project_id"]),
        session_type=SessionType(str(row["session_type"])),
        tmux_pane=str(row["tmux_pane"]) if row["tmux_pane"] else None,
        pid=int(row["pid"]) if row["pid"] else None,  # type: ignore[arg-type]
        status=SessionStatus(str(row["status"])),
        exit_code=int(row["exit_code"]) if row["exit_code"] is not None else None,  # type: ignore[arg-type]
        started_at=_parse_dt_opt(row["started_at"]),
        completed_at=_parse_dt_opt(row["completed_at"]),
        duration_secs=int(row["duration_secs"]) if row["duration_secs"] is not None else None,  # type: ignore[arg-type]
        log_path=str(row["log_path"]) if row["log_path"] else None,
        error_output=str(row["error_output"]) if row["error_output"] else None,
        created_at=_parse_dt(row["created_at"]),
    )


def _event_from_row(row: dict[str, object]) -> Event:
    return Event(
        id=int(row["id"]),  # type: ignore[arg-type]
        project_id=str(row["project_id"]),
        entity_type=str(row["entity_type"]),
        entity_id=str(row["entity_id"]),
        event_type=EventType(str(row["event_type"])),
        old_value=str(row["old_value"]) if row["old_value"] else None,
        new_value=str(row["new_value"]) if row["new_value"] else None,
        metadata=str(row["metadata"]) if row["metadata"] else None,
        created_at=_parse_dt(row["created_at"]),
    )


def _bootstrap_check_from_row(row: dict[str, object]) -> BootstrapCheck:
    return BootstrapCheck(
        id=str(row["id"]),
        project_id=str(row["project_id"]),
        check_name=str(row["check_name"]),
        check_type=str(row["check_type"]),
        command=str(row["command"]),
        expected=str(row["expected"]) if row["expected"] else None,
        actual_output=str(row["actual_output"]) if row["actual_output"] else None,
        passed=_bool_from_int(row["passed"]),
        run_at=_parse_dt(row["run_at"]),
    )


class Repository:
    """Database repository for Terminal Coder entities."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    # -- Projects --

    def create_project(
        self,
        id: str,
        name: str,
        project_dir: str,
        prd_path: str,
        *,
        bootstrap_path: str | None = None,
        claude_md_path: str | None = None,
        status: ProjectStatus = ProjectStatus.INITIALIZED,
    ) -> Project:
        self._conn.execute(
            queries.INSERT_PROJECT,
            (id, name, project_dir, prd_path, bootstrap_path, claude_md_path, status.value),
        )
        self._conn.commit()
        return self.get_project(id)

    def get_project(self, project_id: str) -> Project:
        row = self._conn.execute(queries.SELECT_PROJECT_BY_ID, (project_id,)).fetchone()
        if row is None:
            raise ValueError(f"Project not found: {project_id}")
        return _project_from_row(row)

    def update_project_status(self, project_id: str, status: ProjectStatus) -> Project:
        self._conn.execute(queries.UPDATE_PROJECT_STATUS, (status.value, project_id))
        self._conn.commit()
        return self.get_project(project_id)

    # -- Phases --

    def create_phase(
        self,
        id: str,
        project_id: str,
        sequence: int,
        name: str,
        *,
        description: str | None = None,
        status: PhaseStatus = PhaseStatus.PENDING,
    ) -> Phase:
        self._conn.execute(
            queries.INSERT_PHASE,
            (id, project_id, sequence, name, description, status.value),
        )
        self._conn.commit()
        return self.get_phases_by_project(project_id)[sequence - 1]

    def get_phases_by_project(self, project_id: str) -> list[Phase]:
        rows = self._conn.execute(queries.SELECT_PHASES_BY_PROJECT, (project_id,)).fetchall()
        return [_phase_from_row(row) for row in rows]

    def update_phase_status(self, phase_id: str, status: PhaseStatus) -> None:
        if status == PhaseStatus.IN_PROGRESS:
            self._conn.execute(queries.UPDATE_PHASE_STARTED, (status.value, phase_id))
        elif status in (PhaseStatus.COMPLETED, PhaseStatus.FAILED):
            self._conn.execute(queries.UPDATE_PHASE_COMPLETED, (status.value, phase_id))
        else:
            self._conn.execute(queries.UPDATE_PHASE_STATUS, (status.value, phase_id))
        self._conn.commit()

    # -- Tasks --

    def create_task(
        self,
        id: str,
        phase_id: str,
        project_id: str,
        sequence: int,
        name: str,
        task_type: TaskType,
        *,
        description: str | None = None,
        brief_path: str | None = None,
        status: TaskStatus = TaskStatus.PENDING,
        retry_count: int = 0,
        max_retries: int = 1,
    ) -> Task:
        self._conn.execute(
            queries.INSERT_TASK,
            (
                id, phase_id, project_id, sequence, name, description,
                task_type.value, brief_path, status.value, retry_count, max_retries,
            ),
        )
        self._conn.commit()
        return self.get_task(id)

    def get_task(self, task_id: str) -> Task:
        row = self._conn.execute(queries.SELECT_TASK_BY_ID, (task_id,)).fetchone()
        if row is None:
            raise ValueError(f"Task not found: {task_id}")
        return _task_from_row(row)

    def get_tasks_by_phase(self, phase_id: str) -> list[Task]:
        rows = self._conn.execute(queries.SELECT_TASKS_BY_PHASE, (phase_id,)).fetchall()
        return [_task_from_row(row) for row in rows]

    def get_tasks_by_project(self, project_id: str) -> list[Task]:
        rows = self._conn.execute(queries.SELECT_TASKS_BY_PROJECT, (project_id,)).fetchall()
        return [_task_from_row(row) for row in rows]

    def get_tasks_by_status(self, project_id: str, status: TaskStatus) -> list[Task]:
        rows = self._conn.execute(
            queries.SELECT_TASKS_BY_STATUS, (project_id, status.value)
        ).fetchall()
        return [_task_from_row(row) for row in rows]

    def get_pending_tasks_with_met_deps(self, project_id: str) -> list[Task]:
        rows = self._conn.execute(
            queries.SELECT_PENDING_TASKS_WITH_MET_DEPENDENCIES, (project_id,)
        ).fetchall()
        return [_task_from_row(row) for row in rows]

    def update_task_status(self, task_id: str, status: TaskStatus) -> Task:
        if status == TaskStatus.RUNNING:
            self._conn.execute(queries.UPDATE_TASK_STARTED, (status.value, task_id))
        elif status == TaskStatus.COMPLETED:
            self._conn.execute(queries.UPDATE_TASK_COMPLETED, (status.value, task_id))
        else:
            self._conn.execute(queries.UPDATE_TASK_STATUS, (status.value, task_id))
        self._conn.commit()
        return self.get_task(task_id)

    def update_task_error(self, task_id: str, error_context: str) -> Task:
        self._conn.execute(queries.UPDATE_TASK_ERROR, (error_context, task_id))
        self._conn.commit()
        return self.get_task(task_id)

    def update_task_brief_path(self, task_id: str, brief_path: str) -> Task:
        self._conn.execute(queries.UPDATE_TASK_BRIEF_PATH, (brief_path, task_id))
        self._conn.commit()
        return self.get_task(task_id)

    # -- Task Dependencies --

    def add_task_dependency(self, task_id: str, depends_on_id: str) -> TaskDependency:
        self._conn.execute(queries.INSERT_TASK_DEPENDENCY, (task_id, depends_on_id))
        self._conn.commit()
        return TaskDependency(task_id=task_id, depends_on_id=depends_on_id)

    def get_task_dependencies(self, task_id: str) -> list[TaskDependency]:
        rows = self._conn.execute(queries.SELECT_TASK_DEPENDENCIES, (task_id,)).fetchall()
        return [
            TaskDependency(task_id=str(row["task_id"]), depends_on_id=str(row["depends_on_id"]))
            for row in rows
        ]

    # -- Sessions --

    def create_session(
        self,
        id: str,
        task_id: str,
        project_id: str,
        session_type: SessionType,
        *,
        tmux_pane: str | None = None,
        pid: int | None = None,
        status: SessionStatus = SessionStatus.PENDING,
        log_path: str | None = None,
    ) -> Session:
        self._conn.execute(
            queries.INSERT_SESSION,
            (id, task_id, project_id, session_type.value, tmux_pane, pid, status.value, log_path),
        )
        self._conn.commit()
        return self.get_sessions_by_task(task_id)[0]

    def get_sessions_by_task(self, task_id: str) -> list[Session]:
        rows = self._conn.execute(queries.SELECT_SESSIONS_BY_TASK, (task_id,)).fetchall()
        return [_session_from_row(row) for row in rows]

    def get_active_sessions(self, project_id: str) -> list[Session]:
        rows = self._conn.execute(queries.SELECT_ACTIVE_SESSIONS, (project_id,)).fetchall()
        return [_session_from_row(row) for row in rows]

    def update_session_status(self, session_id: str, status: SessionStatus) -> None:
        self._conn.execute(queries.UPDATE_SESSION_STATUS, (status.value, session_id))
        self._conn.commit()

    def update_session_started(self, session_id: str, pid: int) -> None:
        self._conn.execute(queries.UPDATE_SESSION_STARTED, (pid, session_id))
        self._conn.commit()

    def update_session_completed(
        self, session_id: str, status: SessionStatus, exit_code: int
    ) -> None:
        self._conn.execute(queries.UPDATE_SESSION_COMPLETED, (status.value, exit_code, session_id))
        self._conn.commit()

    def update_session_error(self, session_id: str, error_output: str) -> None:
        self._conn.execute(queries.UPDATE_SESSION_ERROR, (error_output, session_id))
        self._conn.commit()

    # -- Events --

    def create_event(
        self,
        project_id: str,
        entity_type: str,
        entity_id: str,
        event_type: EventType,
        *,
        old_value: str | None = None,
        new_value: str | None = None,
        metadata: str | None = None,
    ) -> Event:
        cursor = self._conn.execute(
            queries.INSERT_EVENT,
            (project_id, entity_type, entity_id, event_type.value, old_value, new_value, metadata),
        )
        self._conn.commit()
        event_id = cursor.lastrowid
        rows = self._conn.execute(
            "SELECT * FROM events WHERE id = ?", (event_id,)
        ).fetchall()
        return _event_from_row(rows[0])

    def get_events_by_project(self, project_id: str, limit: int = 50) -> list[Event]:
        rows = self._conn.execute(
            queries.SELECT_EVENTS_BY_PROJECT, (project_id, limit)
        ).fetchall()
        return [_event_from_row(row) for row in rows]

    def get_events_by_entity(self, entity_type: str, entity_id: str) -> list[Event]:
        rows = self._conn.execute(
            queries.SELECT_EVENTS_BY_ENTITY, (entity_type, entity_id)
        ).fetchall()
        return [_event_from_row(row) for row in rows]

    # -- Bootstrap Checks --

    def create_bootstrap_check(
        self,
        id: str,
        project_id: str,
        check_name: str,
        check_type: str,
        command: str,
        *,
        expected: str | None = None,
        actual_output: str | None = None,
        passed: bool = False,
    ) -> BootstrapCheck:
        self._conn.execute(
            queries.INSERT_BOOTSTRAP_CHECK,
            (id, project_id, check_name, check_type, command, expected, actual_output, int(passed)),
        )
        self._conn.commit()
        rows = self._conn.execute(
            "SELECT * FROM bootstrap_checks WHERE id = ?", (id,)
        ).fetchall()
        return _bootstrap_check_from_row(rows[0])

    def get_bootstrap_checks_by_project(self, project_id: str) -> list[BootstrapCheck]:
        rows = self._conn.execute(
            queries.SELECT_BOOTSTRAP_CHECKS_BY_PROJECT, (project_id,)
        ).fetchall()
        return [_bootstrap_check_from_row(row) for row in rows]
