"""Success screen - green checkmark and next-step commands."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from tc.tui.onboarding.state import WizardState
from tc.tui.onboarding.widgets.step_indicator import StepIndicator


class SuccessScreen(Screen[None]):
    """Seventh screen: success message and next steps."""

    BINDINGS = [
        Binding("enter", "quit_wizard", "Exit", show=True),
        Binding("q", "quit_wizard", "Exit", show=True),
    ]

    def __init__(self, state: WizardState) -> None:
        super().__init__()
        self._state = state

    def compose(self) -> ComposeResult:
        project_dir = self._state.project_dir
        has_bootstrap = bool(self._state.bootstrap_path.strip())

        with Vertical(classes="wizard-card"):
            indicator = StepIndicator()
            indicator.current_step = 6
            yield indicator

            yield Static(
                "Project Created Successfully!",
                classes="success-check",
            )
            yield Static(
                f"'{self._state.project_name}' is ready to go.",
                classes="wizard-subtitle",
            )

            yield Static("Next steps:", classes="wizard-label")
            with Vertical(classes="success-commands"):
                step = 1
                if has_bootstrap:
                    yield Static(
                        f"  {step}. tc verify --project-dir {project_dir}",
                        classes="success-command",
                    )
                    step += 1
                yield Static(
                    f"  {step}. tc plan --project-dir {project_dir}",
                    classes="success-command",
                )
                step += 1
                yield Static(
                    f"  {step}. tc run --project-dir {project_dir}",
                    classes="success-command",
                )

            yield Static("")
            yield Static(
                "Press Enter or Q to exit",
                classes="wizard-keyhint",
            )

    def action_quit_wizard(self) -> None:
        self.app.exit()
