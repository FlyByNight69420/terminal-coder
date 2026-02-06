"""Tests for bootstrap.md parser."""

from __future__ import annotations

from pathlib import Path

from tc.bootstrap.parser import BUILTIN_CHECKS, Check, parse_bootstrap


class TestParseBootstrap:
    def test_parse_sample_bootstrap(self, fixtures_dir: Path) -> None:
        bootstrap_path = fixtures_dir / "sample_bootstrap.md"
        checks = parse_bootstrap(bootstrap_path)

        # Should have tool checks + credential checks + env checks + builtins
        assert len(checks) > len(BUILTIN_CHECKS)

        names = [c.name for c in checks]
        types = [c.check_type for c in checks]

        # Tool prerequisites
        assert "node.js_20+" in names or "node" in names
        assert "tool" in types

        # Credential checks
        assert "credential" in types

        # Builtin checks should be present
        assert "claude" in names
        assert "tmux" in names
        assert "git" in names

    def test_parses_tool_prerequisites(self, fixtures_dir: Path) -> None:
        bootstrap_path = fixtures_dir / "sample_bootstrap.md"
        checks = parse_bootstrap(bootstrap_path)

        tool_checks = [c for c in checks if c.check_type == "tool" and c not in BUILTIN_CHECKS]
        commands = [c.command for c in tool_checks]

        assert "node --version" in commands
        assert "pnpm --version" in commands
        assert "docker info" in commands

    def test_parses_credential_checks(self, fixtures_dir: Path) -> None:
        bootstrap_path = fixtures_dir / "sample_bootstrap.md"
        checks = parse_bootstrap(bootstrap_path)

        cred_checks = [c for c in checks if c.check_type == "credential"]
        commands = [c.command for c in cred_checks]

        assert "gh auth status" in commands
        assert "pg_isready -h localhost" in commands

    def test_parses_env_checks(self, fixtures_dir: Path) -> None:
        bootstrap_path = fixtures_dir / "sample_bootstrap.md"
        checks = parse_bootstrap(bootstrap_path)

        env_checks = [c for c in checks if c.check_type == "env"]
        names = [c.name for c in env_checks]

        assert "env_database_url" in names
        assert "env_api_key" in names
        assert "env_node_env" in names

    def test_builtin_checks_always_present(self, fixtures_dir: Path) -> None:
        bootstrap_path = fixtures_dir / "sample_bootstrap.md"
        checks = parse_bootstrap(bootstrap_path)

        builtin_names = {c.name for c in BUILTIN_CHECKS}
        check_names = {c.name for c in checks}

        assert builtin_names.issubset(check_names)


class TestParseMinimalBootstrap:
    def test_empty_bootstrap(self, tmp_path: Path) -> None:
        bootstrap = tmp_path / "bootstrap.md"
        bootstrap.write_text("# Empty Bootstrap\n\nNo checks here.\n")

        checks = parse_bootstrap(bootstrap)
        # Should still have builtins
        assert len(checks) == len(BUILTIN_CHECKS)
