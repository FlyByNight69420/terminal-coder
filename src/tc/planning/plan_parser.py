"""Parse Claude Code planning session output into structured data."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlannedTask:
    name: str
    description: str
    task_type: str
    depends_on: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    relevant_files: tuple[str, ...]


@dataclass(frozen=True)
class PlannedPhase:
    name: str
    description: str
    tasks: tuple[PlannedTask, ...]


@dataclass(frozen=True)
class PlanningResult:
    project_name: str
    claude_md_content: str
    phases: tuple[PlannedPhase, ...]


def parse_planning_output(raw_output: str) -> PlanningResult:
    """Extract and parse JSON from Claude's planning output."""
    json_str = _extract_json(raw_output)
    data = json.loads(json_str)
    return _build_result(data)


def _extract_json(raw: str) -> str:
    """Extract JSON from raw output, handling markdown code fences."""
    # Try to find JSON in code fences first
    fence_pattern = re.compile(r"```(?:json)?\s*\n(.*?)\n\s*```", re.DOTALL)
    match = fence_pattern.search(raw)
    if match:
        return match.group(1).strip()

    # Try to find a top-level JSON object
    brace_start = raw.find("{")
    if brace_start == -1:
        raise ValueError("No JSON object found in planning output")

    # Find the matching closing brace
    depth = 0
    for i in range(brace_start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                return raw[brace_start : i + 1]

    raise ValueError("Unclosed JSON object in planning output")


def _build_result(data: dict[str, object]) -> PlanningResult:
    """Build a PlanningResult from parsed JSON data."""
    project_name = str(data.get("project_name", "unnamed"))
    claude_md = str(data.get("claude_md", ""))

    phases_data = data.get("phases", [])
    if not isinstance(phases_data, list):
        raise ValueError("'phases' must be a list")

    phases: list[PlannedPhase] = []
    for phase_data in phases_data:
        if not isinstance(phase_data, dict):
            continue
        tasks_data = phase_data.get("tasks", [])
        if not isinstance(tasks_data, list):
            tasks_data = []

        tasks: list[PlannedTask] = []
        for task_data in tasks_data:
            if not isinstance(task_data, dict):
                continue
            tasks.append(PlannedTask(
                name=str(task_data.get("name", "Unnamed Task")),
                description=str(task_data.get("description", "")),
                task_type=str(task_data.get("task_type", "coding")),
                depends_on=tuple(
                    str(d) for d in task_data.get("depends_on", []) or []
                    if d is not None
                ),
                acceptance_criteria=tuple(
                    str(c) for c in task_data.get("acceptance_criteria", []) or []
                ),
                relevant_files=tuple(
                    str(f) for f in task_data.get("relevant_files", []) or []
                ),
            ))

        phases.append(PlannedPhase(
            name=str(phase_data.get("name", "Unnamed Phase")),
            description=str(phase_data.get("description", "")),
            tasks=tuple(tasks),
        ))

    return PlanningResult(
        project_name=project_name,
        claude_md_content=claude_md,
        phases=tuple(phases),
    )
