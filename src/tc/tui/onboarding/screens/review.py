"""Review screen - summary of all choices before init."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from tc.tui.onboarding.state import WizardState
from tc.tui.onboarding.widgets.step_indicator import StepIndicator


class ReviewScreen(Screen[None]):
    """Fifth screen: summary card with confirm/back buttons."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
        Binding("enter", "create", "Create Project", show=True),
    ]

    def __init__(self, state: WizardState) -> None:
        super().__init__()
        self._state = state

    def compose(self) -> ComposeResult:
        with Vertical(classes="wizard-card"):
            indicator = StepIndicator()
            indicator.current_step = 4
            yield indicator
            yield Static("Review", classes="wizard-title")
            yield Static(
                "Please confirm your project settings",
                classes="wizard-subtitle",
            )

            # Summary rows
            with Vertical(classes="review-table"):
                with Horizontal(classes="review-row"):
                    yield Static("Directory", classes="review-key")
                    yield Static(
                        self._state.project_dir, classes="review-value",
                    )
                with Horizontal(classes="review-row"):
                    yield Static("Name", classes="review-key")
                    yield Static(
                        self._state.project_name, classes="review-value",
                    )
                with Horizontal(classes="review-row"):
                    yield Static("PRD File", classes="review-key")
                    yield Static(
                        self._state.prd_path, classes="review-value",
                    )
                with Horizontal(classes="review-row"):
                    yield Static("Bootstrap", classes="review-key")
                    yield Static(
                        self._state.bootstrap_path or "(none)",
                        classes="review-value",
                    )

            yield Static("", id="review-error", classes="wizard-error")

            with Horizontal(classes="wizard-buttons"):
                yield Button("Back", id="back-btn", classes="wizard-btn-secondary")
                yield Button(
                    "Create Project", id="create-btn", classes="wizard-btn-primary",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.action_go_back()
        elif event.button.id == "create-btn":
            self.action_create()

    def action_create(self) -> None:
        errors = self._state.validate()
        if errors:
            error_widget = self.query_one("#review-error", Static)
            error_widget.update("\n".join(errors))
            error_widget.add_class("visible")
            return

        self._state.current_step = 5
        self.app.push_screen("progress")

    def action_go_back(self) -> None:
        self.app.pop_screen()
