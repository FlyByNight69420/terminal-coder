"""Key constants for Terminal Coder. Do not hardcode these values elsewhere."""

from __future__ import annotations

POLL_INTERVAL_SECS: float = 2.0
SESSION_TIMEOUT_SECS: int = 1800  # 30 min
REVIEW_TIMEOUT_SECS: int = 600  # 10 min
MAX_RETRIES_DEFAULT: int = 1
GRACEFUL_KILL_WAIT_SECS: int = 10
MAX_CONCURRENT_CODING: int = 1
MAX_CONCURRENT_REVIEW: int = 1
MAX_TMUX_PANES: int = 2
DB_FILENAME: str = "tc.db"
TC_DIR: str = ".tc"
BRIEFS_DIR: str = "briefs"
LOGS_DIR: str = "logs"
PLANS_DIR: str = "plans"
