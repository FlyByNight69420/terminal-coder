"""Jinja2 template renderer for task briefs."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from tc.core.models import Phase, Task

# Default templates directory is the package directory containing the .j2 files
_DEFAULT_TEMPLATES_DIR = Path(__file__).parent


class BriefRenderer:
    """Renders task brief templates using Jinja2."""

    def __init__(self, templates_dir: Path | None = None) -> None:
        dir_path = templates_dir or _DEFAULT_TEMPLATES_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(dir_path)),
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_planning_brief(self, prd_content: str) -> str:
        """Render the planning brief template with PRD content."""
        template = self._env.get_template("planning_brief.md.j2")
        return template.render(prd_content=prd_content)

    def render_task_brief(
        self,
        task: Task,
        phase: Phase,
        total_phases: int,
        project_overview: str,
        *,
        completed_tasks: list[Task] | None = None,
        review_findings: list[str] | None = None,
        acceptance_criteria: list[str] | None = None,
        relevant_files: list[str] | None = None,
    ) -> str:
        """Render a coding task brief."""
        template = self._env.get_template("task_brief.md.j2")
        return template.render(
            task=task,
            phase=phase,
            total_phases=total_phases,
            project_overview=project_overview,
            completed_tasks=completed_tasks or [],
            review_findings=review_findings or [],
            acceptance_criteria=acceptance_criteria or [],
            relevant_files=relevant_files or [],
        )

    def render_review_brief(
        self,
        task: Task,
        source_task: Task,
        files_changed: list[str],
    ) -> str:
        """Render a code review brief."""
        template = self._env.get_template("review_brief.md.j2")
        return template.render(
            task=task,
            source_task=source_task,
            files_changed=files_changed,
        )

    def render_security_brief(
        self,
        task: Task,
        source_task: Task,
        files_changed: list[str],
        security_concern: str,
    ) -> str:
        """Render a security review brief."""
        template = self._env.get_template("security_brief.md.j2")
        return template.render(
            task=task,
            source_task=source_task,
            files_changed=files_changed,
            security_concern=security_concern,
        )

    def render_deploy_brief(
        self,
        task: Task,
        phase: Phase,
        *,
        deployment_steps: list[str] | None = None,
        verification_steps: list[str] | None = None,
    ) -> str:
        """Render a deployment task brief."""
        template = self._env.get_template("deploy_brief.md.j2")
        return template.render(
            task=task,
            phase=phase,
            deployment_steps=deployment_steps or [],
            verification_steps=verification_steps or [],
        )
