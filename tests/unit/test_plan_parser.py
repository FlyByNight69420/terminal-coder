"""Tests for planning output parser."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tc.planning.plan_parser import parse_planning_output


class TestParsePlanningOutput:
    def test_parse_raw_json(self) -> None:
        raw = json.dumps({
            "project_name": "test-proj",
            "claude_md": "# Test\n\n## Build\n## Test\n## Style",
            "phases": [
                {
                    "name": "Setup",
                    "description": "Project setup",
                    "tasks": [
                        {
                            "name": "Init",
                            "description": "Initialize project",
                            "task_type": "coding",
                            "depends_on": [],
                            "acceptance_criteria": ["Works"],
                            "relevant_files": ["package.json"],
                        }
                    ],
                }
            ],
        })

        result = parse_planning_output(raw)
        assert result.project_name == "test-proj"
        assert len(result.phases) == 1
        assert result.phases[0].name == "Setup"
        assert len(result.phases[0].tasks) == 1
        assert result.phases[0].tasks[0].name == "Init"

    def test_parse_json_in_code_fences(self) -> None:
        raw = """Here is the plan:

```json
{
  "project_name": "fenced",
  "claude_md": "",
  "phases": []
}
```

Done!"""

        result = parse_planning_output(raw)
        assert result.project_name == "fenced"

    def test_parse_json_in_bare_code_fences(self) -> None:
        raw = """```
{
  "project_name": "bare",
  "claude_md": "",
  "phases": []
}
```"""

        result = parse_planning_output(raw)
        assert result.project_name == "bare"

    def test_parse_json_with_surrounding_text(self) -> None:
        raw = 'I\'ll decompose this into phases:\n\n' + json.dumps({
            "project_name": "inline",
            "claude_md": "# Proj\n## Build\n## Test\n## Style",
            "phases": [
                {
                    "name": "Phase 1",
                    "description": "First phase",
                    "tasks": [],
                }
            ],
        }, indent=2) + '\n\nThat covers everything.'

        result = parse_planning_output(raw)
        assert result.project_name == "inline"
        assert len(result.phases) == 1

    def test_parse_sample_fixture(self, fixtures_dir: Path) -> None:
        raw = (fixtures_dir / "sample_plan.json").read_text()
        result = parse_planning_output(raw)

        assert result.project_name == "todo-api"
        assert len(result.phases) == 4
        assert result.phases[0].name == "Project Setup"
        assert result.phases[1].name == "Core API"
        assert len(result.phases[1].tasks) == 2

        # Check dependencies
        crud_task = result.phases[1].tasks[1]
        assert "Database schema" in crud_task.depends_on

    def test_handles_missing_fields(self) -> None:
        raw = json.dumps({
            "phases": [
                {
                    "name": "Minimal",
                    "tasks": [{"name": "Task"}],
                }
            ],
        })

        result = parse_planning_output(raw)
        assert result.project_name == "unnamed"
        assert result.phases[0].tasks[0].task_type == "coding"

    def test_handles_null_depends_on(self) -> None:
        raw = json.dumps({
            "project_name": "test",
            "claude_md": "",
            "phases": [
                {
                    "name": "Phase",
                    "description": "",
                    "tasks": [
                        {
                            "name": "Task",
                            "description": "",
                            "task_type": "coding",
                            "depends_on": [None, "Other Task"],
                        }
                    ],
                }
            ],
        })

        result = parse_planning_output(raw)
        # None should be filtered out
        assert "Other Task" in result.phases[0].tasks[0].depends_on
        assert len(result.phases[0].tasks[0].depends_on) == 1

    def test_raises_on_no_json(self) -> None:
        with pytest.raises(ValueError, match="No JSON"):
            parse_planning_output("No json here at all")

    def test_raises_on_invalid_json(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            parse_planning_output("{invalid json}")

    def test_raises_on_invalid_phases(self) -> None:
        with pytest.raises(ValueError, match="phases"):
            parse_planning_output(json.dumps({"phases": "not a list"}))
