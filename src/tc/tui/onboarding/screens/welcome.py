"""Welcome screen - ASCII logo and "Press Enter to begin"."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from tc.tui.onboarding.widgets.step_indicator import StepIndicator

LOGO = r"""
  _____ _____ ____  __  __ ___ _   _    _    _
 |_   _| ____|  _ \|  \/  |_ _| \ | |  / \  | |
   | | |  _| | |_) | |\/| || ||  \| | / _ \ | |
   | | | |___|  _ <| |  | || || |\  |/ ___ \| |___
   |_| |_____|_| \_\_|  |_|___|_| \_/_/   \_\_____|

    ____ ___  ____  _____ ____
   / ___/ _ \|  _ \| ____|  _ \
  | |  | | | | | | |  _| | |_) |
  | |__| |_| | |_| | |___|  _ <
   \____\___/|____/|_____|_| \_\
"""


class WelcomeScreen(Screen[None]):
    """First screen: ASCII logo and call to action."""

    BINDINGS = [
        Binding("enter", "next", "Begin", show=True),
        Binding("q", "quit_wizard", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="wizard-card"):
            indicator = StepIndicator()
            indicator.current_step = 0
            yield indicator
            yield Static(LOGO, classes="wizard-logo")
            yield Static(
                "Autonomous software building orchestrator",
                classes="wizard-subtitle",
            )
            yield Static("")
            yield Static(
                "Press Enter to begin setup",
                classes="wizard-keyhint",
            )

    def action_next(self) -> None:
        self.app.push_screen("project_setup")

    def action_quit_wizard(self) -> None:
        self.app.exit()
