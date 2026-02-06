"""Onboarding wizard app - standalone Textual app for tc init."""

from __future__ import annotations

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from tc.tui.onboarding.screens.bootstrap_file import BootstrapFileScreen
from tc.tui.onboarding.screens.prd_file import PrdFileScreen
from tc.tui.onboarding.screens.progress import ProgressScreen
from tc.tui.onboarding.screens.project_setup import ProjectSetupScreen
from tc.tui.onboarding.screens.review import ReviewScreen
from tc.tui.onboarding.screens.success import SuccessScreen
from tc.tui.onboarding.screens.welcome import WelcomeScreen
from tc.tui.onboarding.state import WizardState


class OnboardingApp(App[None]):
    """Step-by-step onboarding wizard for tc init.

    Launches when the user runs `tc` or `tc init` with no arguments.
    Guides through project setup and calls init_service to create
    the project.
    """

    TITLE = "Terminal Coder Setup"

    CSS_PATH = str(
        Path(__file__).parent.parent / "styles" / "wizard.tcss"
    )

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._state = WizardState()

    def on_mount(self) -> None:
        # Register named screens with shared state
        self.install_screen(WelcomeScreen(), name="welcome")
        self.install_screen(
            ProjectSetupScreen(self._state), name="project_setup",
        )
        self.install_screen(PrdFileScreen(self._state), name="prd_file")
        self.install_screen(
            BootstrapFileScreen(self._state), name="bootstrap_file",
        )
        self.install_screen(ReviewScreen(self._state), name="review")
        self.install_screen(ProgressScreen(self._state), name="progress")
        self.install_screen(SuccessScreen(self._state), name="success")

        self.push_screen("welcome")
