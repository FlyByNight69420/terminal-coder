"""Named SQL query constants for Terminal Coder."""

from __future__ import annotations

# -- Projects --
INSERT_PROJECT = """
INSERT INTO projects (id, name, project_dir, prd_path, bootstrap_path, claude_md_path, status)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

SELECT_PROJECT_BY_ID = "SELECT * FROM projects WHERE id = ?"

UPDATE_PROJECT_STATUS = """
UPDATE projects SET status = ?, updated_at = datetime('now') WHERE id = ?
"""

# -- Phases --
INSERT_PHASE = """
INSERT INTO phases (id, project_id, sequence, name, description, status)
VALUES (?, ?, ?, ?, ?, ?)
"""

SELECT_PHASES_BY_PROJECT = """
SELECT * FROM phases WHERE project_id = ? ORDER BY sequence
"""

UPDATE_PHASE_STATUS = "UPDATE phases SET status = ? WHERE id = ?"

UPDATE_PHASE_STARTED = """
UPDATE phases SET status = ?, started_at = datetime('now') WHERE id = ?
"""

UPDATE_PHASE_COMPLETED = """
UPDATE phases SET status = ?, completed_at = datetime('now') WHERE id = ?
"""

# -- Tasks --
INSERT_TASK = """
INSERT INTO tasks (
    id, phase_id, project_id, sequence, name, description,
    task_type, brief_path, status, retry_count, max_retries
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

SELECT_TASK_BY_ID = "SELECT * FROM tasks WHERE id = ?"

SELECT_TASKS_BY_PHASE = """
SELECT * FROM tasks WHERE phase_id = ? ORDER BY sequence
"""

SELECT_TASKS_BY_STATUS = """
SELECT * FROM tasks WHERE project_id = ? AND status = ?
"""

SELECT_TASKS_BY_PROJECT = """
SELECT * FROM tasks WHERE project_id = ? ORDER BY sequence
"""

UPDATE_TASK_STATUS = "UPDATE tasks SET status = ? WHERE id = ?"

UPDATE_TASK_STARTED = """
UPDATE tasks SET status = ?, started_at = datetime('now') WHERE id = ?
"""

UPDATE_TASK_COMPLETED = """
UPDATE tasks SET status = ?, completed_at = datetime('now') WHERE id = ?
"""

UPDATE_TASK_ERROR = """
UPDATE tasks SET error_context = ?, retry_count = retry_count + 1 WHERE id = ?
"""

UPDATE_TASK_BRIEF_PATH = "UPDATE tasks SET brief_path = ? WHERE id = ?"

# -- Task Dependencies --
INSERT_TASK_DEPENDENCY = """
INSERT INTO task_dependencies (task_id, depends_on_id) VALUES (?, ?)
"""

SELECT_TASK_DEPENDENCIES = """
SELECT * FROM task_dependencies WHERE task_id = ?
"""

SELECT_DEPENDENTS = """
SELECT * FROM task_dependencies WHERE depends_on_id = ?
"""

SELECT_PENDING_TASKS_WITH_MET_DEPENDENCIES = """
SELECT t.* FROM tasks t
WHERE t.project_id = ?
  AND t.status = 'pending'
  AND NOT EXISTS (
    SELECT 1 FROM task_dependencies td
    JOIN tasks dep ON dep.id = td.depends_on_id
    WHERE td.task_id = t.id AND dep.status != 'completed'
  )
ORDER BY t.sequence
"""

# -- Sessions --
INSERT_SESSION = """
INSERT INTO sessions (
    id, task_id, project_id, session_type, tmux_pane, pid,
    status, log_path
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

SELECT_SESSIONS_BY_TASK = """
SELECT * FROM sessions WHERE task_id = ? ORDER BY created_at DESC
"""

SELECT_ACTIVE_SESSIONS = """
SELECT * FROM sessions WHERE project_id = ? AND status IN ('pending', 'starting', 'running')
"""

UPDATE_SESSION_STATUS = "UPDATE sessions SET status = ? WHERE id = ?"

UPDATE_SESSION_COMPLETED = """
UPDATE sessions SET status = ?, exit_code = ?, completed_at = datetime('now'),
    duration_secs = CAST((julianday(datetime('now')) - julianday(started_at)) * 86400 AS INTEGER)
WHERE id = ?
"""

UPDATE_SESSION_STARTED = """
UPDATE sessions SET status = 'running', started_at = datetime('now'), pid = ? WHERE id = ?
"""

UPDATE_SESSION_ERROR = """
UPDATE sessions SET error_output = ? WHERE id = ?
"""

# -- Events --
INSERT_EVENT = """
INSERT INTO events (project_id, entity_type, entity_id, event_type, old_value, new_value, metadata)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

SELECT_EVENTS_BY_PROJECT = """
SELECT * FROM events WHERE project_id = ? ORDER BY created_at DESC LIMIT ?
"""

SELECT_EVENTS_BY_ENTITY = """
SELECT * FROM events WHERE entity_type = ? AND entity_id = ? ORDER BY created_at DESC
"""

# -- Bootstrap Checks --
INSERT_BOOTSTRAP_CHECK = """
INSERT INTO bootstrap_checks (id, project_id, check_name, check_type, command, expected, actual_output, passed)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

SELECT_BOOTSTRAP_CHECKS_BY_PROJECT = """
SELECT * FROM bootstrap_checks WHERE project_id = ? ORDER BY run_at
"""
