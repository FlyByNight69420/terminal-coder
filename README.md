# Terminal Coder (`tc`)

Autonomous software building orchestrator using Claude Code. Takes a PRD and bootstrap specification, decomposes them into phases and tasks, then orchestrates Claude Code sessions via TMUX to build, review, deploy, and verify a software project.

## Quick Start

```bash
# Install
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# Initialize a project
tc init /path/to/project --prd prd.md --bootstrap bootstrap.md

# Verify environment (tools, credentials, env vars)
tc verify --project-dir /path/to/project

# Decompose PRD into phases and tasks
tc plan --project-dir /path/to/project

# Run orchestration (with TUI dashboard)
tc run --project-dir /path/to/project

# Run headless (no TUI)
tc run --project-dir /path/to/project --headless
```

## Requirements

- Python 3.11+
- TMUX
- Claude Code CLI (`claude`)
- Git

## CLI Commands

| Command | Description |
|---------|-------------|
| `tc init <dir> --prd <path>` | Initialize project, create `.tc/` directory and SQLite DB |
| `tc status [--json]` | Show phase/task summary table |
| `tc verify` | Run bootstrap connectivity checks |
| `tc plan [--replan]` | Decompose PRD into phases/tasks via Claude Code |
| `tc run [--headless]` | Start orchestration engine (with or without TUI) |
| `tc pause` | Pause orchestration (finish current task, stop scheduling) |
| `tc resume` | Resume paused orchestration |
| `tc retry --task <id>` | Retry a failed or paused task |
| `tc kill [--session <id>]` | Kill a running Claude Code session |
| `tc dashboard` | Launch read-only TUI dashboard |
| `tc history [--task <id>]` | Show event history |
| `tc reset --task <id>` | Reset task or phase to pending |

All commands accept `--project-dir <path>` (defaults to current directory).

## Architecture

```
PRD + Bootstrap --> tc plan --> Phases/Tasks in SQLite
                                     |
                              tc run (engine loop)
                                     |
                    +----------------+----------------+
                    |                                 |
              TMUX Pane 0                       TMUX Pane 1
              (coding tasks)                    (review tasks)
                    |                                 |
              Claude Code                       Claude Code
              session                           session
                    |                                 |
                    +---------> MCP Server <----------+
                              (6 tools for
                               progress/completion
                               reporting)
```

### Module Layout

| Module | Purpose |
|--------|---------|
| `core/` | Pure domain logic (enums, models, state machine, scheduler) - zero I/O |
| `db/` | SQLite with WAL mode, repository pattern |
| `cli/` | Typer commands, thin wrappers |
| `orchestrator/` | Engine loop, session management, review coordination |
| `tmux/` | libtmux wrapper for 2-pane management |
| `mcp/` | MCP server with 6 tools for session communication |
| `tui/` | Textual live dashboard |
| `planning/` | PRD decomposition via Claude Code |
| `templates/` | Jinja2 task brief templates (.j2) |
| `bootstrap/` | Bootstrap.md parsing and verification |
| `config/` | Constants and path settings |

### Orchestration Loop

The engine polls every 2 seconds:

1. Check active sessions for exit (completion or failure)
2. Handle completions: mark task done, update phase, schedule code review
3. Handle failures: retry once with error context, then pause
4. Dispatch queued review to pane 1 (if free)
5. Dispatch next coding task to pane 0 (if free and not paused)
6. Detect completion (all tasks done) or deadlock

### MCP Tools

Sessions communicate back to the orchestrator via these MCP tools:

| Tool | Purpose |
|------|---------|
| `tc_report_progress` | Report task progress with optional percentage |
| `tc_report_completion` | Mark task complete with summary and files changed |
| `tc_report_failure` | Report failure with error details |
| `tc_report_review` | Submit review verdict and findings |
| `tc_get_context` | Retrieve context about completed work |
| `tc_request_human_input` | Request human decision via TUI |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=tc --cov-report=term-missing

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/tc/
```

## Project Structure

```
terminal-coder/
  src/tc/
    cli/commands/     # 12 CLI command handlers
    core/             # Enums, models, state machine, scheduler, events
    db/               # Schema, queries, repository, connection
    orchestrator/     # Engine, session manager, review coordinator
    tmux/             # TMUX pane manager and monitor
    mcp/              # MCP server and 6 tool handlers
    tui/              # Textual dashboard (widgets, screens, styles)
    planning/         # PRD planner, plan parser, CLAUDE.md generator
    templates/        # 5 Jinja2 brief templates
    bootstrap/        # Bootstrap parser, checks, verifier
    config/           # Constants, path settings
  tests/
    unit/             # 11 unit test files
    integration/      # 4 integration test files
    fixtures/         # Sample PRD, bootstrap, plan JSON
  docs/               # Documentation
```

## License

Proprietary.
