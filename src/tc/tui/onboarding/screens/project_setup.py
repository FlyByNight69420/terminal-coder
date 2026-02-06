"""Project setup screen - directory path and project name."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from tc.tui.onboarding.state import WizardState
from tc.tui.onboarding.widgets.step_indicator import StepIndicator


class ProjectSetupScreen(Screen[None]):
    """Second screen: project directory and name inputs."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, state: WizardState) -> None:
        super().__init__()
        self._state = state

    def compose(self) -> ComposeResult:
        with Vertical(classes="wizard-card"):
            indicator = StepIndicator()
            indicator.current_step = 1
            yield indicator
            yield Static("Project Setup", classes="wizard-title")
            yield Static(
                "Where is your project located?",
                classes="wizard-subtitle",
            )

            yield Static("Project Directory", classes="wizard-label")
            yield Input(
                value=self._state.project_dir or str(Path.cwd()),
                placeholder="/path/to/your/project",
                id="dir-input",
                classes="wizard-input",
            )
            yield Static("", id="dir-error", classes="wizard-error")

            yield Static("Project Name", classes="wizard-label")
            yield Input(
                value=self._state.project_name,
                placeholder="my-project",
                id="name-input",
                classes="wizard-input",
            )
            yield Static(
                "Auto-derived from directory name if left empty",
                classes="wizard-hint",
            )

            with Horizontal(classes="wizard-buttons"):
                yield Button("Back", id="back-btn", classes="wizard-btn-secondary")
                yield Button("Next", id="next-btn", classes="wizard-btn-primary")

    def on_mount(self) -> None:
        dir_input = self.query_one("#dir-input", Input)
        if not self._state.project_name and dir_input.value:
            name_input = self.query_one("#name-input", Input)
            name_input.value = Path(dir_input.value).name

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "dir-input":
            # Auto-derive name from dir
            name_input = self.query_one("#name-input", Input)
            if not name_input.value or name_input.value == self._state.project_name:
                val = event.value.strip()
                if val:
                    name_input.value = Path(val).name

            # Validate directory
            error = self.query_one("#dir-error", Static)
            val = event.value.strip()
            if val:
                p = Path(val)
                if not p.is_absolute():
                    error.update("Must be an absolute path")
                    error.add_class("visible")
                elif not p.exists():
                    error.update("Directory does not exist")
                    error.add_class("visible")
                elif not p.is_dir():
                    error.update("Path is not a directory")
                    error.add_class("visible")
                else:
                    error.remove_class("visible")
            else:
                error.remove_class("visible")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # Both dir-input and name-input can trigger advance via Enter
        self._advance()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.action_go_back()
        elif event.button.id == "next-btn":
            self._advance()

    def _advance(self) -> None:
        dir_val = self.query_one("#dir-input", Input).value.strip()
        name_val = self.query_one("#name-input", Input).value.strip()

        # Validate
        if not dir_val:
            error = self.query_one("#dir-error", Static)
            error.update("Project directory is required")
            error.add_class("visible")
            return

        p = Path(dir_val)
        if not p.is_absolute() or not p.exists() or not p.is_dir():
            return

        self._state.project_dir = dir_val
        self._state.project_name = name_val or p.name
        self._state.current_step = 2
        self.app.push_screen("prd_file")

    def action_go_back(self) -> None:
        self.app.pop_screen()
