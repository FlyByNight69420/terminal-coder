"""Shared test fixtures for Terminal Coder."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    return project_dir
