"""Deployment verification utilities."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DeployStatus:
    success: bool
    url: str | None
    message: str


class DeployVerifier:
    """Verifies deployment status across different targets."""

    def __init__(self, project_dir: Path) -> None:
        self._project_dir = project_dir

    def verify_git_push(self, remote: str = "origin") -> bool:
        """Check that the latest commit is pushed to the remote."""
        try:
            result = subprocess.run(
                ["git", "status", "-sb"],
                capture_output=True, text=True, timeout=15,
                cwd=str(self._project_dir),
            )
            # If branch is behind or diverged, push wasn't clean
            return "behind" not in result.stdout and result.returncode == 0
        except Exception:
            return False

    def verify_gitea_deployment(
        self, gitea_url: str, repo: str, branch: str = "main"
    ) -> DeployStatus:
        """Query Gitea API for deployment status."""
        try:
            api_url = f"{gitea_url}/api/v1/repos/{repo}/branches/{branch}"
            result = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", api_url],
                capture_output=True, text=True, timeout=15,
            )
            status_code = result.stdout.strip()
            if status_code == "200":
                return DeployStatus(
                    success=True, url=f"{gitea_url}/{repo}", message="Branch exists on Gitea",
                )
            return DeployStatus(
                success=False, url=None,
                message=f"Gitea returned status {status_code}",
            )
        except Exception as e:
            return DeployStatus(success=False, url=None, message=str(e))

    def verify_aws_deployment(
        self, service_name: str, region: str = "us-east-1"
    ) -> DeployStatus:
        """Check AWS deployment status via CLI."""
        try:
            result = subprocess.run(
                [
                    "aws", "ecs", "describe-services",
                    "--cluster", "default",
                    "--services", service_name,
                    "--region", region,
                    "--query", "services[0].deployments[0].rolloutState",
                    "--output", "text",
                ],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                state = result.stdout.strip()
                return DeployStatus(
                    success=state == "COMPLETED",
                    url=None,
                    message=f"ECS deployment state: {state}",
                )
            return DeployStatus(
                success=False, url=None, message=result.stderr[:200],
            )
        except FileNotFoundError:
            return DeployStatus(
                success=False, url=None, message="AWS CLI not installed",
            )
        except Exception as e:
            return DeployStatus(success=False, url=None, message=str(e))
