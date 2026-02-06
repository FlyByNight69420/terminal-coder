"""Bootstrap file screen - optional bootstrap markdown file."""

from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from tc.tui.onboarding.state import WizardState
from tc.tui.onboarding.widgets.step_indicator import StepIndicator


class BootstrapFileScreen(Screen[None]):
    """Fourth screen: optional bootstrap file path."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, state: WizardState) -> None:
        super().__init__()
        self._state = state

    def compose(self) -> ComposeResult:
        with Vertical(classes="wizard-card"):
            indicator = StepIndicator()
            indicator.current_step = 3
            yield indicator
            yield Static("Bootstrap File", classes="wizard-title")
            yield Static(
                "Optional: verification rules for your project setup",
                classes="wizard-subtitle",
            )

            yield Static("Bootstrap File Path", classes="wizard-label")
            yield Input(
                value=self._state.bootstrap_path,
                placeholder="/path/to/bootstrap.md (optional)",
                id="bootstrap-input",
                classes="wizard-input",
            )
            yield Static("", id="bootstrap-error", classes="wizard-error")
            yield Static(
                "Leave empty or press Skip to continue without a bootstrap file",
                classes="wizard-hint",
            )

            with Horizontal(classes="wizard-buttons"):
                yield Button("Back", id="back-btn", classes="wizard-btn-secondary")
                yield Button("Skip", id="skip-btn", classes="wizard-btn-skip")
                yield Button("Next", id="next-btn", classes="wizard-btn-primary")

    def on_screen_resume(self) -> None:
        if self._state.prd_generated and self._state.bootstrap_path:
            self.query_one("#bootstrap-input", Input).value = (
                self._state.bootstrap_path
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._advance()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "bootstrap-input":
            error = self.query_one("#bootstrap-error", Static)
            val = event.value.strip()
            if val:
                p = Path(val)
                if not p.exists():
                    error.update("File does not exist")
                    error.add_class("visible")
                elif not p.is_file():
                    error.update("Path is not a file")
                    error.add_class("visible")
                else:
                    error.remove_class("visible")
            else:
                error.remove_class("visible")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.action_go_back()
        elif event.button.id == "skip-btn":
            self._state.bootstrap_path = ""
            self._state.current_step = 4
            self.app.push_screen("review")
        elif event.button.id == "next-btn":
            self._advance()

    def _advance(self) -> None:
        val = self.query_one("#bootstrap-input", Input).value.strip()

        if val:
            p = Path(val)
            if not p.exists() or not p.is_file():
                return
            self._state.bootstrap_path = val
        else:
            self._state.bootstrap_path = ""

        self._state.current_step = 4
        self.app.push_screen("review")

    def action_go_back(self) -> None:
        self.app.pop_screen()
