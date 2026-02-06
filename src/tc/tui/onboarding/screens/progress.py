"""Progress screen - animated init steps with spinners."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static
from textual.worker import Worker, WorkerState

from tc.core.init_service import (
    InitResult,
    ProjectAlreadyExistsError,
    initialize_project,
)
from tc.tui.onboarding.state import WizardState
from tc.tui.onboarding.widgets.step_indicator import StepIndicator

# Init steps in display order
INIT_STEPS = [
    ("directories", "Creating .tc/ directory structure"),
    ("database", "Initializing SQLite database"),
    ("prd", "Copying PRD file"),
    ("bootstrap", "Copying bootstrap file"),
    ("project_record", "Creating project record"),
    ("mcp_config", "Generating .mcp.json config"),
]

SPINNER_FRAMES = list(">>>---<<<---")
CHECK = "[bold green]OK[/bold green]"
CROSS = "[bold red]FAIL[/bold red]"
PENDING = "[dim]...[/dim]"
RUNNING = "[yellow]>>[/yellow]"


class ProgressScreen(Screen[None]):
    """Sixth screen: animated checklist showing init progress."""

    def __init__(self, state: WizardState) -> None:
        super().__init__()
        self._state = state
        self._step_widgets: dict[str, Static] = {}
        self._result: InitResult | None = None
        self._error: str | None = None

    def compose(self) -> ComposeResult:
        with Vertical(classes="wizard-card"):
            indicator = StepIndicator()
            indicator.current_step = 5
            yield indicator
            yield Static("Initializing Project", classes="wizard-title")
            yield Static("")

            has_bootstrap = bool(self._state.bootstrap_path.strip())
            for step_id, label in INIT_STEPS:
                if step_id == "bootstrap" and not has_bootstrap:
                    continue
                widget = Static(
                    f"  {PENDING}  {label}",
                    id=f"step-{step_id}",
                )
                self._step_widgets[step_id] = widget
                yield widget

            yield Static("")
            yield Static("", id="progress-status")

    def on_mount(self) -> None:
        self.run_worker(self._do_init(), exclusive=True)

    async def _do_init(self) -> None:
        wizard_result = self._state.to_result()

        def on_step(step: str, status: str) -> None:
            self.call_from_thread(self._update_step, step, status)

        try:
            self._result = initialize_project(
                project_dir=wizard_result.project_dir,
                project_name=wizard_result.project_name,
                prd_path=wizard_result.prd_path,
                bootstrap_path=wizard_result.bootstrap_path,
                on_step=on_step,
            )
        except ProjectAlreadyExistsError as exc:
            self._error = str(exc)
            self.call_from_thread(self._show_error, str(exc))
            return
        except Exception as exc:
            self._error = str(exc)
            self.call_from_thread(self._show_error, str(exc))
            return

        self.call_from_thread(self._show_done)

    def _update_step(self, step: str, status: str) -> None:
        widget = self._step_widgets.get(step)
        if widget is None:
            return

        label = ""
        for sid, lbl in INIT_STEPS:
            if sid == step:
                label = lbl
                break

        if status == "start":
            widget.update(f"  {RUNNING}  {label}")
        elif status == "done":
            widget.update(f"  {CHECK}  {label}")
        elif status == "error":
            widget.update(f"  {CROSS}  {label}")

    def _show_error(self, message: str) -> None:
        status = self.query_one("#progress-status", Static)
        status.update(f"[bold red]Error:[/bold red] {message}")

    def _show_done(self) -> None:
        status = self.query_one("#progress-status", Static)
        status.update("[bold green]Project initialized successfully![/bold green]")
        self._state.current_step = 6
        self.set_timer(1.0, self._go_to_success)

    def _go_to_success(self) -> None:
        self.app.push_screen("success")

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.ERROR:
            self._show_error("Unexpected error during initialization")
