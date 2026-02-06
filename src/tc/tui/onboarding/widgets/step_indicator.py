"""Step indicator widget showing wizard progress."""

from __future__ import annotations

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget


class StepIndicator(Widget):
    """Displays wizard progress as connected dots.

    Completed: green filled circle
    Current:   blue filled circle
    Future:    dim open circle

    Example: completed=2, current=2, total=7
             green green blue dim dim dim dim
    """

    DEFAULT_CSS = """
    StepIndicator {
        height: 1;
        width: 100%;
        content-align: center middle;
    }
    """

    current_step: reactive[int] = reactive(0)
    total_steps: reactive[int] = reactive(7)

    STEP_LABELS = [
        "Welcome",
        "Project",
        "PRD",
        "Bootstrap",
        "Review",
        "Init",
        "Done",
    ]

    def render(self) -> Text:
        parts = Text()
        for i in range(self.total_steps):
            if i > 0:
                connector_style = (
                    "green" if i <= self.current_step else "dim"
                )
                parts.append(" -- ", style=connector_style)

            if i < self.current_step:
                # Completed
                parts.append("*", style="bold green")
            elif i == self.current_step:
                # Current
                parts.append("@", style="bold cyan")
            else:
                # Future
                parts.append("o", style="dim")

        # Add current step label
        if 0 <= self.current_step < len(self.STEP_LABELS):
            label = self.STEP_LABELS[self.current_step]
            parts.append(f"  {label}", style="bold")

        return parts
