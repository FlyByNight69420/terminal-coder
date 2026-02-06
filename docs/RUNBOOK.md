# Runbook

Operational guide for running and troubleshooting Terminal Coder projects.

## Normal Operations

### Starting a New Project

```bash
# 1. Initialize
tc init /path/to/project --prd prd.md --bootstrap bootstrap.md --name "my-project"

# 2. Verify environment
tc verify --project-dir /path/to/project
# Fix any failing checks before proceeding

# 3. Plan (decomposes PRD into phases/tasks)
tc plan --project-dir /path/to/project

# 4. Review the plan
tc status --project-dir /path/to/project

# 5. Run
tc run --project-dir /path/to/project
```

### Monitoring a Running Project

```bash
# From another terminal, launch read-only dashboard
tc dashboard --project-dir /path/to/project

# Or check status in CLI
tc status --project-dir /path/to/project

# View event history
tc history --project-dir /path/to/project --limit 20

# Watch TMUX session directly
tmux attach -t tc-my-project
```

### TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `P` | Pause orchestration |
| `R` | Resume orchestration |
| `K` | Kill active session |
| `A` | Toggle auto-scroll in log panel |
| `Q` | Quit dashboard |

### Pausing and Resuming

```bash
# Pause (finishes current task, stops scheduling new ones)
tc pause --project-dir /path/to/project

# Resume
tc resume --project-dir /path/to/project
```

## Failure Recovery

### Task Failed (Auto-Retry)

The engine automatically retries failed tasks once with the error context included in the retry brief. If the retry also fails, the engine pauses.

Check what happened:
```bash
tc history --project-dir /path/to/project --task <task-id>
tc status --project-dir /path/to/project
```

### Task Failed (After Retry)

When a task fails after retry, the engine pauses. Options:

```bash
# Option 1: Retry manually (resets retry count)
tc retry --task <task-id> --project-dir /path/to/project
tc resume --project-dir /path/to/project

# Option 2: Reset and re-run
tc reset --task <task-id> --project-dir /path/to/project
tc resume --project-dir /path/to/project

# Option 3: Skip the task
# (not yet implemented via CLI - manual DB update required)
```

### Phase Failed

Reset an entire phase and all its tasks:

```bash
tc reset --phase <phase-number> --project-dir /path/to/project
```

This resets all tasks in the phase to pending, clears error contexts and retry counts, and deletes associated sessions.

### Stuck Session

If a Claude Code session hangs:

```bash
# Graceful kill
tc kill --session <session-id> --project-dir /path/to/project

# Force kill
tc kill --session <session-id> --force --project-dir /path/to/project

# Kill all running sessions
tc kill --project-dir /path/to/project
```

### Re-Planning

If the plan needs changes:

```bash
tc plan --project-dir /path/to/project --replan
```

This re-runs the planning session and overwrites existing phases/tasks.

## Data and State

### Project Directory Layout

```
project/
  .tc/
    tc.db           # SQLite database (WAL mode)
    briefs/         # Generated task brief markdown files
    logs/           # Session logs and result JSON files
    plans/          # Raw plan JSON from planning session
  .mcp.json         # MCP server configuration for Claude Code
  CLAUDE.md         # Generated project coding standards
  prd.md            # Product requirements document
  bootstrap.md      # Bootstrap specification
```

### Database

SQLite with WAL mode. Tables:

| Table | Purpose |
|-------|---------|
| `projects` | Project metadata and status |
| `phases` | Ordered phases with status |
| `tasks` | Tasks within phases, with status and error context |
| `task_dependencies` | Task-to-task dependency edges |
| `sessions` | Claude Code session records (PID, pane, exit code) |
| `events` | Full event log (status changes, progress, errors) |
| `bootstrap_checks` | Bootstrap verification results |

### Inspecting State Directly

```bash
# SQLite CLI
sqlite3 /path/to/project/.tc/tc.db

# Useful queries
SELECT id, name, status FROM phases ORDER BY sequence;
SELECT id, name, status, retry_count, error_context FROM tasks ORDER BY sequence;
SELECT * FROM events ORDER BY created_at DESC LIMIT 20;
SELECT * FROM sessions WHERE status = 'running';
```

### Session Logs

Each Claude Code session produces:
- `.tc/logs/session-<uuid>.log` - Full stdout/stderr
- `.tc/logs/session-<uuid>-result.json` - Claude Code output file

## Common Issues

### "No project found"

The `.tc/` directory or `tc.db` doesn't exist. Run `tc init` first.

### Bootstrap verification fails

Fix the failing checks before running `tc plan` or `tc run`. Common causes:
- Missing tool (install it)
- Expired credentials (re-authenticate)
- Missing `.env` variables (populate them)

### TMUX session already exists

If `tc run` fails because the TMUX session `tc-<name>` already exists:

```bash
# Check if an old session is still running
tmux ls

# Kill it manually
tmux kill-session -t tc-<name>
```

### MCP server connection issues

The MCP server is started automatically by `tc run` and configured via `.mcp.json`. Verify the config:

```bash
cat /path/to/project/.mcp.json
```

It should point to the `tc mcp-server` command with the correct absolute project path.

### Engine deadlock

If the engine reports "deadlock" (nothing schedulable but tasks remain), check for circular dependencies or tasks stuck in invalid states:

```bash
tc status --project-dir /path/to/project --json
sqlite3 /path/to/project/.tc/tc.db "SELECT t.id, t.name, t.status, d.depends_on_id FROM tasks t LEFT JOIN task_dependencies d ON t.id = d.task_id WHERE t.status NOT IN ('completed', 'skipped')"
```

### Disk space

Session logs can accumulate. Clean up old logs:

```bash
ls -la /path/to/project/.tc/logs/
# Remove logs from completed sessions as needed
```
