"""Planning session orchestrator - spawns Claude Code to decompose a PRD."""

from __future__ import annotations

import subprocess
from pathlib import Path

from tc.planning.plan_parser import PlanningResult, parse_planning_output
from tc.templates.renderer import BriefRenderer


class PlannerError(Exception):
    """Raised when planning session fails."""


class Planner:
    """Spawns a Claude Code session to decompose a PRD into phases and tasks."""

    def __init__(self, project_dir: Path, renderer: BriefRenderer | None = None) -> None:
        self._project_dir = project_dir
        self._renderer = renderer or BriefRenderer()

    def run_planning_session(self, prd_content: str) -> PlanningResult:
        """Render planning brief and run Claude Code to decompose the PRD."""
        brief = self._renderer.render_planning_brief(prd_content)
        raw_output = self._invoke_claude(brief)
        return parse_planning_output(raw_output)

    def _invoke_claude(self, prompt: str) -> str:
        """Invoke claude -p with the given prompt and return stdout."""
        try:
            result = subprocess.run(
                ["claude", "-p", "--output-format", "text"],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for planning
                cwd=str(self._project_dir),
            )
        except FileNotFoundError:
            raise PlannerError(
                "Claude Code CLI not found. Install it: https://docs.anthropic.com/en/docs/claude-code"
            )
        except subprocess.TimeoutExpired:
            raise PlannerError("Planning session timed out after 5 minutes")

        if result.returncode != 0:
            raise PlannerError(
                f"Claude Code exited with code {result.returncode}: {result.stderr[:500]}"
            )

        return result.stdout
