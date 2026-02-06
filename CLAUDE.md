# Terminal Coder

## Build/Test Commands
- Install: `pip install -e ".[dev]"`
- Test: `pytest`
- Test with coverage: `pytest --cov=tc --cov-report=term-missing`
- Lint: `ruff check src/ tests/`
- Type check: `mypy src/tc/`
- Format: `ruff format src/ tests/`

## Code Style
- Python 3.11+, strict mypy
- Frozen dataclasses for all models (immutability)
- No emoji in code or comments
- 200-400 lines per file, 800 max
- Type hints on all public functions
- core/ module has ZERO I/O dependencies (pure logic)

## Architecture
- `core/` - Pure domain logic, no I/O, no imports from other tc modules except config
- `db/` - SQLite layer, repository pattern
- `orchestrator/` - Composes core + I/O (tmux, db, mcp)
- `cli/` - Typer commands, thin wrappers around orchestrator
- `tui/` - Textual dashboard, subscribes to events
- `mcp/` - MCP server for Claude Code session communication
- `tmux/` - libtmux wrapper for pane management
- `planning/` - PRD decomposition via Claude Code
- `bootstrap/` - Bootstrap.md verification
- `templates/` - Jinja2 task brief templates

## Testing
- TDD: write tests first
- 80% coverage minimum on core/ and db/
- Unit tests mock I/O boundaries
- Integration tests use real SQLite (in-memory)
