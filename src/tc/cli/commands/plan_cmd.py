"""tc plan command - decompose PRD into phases and tasks."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import typer
from rich.console import Console

from tc.config.settings import project_paths
from tc.core.enums import EventType, ProjectStatus, TaskType
from tc.db.connection import create_connection
from tc.db.repository import Repository
from tc.planning.claude_md_generator import write_claude_md
from tc.planning.plan_parser import PlanningResult
from tc.planning.planner import Planner, PlannerError
from tc.templates.renderer import BriefRenderer

console = Console()


def plan_command(
    project_dir: Path = typer.Option(
        None, "--project-dir", help="Project directory", resolve_path=True,
    ),
    replan: bool = typer.Option(False, "--replan", help="Re-run planning (overwrites existing)"),
) -> None:
    """Decompose PRD into phases and tasks using Claude Code."""
    resolved_dir = project_dir or Path.cwd()
    paths = project_paths(resolved_dir)

    if not paths.db_path.exists():
        console.print("[red]No project found. Run 'tc init' first.[/red]")
        raise typer.Exit(code=1)

    conn = create_connection(paths.db_path)
    try:
        repo = Repository(conn)
        row = conn.execute("SELECT id, prd_path, status FROM projects LIMIT 1").fetchone()
        if row is None:
            console.print("[red]No project found in database.[/red]")
            raise typer.Exit(code=1)

        project_id = str(row["id"])
        prd_path = Path(str(row["prd_path"]))
        status = str(row["status"])

        if status == "planned" and not replan:
            console.print("[yellow]Project already planned. Use --replan to re-run.[/yellow]")
            raise typer.Exit(code=1)

        if not prd_path.exists():
            console.print(f"[red]PRD not found: {prd_path}[/red]")
            raise typer.Exit(code=1)

        prd_content = prd_path.read_text()

        # Update status to planning
        repo.update_project_status(project_id, ProjectStatus.PLANNING)

        console.print("[bold]Running planning session...[/bold]")
        console.print("[dim]This spawns Claude Code to analyze the PRD.[/dim]\n")

        try:
            planner = Planner(resolved_dir)
            result = planner.run_planning_session(prd_content)
        except PlannerError as e:
            repo.update_project_status(project_id, ProjectStatus.FAILED)
            console.print(f"[red]Planning failed: {e}[/red]")
            raise typer.Exit(code=1)

        # Store plan in database
        _store_plan(repo, project_id, result, paths)

        # Write CLAUDE.md if generated
        if result.claude_md_content:
            try:
                write_claude_md(resolved_dir, result.claude_md_content)
                console.print("[green]Wrote CLAUDE.md[/green]")
            except Exception as e:
                console.print(f"[yellow]Could not write CLAUDE.md: {e}[/yellow]")

        # Save raw plan JSON
        plan_json_path = paths.plans_dir / "plan.json"
        plan_json_path.write_text(json.dumps(_result_to_dict(result), indent=2))

        # Update status to planned
        repo.update_project_status(project_id, ProjectStatus.PLANNED)

        # Summary
        total_tasks = sum(len(p.tasks) for p in result.phases)
        console.print(f"\n[green]Planning complete![/green]")
        console.print(f"  Phases: {len(result.phases)}")
        console.print(f"  Tasks: {total_tasks}")
        console.print(f"  Plan saved: {plan_json_path}")
        console.print(f"\nNext: tc run --project-dir {resolved_dir}")

    finally:
        conn.close()


def _store_plan(
    repo: Repository,
    project_id: str,
    result: PlanningResult,
    paths: object,
) -> None:
    """Insert phases and tasks from planning result into the database."""
    renderer = BriefRenderer()

    # Build a map of task names for dependency resolution
    task_name_to_id: dict[str, str] = {}

    for phase_seq, planned_phase in enumerate(result.phases, start=1):
        phase_id = str(uuid.uuid4())
        repo.create_phase(
            id=phase_id,
            project_id=project_id,
            sequence=phase_seq,
            name=planned_phase.name,
            description=planned_phase.description,
        )

        for task_seq, planned_task in enumerate(planned_phase.tasks, start=1):
            task_id = str(uuid.uuid4())
            task_type = _parse_task_type(planned_task.task_type)

            repo.create_task(
                id=task_id,
                phase_id=phase_id,
                project_id=project_id,
                sequence=task_seq,
                name=planned_task.name,
                task_type=task_type,
                description=planned_task.description,
            )

            task_name_to_id[planned_task.name] = task_id

    # Resolve dependencies (second pass)
    for planned_phase in result.phases:
        for planned_task in planned_phase.tasks:
            task_id = task_name_to_id.get(planned_task.name)
            if task_id is None:
                continue
            for dep_name in planned_task.depends_on:
                dep_id = task_name_to_id.get(dep_name)
                if dep_id is not None:
                    repo.add_task_dependency(task_id, dep_id)

    # Log event
    repo.create_event(
        project_id=project_id,
        entity_type="project",
        entity_id=project_id,
        event_type=EventType.STATUS_CHANGED,
        old_value="planning",
        new_value="planned",
    )


def _parse_task_type(raw: str) -> TaskType:
    """Parse task type string to enum, defaulting to coding."""
    try:
        return TaskType(raw)
    except ValueError:
        return TaskType.CODING


def _result_to_dict(result: PlanningResult) -> dict[str, object]:
    """Convert PlanningResult to a JSON-serializable dict."""
    return {
        "project_name": result.project_name,
        "claude_md": result.claude_md_content,
        "phases": [
            {
                "name": p.name,
                "description": p.description,
                "tasks": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "task_type": t.task_type,
                        "depends_on": list(t.depends_on),
                        "acceptance_criteria": list(t.acceptance_criteria),
                        "relevant_files": list(t.relevant_files),
                    }
                    for t in p.tasks
                ],
            }
            for p in result.phases
        ],
    }
