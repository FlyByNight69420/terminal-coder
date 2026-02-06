"""Parse bootstrap.md to extract verification checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    check_type: str
    command: str
    expected_output: str | None = None


# Always-on checks that tc adds regardless of bootstrap.md content
BUILTIN_CHECKS: tuple[Check, ...] = (
    Check(name="claude", check_type="tool", command="claude --version"),
    Check(name="tmux", check_type="tool", command="tmux -V"),
    Check(name="git", check_type="tool", command="git status"),
)


def parse_bootstrap(bootstrap_path: Path) -> list[Check]:
    """Parse a bootstrap.md file and extract verification checks."""
    content = bootstrap_path.read_text()
    checks: list[Check] = []

    checks.extend(_parse_tool_prerequisites(content))
    checks.extend(_parse_credential_checks(content))
    checks.extend(_parse_env_checks(content))
    checks.extend(BUILTIN_CHECKS)

    return checks


def _parse_tool_prerequisites(content: str) -> list[Check]:
    """Parse the Prerequisites table for tool verification commands.

    Looks for markdown tables with columns: Tool | Install | Verify
    """
    checks: list[Check] = []
    lines = content.split("\n")

    in_table = False
    header_indices: dict[str, int] = {}

    for line in lines:
        stripped = line.strip()

        # Detect table header row
        if "|" in stripped and not in_table:
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            lower_cells = [c.lower() for c in cells]
            if "tool" in lower_cells and "verify" in lower_cells:
                header_indices = {c: i for i, c in enumerate(lower_cells)}
                in_table = True
                continue

        # Skip separator row
        if in_table and re.match(r"^\|[\s\-:|]+\|$", stripped):
            continue

        # Parse data rows
        if in_table and "|" in stripped:
            cells = [c.strip() for c in stripped.split("|") if c.strip()]
            if len(cells) > max(header_indices.values(), default=0):
                tool_idx = header_indices.get("tool", 0)
                verify_idx = header_indices.get("verify", 2)
                tool_name = _strip_markdown(cells[tool_idx])
                verify_cmd = _strip_markdown(cells[verify_idx])
                if verify_cmd and verify_cmd != "-":
                    checks.append(Check(
                        name=tool_name.lower().replace(" ", "_"),
                        check_type="tool",
                        command=verify_cmd,
                    ))
            continue

        # End of table
        if in_table and "|" not in stripped and stripped:
            in_table = False

    return checks


def _parse_credential_checks(content: str) -> list[Check]:
    """Parse **Verify:** lines for credential connectivity checks."""
    checks: list[Check] = []
    pattern = re.compile(r"\*\*Verify:\*\*\s*`([^`]+)`")

    for match in pattern.finditer(content):
        command = match.group(1)
        # Derive a name from the command
        name = _derive_check_name(command)
        checks.append(Check(
            name=name,
            check_type="credential",
            command=command,
        ))

    return checks


def _parse_env_checks(content: str) -> list[Check]:
    """Parse .env variable references and generate existence checks."""
    checks: list[Check] = []
    # Match lines like: - `VAR_NAME` - description
    # or KEY=value patterns in code blocks
    pattern = re.compile(r"`([A-Z][A-Z0-9_]+)`")

    # Only look in .env-related sections
    in_env_section = False
    for line in content.split("\n"):
        lower = line.lower().strip()
        if ".env" in lower and any(kw in lower for kw in ("populate", "create", "variable", "environment", "config")):
            in_env_section = True
            continue
        if in_env_section and line.strip().startswith("#"):
            # New heading, end of env section
            in_env_section = False

        if in_env_section:
            for match in pattern.finditer(line):
                var_name = match.group(1)
                checks.append(Check(
                    name=f"env_{var_name.lower()}",
                    check_type="env",
                    command=f"env_check:{var_name}",
                    expected_output="set",
                ))

    return checks


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting like backticks, bold, etc."""
    text = text.strip("`")
    text = text.replace("**", "")
    return text.strip()


def _derive_check_name(command: str) -> str:
    """Derive a human-readable check name from a command."""
    words = command.split()
    if words:
        base = words[0].split("/")[-1]
        return f"credential_{base}"
    return "credential_check"
