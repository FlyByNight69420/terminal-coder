# Contributing to Terminal Coder

## Environment Setup

```bash
# Clone and enter project
git clone <repo-url> terminal-coder
cd terminal-coder

# Create virtual environment (required - system Python will refuse pip install)
python3 -m venv .venv
. .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
tc --version
tc --help
```

### Requirements

- Python 3.11+
- TMUX (for integration testing with real sessions)
- Claude Code CLI (for end-to-end testing)

## Development Workflow

### Code Style

- Python 3.11+, strict mypy
- Frozen dataclasses for all domain models (immutability)
- No emoji in code or comments
- 200-400 lines per file, 800 max
- Type hints on all public functions
- `core/` module has zero I/O dependencies (pure logic)

### Available Commands

| Command | Description |
|---------|-------------|
| `pip install -e ".[dev]"` | Install package in editable mode with dev deps |
| `pytest` | Run all tests |
| `pytest --cov=tc --cov-report=term-missing` | Run tests with coverage report |
| `pytest tests/unit/` | Run unit tests only |
| `pytest tests/integration/` | Run integration tests only |
| `pytest -k test_name` | Run specific test |
| `ruff check src/ tests/` | Lint check |
| `ruff format src/ tests/` | Auto-format code |
| `mypy src/tc/` | Type check |

### Dependencies

**Runtime:**

| Package | Version | Purpose |
|---------|---------|---------|
| typer | >=0.12 | CLI framework |
| textual | >=0.80 | TUI dashboard |
| libtmux | >=0.37 | TMUX session management |
| mcp | >=1.0 | MCP server SDK |
| jinja2 | >=3.1 | Task brief templates |
| rich | >=13.0 | Terminal formatting |

**Dev:**

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.0 | Test framework |
| pytest-asyncio | >=0.23 | Async test support |
| pytest-cov | >=5.0 | Coverage reporting |
| ruff | >=0.4 | Linter and formatter |
| mypy | >=1.10 | Static type checker |

### Build System

Uses [Hatchling](https://hatch.pypa.io/) as the build backend. Source layout with packages under `src/tc/`.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/tc"]
```

## Testing

### Approach

- TDD: write tests first
- 80% coverage minimum on `core/` and `db/` modules
- Unit tests mock I/O boundaries (TMUX, subprocess, filesystem)
- Integration tests use real SQLite (in-memory via `:memory:`)

### Test Organization

```
tests/
  conftest.py           # Shared fixtures (fixtures_dir, tmp_project)
  unit/
    test_models.py      # Frozen dataclass immutability
    test_state_machine.py  # State transition validation
    test_bootstrap_parser.py  # Bootstrap.md parsing
    test_brief_renderer.py    # Jinja2 template rendering
    test_plan_parser.py       # Plan JSON parsing
    test_scheduler.py         # Task scheduling logic
    test_retry_policy.py      # Retry eligibility
    test_events.py            # Event bus pub/sub
    test_mcp_tools.py         # MCP tool handlers
    test_tui_widgets.py       # TUI widget rendering
  integration/
    test_db_repository.py   # Full CRUD with in-memory SQLite
    test_init_cmd.py        # tc init on temp directory
    test_verify_cmd.py      # Bootstrap verification
    test_full_flow.py       # End-to-end orchestration flow
  fixtures/
    sample_bootstrap.md     # Sample bootstrap specification
    sample_prd.md           # Sample PRD
    sample_plan.json        # Expected planning output
```

### Coverage by Module

| Module | Coverage | Notes |
|--------|----------|-------|
| `core/` | 95-100% | Pure logic, fully testable |
| `db/` | 94-100% | In-memory SQLite integration tests |
| `config/` | 100% | Simple constants and paths |
| `templates/` | 100% | Template rendering tests |
| `mcp/tools` | 91% | Tool handler unit tests |
| `bootstrap/` | 93-98% | Parser and verifier tests |
| `cli/` | 20-100% | Commands needing real TMUX/Claude are lower |
| `tui/` | 0-76% | Widget tests exist; full app requires terminal |
| `orchestrator/` | 0-76% | Engine requires real TMUX for full coverage |
| `tmux/` | 19-39% | Requires real TMUX sessions |

## Architecture Rules

1. **`core/` is pure** - No I/O imports, no database, no subprocess. Only depends on `config/`.
2. **Repository pattern** - All database access goes through `db.repository.Repository`.
3. **Frozen models** - All domain objects are `@dataclass(frozen=True)`. Write methods take parameters, not model instances.
4. **State machine validation** - All status transitions go through `core.state_machine.validate_transition()`.
5. **Event-driven communication** - Engine publishes events, TUI subscribes via `core.events.EventBus`.

## Git Workflow

- Conventional commits: `feat:`, `fix:`, `refactor:`, `docs:`, `test:`
- Test locally before committing
- Small, focused commits
