"""Wizard state management for the onboarding flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class WizardResult:
    """Immutable result produced when the wizard completes."""

    project_dir: Path
    project_name: str
    prd_path: Path
    bootstrap_path: Path | None


class ValidationError(Exception):
    """Raised when wizard state fails validation."""


@dataclass
class WizardState:
    """Mutable state accumulated across wizard screens.

    Each screen writes its values here. On the review screen
    the state is validated and converted to a frozen WizardResult.
    """

    project_dir: str = ""
    project_name: str = ""
    prd_path: str = ""
    bootstrap_path: str = ""
    prd_generated: bool = False

    # Track which step the user is on (0-indexed)
    current_step: int = 0

    TOTAL_STEPS: int = field(default=7, init=False, repr=False)

    def validate(self) -> list[str]:
        """Return a list of validation error messages (empty means valid)."""
        errors: list[str] = []

        if not self.project_dir.strip():
            errors.append("Project directory is required.")
        else:
            p = Path(self.project_dir)
            if not p.is_absolute():
                errors.append("Project directory must be an absolute path.")
            elif not p.exists():
                errors.append(f"Project directory does not exist: {p}")
            elif not p.is_dir():
                errors.append(f"Path is not a directory: {p}")

        if not self.project_name.strip():
            errors.append("Project name is required.")

        if not self.prd_path.strip():
            errors.append("PRD file path is required.")
        else:
            prd = Path(self.prd_path)
            if not prd.exists():
                errors.append(f"PRD file does not exist: {prd}")
            elif not prd.is_file():
                errors.append(f"PRD path is not a file: {prd}")

        if self.bootstrap_path.strip():
            bp = Path(self.bootstrap_path)
            if not bp.exists():
                errors.append(f"Bootstrap file does not exist: {bp}")
            elif not bp.is_file():
                errors.append(f"Bootstrap path is not a file: {bp}")

        return errors

    def to_result(self) -> WizardResult:
        """Convert to an immutable WizardResult.

        Raises:
            ValidationError: If the current state is invalid.
        """
        errors = self.validate()
        if errors:
            raise ValidationError("; ".join(errors))

        bootstrap = (
            Path(self.bootstrap_path).resolve()
            if self.bootstrap_path.strip()
            else None
        )

        return WizardResult(
            project_dir=Path(self.project_dir).resolve(),
            project_name=self.project_name.strip(),
            prd_path=Path(self.prd_path).resolve(),
            bootstrap_path=bootstrap,
        )
