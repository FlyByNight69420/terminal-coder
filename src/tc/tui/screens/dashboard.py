"""Main dashboard screen layout."""

from __future__ import annotations

from textual.screen import Screen
from textual.widgets import Footer, Header

from tc.tui.widgets.log_panel import LogPanel
from tc.tui.widgets.phase_tree import PhaseTree
from tc.tui.widgets.session_panel import SessionPanel
from tc.tui.widgets.status_bar import StatusBar


class DashboardScreen(Screen[None]):
    """Main dashboard with three-panel layout."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2 2;
        grid-columns: 2fr 3fr;
        grid-rows: 1fr 1fr;
    }

    #phase-tree {
        row-span: 2;
        border: solid $primary;
        padding: 0 1;
    }

    #session-panel {
        border: solid $secondary;
        padding: 0 1;
    }

    #log-panel {
        border: solid $accent;
        padding: 0 1;
    }
    """

    def compose(self):  # type: ignore[override]
        yield Header()
        yield PhaseTree()
        yield SessionPanel()
        yield LogPanel()
        yield StatusBar()
        yield Footer()
