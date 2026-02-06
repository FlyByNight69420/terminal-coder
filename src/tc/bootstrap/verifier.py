"""Bootstrap verification orchestrator."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from tc.bootstrap.checks import CheckResult, run_check
from tc.bootstrap.parser import parse_bootstrap
from tc.db.repository import Repository


@dataclass(frozen=True)
class VerificationReport:
    total: int
    passed: int
    failed: int
    results: tuple[CheckResult, ...]


class BootstrapVerifier:
    """Orchestrates bootstrap verification checks."""

    def __init__(self, repository: Repository, project_dir: Path) -> None:
        self._repo = repository
        self._project_dir = project_dir

    def verify(self, project_id: str, bootstrap_path: Path) -> VerificationReport:
        """Run all bootstrap checks and store results."""
        checks = parse_bootstrap(bootstrap_path)
        results: list[CheckResult] = []

        for check in checks:
            result = run_check(check, self._project_dir)
            results.append(result)

            # Store in database
            self._repo.create_bootstrap_check(
                id=str(uuid.uuid4()),
                project_id=project_id,
                check_name=result.name,
                check_type=result.check_type,
                command=check.command,
                expected=check.expected_output,
                actual_output=result.stdout or result.stderr,
                passed=result.passed,
            )

        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed

        return VerificationReport(
            total=len(results),
            passed=passed,
            failed=failed,
            results=tuple(results),
        )
