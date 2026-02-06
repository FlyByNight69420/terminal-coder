"""Execute bootstrap verification checks."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from tc.bootstrap.parser import Check


@dataclass(frozen=True)
class CheckResult:
    name: str
    check_type: str
    passed: bool
    stdout: str
    stderr: str
    exit_code: int


def run_check(check: Check, project_dir: Path, timeout: int = 30) -> CheckResult:
    """Run a single verification check and return the result."""
    if check.check_type == "env":
        return _run_env_check(check, project_dir)
    return _run_command_check(check, project_dir, timeout)


def _run_command_check(check: Check, project_dir: Path, timeout: int) -> CheckResult:
    """Run a shell command check."""
    try:
        result = subprocess.run(
            check.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(project_dir),
        )
        passed = result.returncode == 0
        return CheckResult(
            name=check.name,
            check_type=check.check_type,
            passed=passed,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=check.name,
            check_type=check.check_type,
            passed=False,
            stdout="",
            stderr=f"Command timed out after {timeout}s",
            exit_code=-1,
        )
    except Exception as e:
        return CheckResult(
            name=check.name,
            check_type=check.check_type,
            passed=False,
            stdout="",
            stderr=str(e),
            exit_code=-1,
        )


def _run_env_check(check: Check, project_dir: Path) -> CheckResult:
    """Check that an environment variable is set in the .env file."""
    # Extract variable name from command format: "env_check:VAR_NAME"
    var_name = check.command.split(":", 1)[1] if ":" in check.command else check.command

    env_file = project_dir / ".env"
    if not env_file.exists():
        return CheckResult(
            name=check.name,
            check_type=check.check_type,
            passed=False,
            stdout="",
            stderr=".env file not found",
            exit_code=1,
        )

    content = env_file.read_text()
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == var_name and value.strip():
            return CheckResult(
                name=check.name,
                check_type=check.check_type,
                passed=True,
                stdout=f"{var_name}=<set>",
                stderr="",
                exit_code=0,
            )

    return CheckResult(
        name=check.name,
        check_type=check.check_type,
        passed=False,
        stdout="",
        stderr=f"{var_name} not found or empty in .env",
        exit_code=1,
    )
