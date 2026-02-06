"""PRD file screen - select or generate a PRD markdown file."""

from __future__ import annotations

import subprocess
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, OptionList, Static, TextArea
from textual.widgets.option_list import Option

from tc.orchestrator.prd_launcher import (
    ClaudeNotFoundError,
    build_claude_command,
    detect_generated_files,
    find_claude_binary,
    load_skill_content,
    prepare_idea_file,
)
from tc.tui.onboarding.state import WizardState
from tc.tui.onboarding.widgets.step_indicator import StepIndicator


class PrdFileScreen(Screen[None]):
    """Third screen: PRD file path input or generation via Claude."""

    BINDINGS = [
        Binding("escape", "go_back", "Back", show=True),
    ]

    def __init__(self, state: WizardState) -> None:
        super().__init__()
        self._state = state

    def compose(self) -> ComposeResult:
        with Vertical(classes="wizard-card"):
            indicator = StepIndicator()
            indicator.current_step = 2
            yield indicator
            yield Static("PRD File", classes="wizard-title")
            yield Static(
                "Product Requirements Document",
                classes="wizard-subtitle",
            )

            # Section 1: Choice (initial view)
            with Vertical(id="prd-choice"):
                yield Static(
                    "How would you like to provide a PRD?",
                    classes="wizard-label",
                )
                yield OptionList(
                    Option("I have a PRD", id="choose-manual"),
                    Option("Generate one", id="choose-generate"),
                    id="prd-options",
                    classes="wizard-options",
                )

            # Section 2: Manual path entry
            with Vertical(id="prd-manual"):
                yield Static("PRD File Path", classes="wizard-label")
                yield Input(
                    value=self._state.prd_path,
                    placeholder="/path/to/prd.md",
                    id="prd-input",
                    classes="wizard-input",
                )
                yield Static("", id="prd-error", classes="wizard-error")
                yield Static(
                    "Markdown file (.md) describing your project requirements",
                    classes="wizard-hint",
                )
                with Horizontal(classes="wizard-buttons"):
                    yield Button(
                        "Back",
                        id="manual-back-btn",
                        classes="wizard-btn-secondary",
                    )
                    yield Button(
                        "Next",
                        id="manual-next-btn",
                        classes="wizard-btn-primary",
                    )

            # Section 3: Generate via Claude
            with Vertical(id="prd-generate"):
                yield Static(
                    "Describe your project idea:",
                    classes="wizard-label",
                )
                yield TextArea(
                    id="idea-textarea",
                    classes="wizard-textarea",
                )
                yield Static("", id="generate-error", classes="wizard-error")
                yield Static(
                    "Claude will ask questions about your project, "
                    "then generate prd.md and bootstrap.md.",
                    classes="wizard-hint",
                )
                with Horizontal(classes="wizard-buttons"):
                    yield Button(
                        "Back",
                        id="generate-back-btn",
                        classes="wizard-btn-secondary",
                    )
                    yield Button(
                        "Generate",
                        id="generate-btn",
                        classes="wizard-btn-primary",
                    )

            # Bottom nav for the choice screen
            with Horizontal(id="prd-choice-nav", classes="wizard-buttons"):
                yield Button(
                    "Back",
                    id="back-btn",
                    classes="wizard-btn-secondary",
                )

    def on_mount(self) -> None:
        self._show_section("choice")
        self.query_one("#prd-options", OptionList).focus()

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        if event.option_id == "choose-manual":
            self._show_section("manual")
            self.query_one("#prd-input", Input).focus()
        elif event.option_id == "choose-generate":
            self._show_section("generate")
            self.query_one("#idea-textarea", TextArea).focus()

    def _show_section(self, section: str) -> None:
        """Toggle visibility of choice / manual / generate sections."""
        choice = self.query_one("#prd-choice")
        manual = self.query_one("#prd-manual")
        generate = self.query_one("#prd-generate")
        choice_nav = self.query_one("#prd-choice-nav")

        choice.display = section == "choice"
        choice_nav.display = section == "choice"
        manual.display = section == "manual"
        generate.display = section == "generate"

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "prd-input":
            self._advance_manual()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "prd-input":
            error = self.query_one("#prd-error", Static)
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
        btn_id = event.button.id
        if btn_id == "back-btn":
            self.action_go_back()
        elif btn_id == "manual-back-btn":
            self._show_section("choice")
            self.query_one("#prd-options", OptionList).focus()
        elif btn_id == "manual-next-btn":
            self._advance_manual()
        elif btn_id == "generate-back-btn":
            self._show_section("choice")
            self.query_one("#prd-options", OptionList).focus()
        elif btn_id == "generate-btn":
            self._advance_generate()

    def _advance_manual(self) -> None:
        """Advance using manually entered PRD path."""
        val = self.query_one("#prd-input", Input).value.strip()
        error = self.query_one("#prd-error", Static)

        if not val:
            error.update("PRD file path is required")
            error.add_class("visible")
            return

        p = Path(val)
        if not p.exists() or not p.is_file():
            return

        self._state.prd_path = val
        self._state.prd_generated = False
        self._state.current_step = 3
        self.app.push_screen("bootstrap_file")

    def _advance_generate(self) -> None:
        """Generate PRD via Claude CLI."""
        idea_text = self.query_one("#idea-textarea", TextArea).text
        error = self.query_one("#generate-error", Static)

        if not idea_text.strip():
            error.update("Please describe your project idea")
            error.add_class("visible")
            return

        # Check claude binary exists
        try:
            claude_bin = find_claude_binary()
        except ClaudeNotFoundError:
            error.update("claude CLI not found on PATH")
            error.add_class("visible")
            return

        error.remove_class("visible")

        project_dir = Path(self._state.project_dir)

        # Write idea.txt
        try:
            prepare_idea_file(project_dir, idea_text)
        except (FileNotFoundError, ValueError) as exc:
            error.update(str(exc))
            error.add_class("visible")
            return

        # Load the prd-generation skill and inject it into the system prompt
        skill_content = load_skill_content()
        cmd = build_claude_command(
            claude_bin,
            prompt="Read idea.txt and follow the PRD generation workflow above.",
            system_prompt=skill_content,
        )

        # Suspend TUI and run claude interactively
        with self.app.suspend():
            try:
                subprocess.run(
                    cmd,
                    cwd=str(project_dir),
                    timeout=3600,
                    shell=False,
                )
            except subprocess.TimeoutExpired:
                pass
            except OSError:
                pass

        # Detect generated files
        result = detect_generated_files(project_dir)

        if result.prd_found:
            self._state.prd_path = result.prd_path  # type: ignore[assignment]
            self._state.prd_generated = True
            if result.bootstrap_found:
                self._state.bootstrap_path = result.bootstrap_path  # type: ignore[assignment]
            self._state.current_step = 3
            self.app.push_screen("bootstrap_file")
        else:
            error.update(
                "No prd.md found after generation. Try again or use manual path."
            )
            error.add_class("visible")

    def action_go_back(self) -> None:
        self.app.pop_screen()
