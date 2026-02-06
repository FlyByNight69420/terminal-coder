"""TMUX session monitoring utilities."""

from __future__ import annotations

from dataclasses import dataclass

from tc.tmux.manager import TmuxManager


@dataclass(frozen=True)
class SessionCheckResult:
    exited: bool
    exit_code: int | None
    stderr: str


def check_session(tmux_manager: TmuxManager, pane_id: str) -> SessionCheckResult:
    """Check the state of a TMUX pane session."""
    is_busy = tmux_manager.is_pane_busy(pane_id)

    if is_busy:
        return SessionCheckResult(exited=False, exit_code=None, stderr="")

    # Process has exited - capture any error output
    output = tmux_manager.capture_output(pane_id, lines=20)

    # Try to determine exit code from captured output
    # Convention: the last line may contain the exit code
    exit_code = 0
    for line in reversed(output.split("\n")):
        line = line.strip()
        if line.startswith("exit code:"):
            try:
                exit_code = int(line.split(":")[-1].strip())
            except ValueError:
                pass
            break

    return SessionCheckResult(exited=True, exit_code=exit_code, stderr="")
