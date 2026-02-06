"""Tests for TUI widgets."""

from __future__ import annotations

from datetime import datetime

from tc.core.enums import EventType, PhaseStatus, SessionStatus, SessionType, TaskStatus, TaskType
from tc.core.models import Event, Phase, Session, Task
from tc.tui.widgets.header import ProjectHeader, _status_color
from tc.tui.widgets.phase_tree import _PHASE_ICONS, _TASK_ICONS
from tc.tui.widgets.session_panel import _type_badge
from tc.tui.widgets.status_bar import StatusBar


class TestProjectHeader:
    def test_status_colors(self) -> None:
        assert "green" in _status_color("completed")
        assert "yellow" in _status_color("running")
        assert "red" in _status_color("failed")

    def test_compose_text(self) -> None:
        header = ProjectHeader(
            project_name="test-project",
            status="running",
            phase_info="Phase 2/4",
        )
        text = header.compose_text()
        assert "test-project" in text
        assert "running" in text
        assert "Phase 2/4" in text


class TestPhaseTreeIcons:
    def test_phase_icons(self) -> None:
        assert "[OK]" == _PHASE_ICONS[PhaseStatus.COMPLETED]
        assert "[>>]" == _PHASE_ICONS[PhaseStatus.IN_PROGRESS]
        assert "[!!]" == _PHASE_ICONS[PhaseStatus.FAILED]
        assert "[--]" == _PHASE_ICONS[PhaseStatus.PENDING]

    def test_task_icons(self) -> None:
        assert "[x]" == _TASK_ICONS[TaskStatus.COMPLETED]
        assert "[>]" == _TASK_ICONS[TaskStatus.RUNNING]
        assert "[!]" == _TASK_ICONS[TaskStatus.FAILED]
        assert "[ ]" == _TASK_ICONS[TaskStatus.PENDING]
        assert "[~]" == _TASK_ICONS[TaskStatus.RETRYING]


class TestSessionPanel:
    def test_type_badges(self) -> None:
        assert "CODING" in _type_badge("coding")
        assert "REVIEW" in _type_badge("review")
        assert "SECURITY" in _type_badge("security_review")
        assert "DEPLOY" in _type_badge("deployment")


class TestStatusBar:
    def test_render_default(self) -> None:
        bar = StatusBar()
        text = bar._render()
        assert "[P]" in text
        assert "[R]" in text
        assert "[K]" in text
        assert "[Q]" in text

    def test_render_paused(self) -> None:
        bar = StatusBar()
        bar.refresh_data(paused=True, failed_count=0)
        text = bar._render()
        assert "PAUSED" in text

    def test_render_with_failures(self) -> None:
        bar = StatusBar()
        bar.refresh_data(paused=False, failed_count=3)
        text = bar._render()
        assert "3 failed" in text
