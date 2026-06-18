"""Exercise 02: Docker Installation.

Guides the learner through installing Docker Engine and docker-compose v2
on an Ubuntu 22.04 or 24.04 system.
"""

import subprocess
from typing import Optional

from labs.templates.exercise_base import Exercise


DEPENDENCY_INSTALL_COMMANDS = {
    "docker": (
        "sudo apt-get update && "
        "sudo apt-get install -y ca-certificates curl gnupg && "
        "sudo install -m 0755 -d /etc/apt/keyrings && "
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | "
        "sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg && "
        "sudo chmod a+r /etc/apt/keyrings/docker.gpg && "
        'echo "deb [arch=$(dpkg --print-architecture) '
        "signed-by=/etc/apt/keyrings/docker.gpg] "
        "https://download.docker.com/linux/ubuntu "
        '$(. /etc/os-release && echo $VERSION_CODENAME) stable" | '
        "sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && "
        "sudo apt-get update && "
        "sudo apt-get install -y docker-ce docker-ce-cli containerd.io "
        "docker-buildx-plugin docker-compose-plugin"
    ),
    "docker-compose": (
        "sudo apt-get install -y docker-compose-plugin"
    ),
}

MIN_DOCKER_VERSION = "20.10"
MIN_COMPOSE_VERSION = "2.0"


class DockerInstallExercise(Exercise):
    """Install Docker Engine and docker-compose v2."""

    @property
    def exercise_id(self) -> str:
        return "02_docker_install"

    @property
    def name(self) -> str:
        return "Docker Installation"

    @property
    def description(self) -> str:
        return (
            "Install Docker Engine and docker-compose v2 on the Ubuntu system, "
            "verify the installation, and ensure the current user can run Docker commands."
        )

    @property
    def timeout_minutes(self) -> int:
        return 20

    @property
    def prerequisites(self) -> list[str]:
        return ["01_system_prereqs"]

    def setup(self) -> None:
        """No setup required — learner performs the installation."""
        pass

    def execute(self, submission: dict) -> dict:
        """Collect Docker installation status.

        Args:
            submission: Optional dict with keys:
                - docker_version: Docker Engine version string
                - compose_version: docker-compose version string
                - docker_running: Whether Docker daemon is running (bool)
                - user_in_docker_group: Whether current user is in docker group (bool)

        Returns:
            Dict with Docker installation information.
        """
        result = {}
        result["docker_version"] = submission.get("docker_version") or self._detect_docker_version()
        result["compose_version"] = submission.get("compose_version") or self._detect_compose_version()
        result["docker_running"] = submission.get("docker_running") if submission.get("docker_running") is not None else self._is_docker_running()
        result["user_in_docker_group"] = submission.get("user_in_docker_group") if submission.get("user_in_docker_group") is not None else self._is_user_in_docker_group()
        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate Docker installation meets requirements."""
        checks = []

        # Check Docker Engine installed
        docker_version = result.get("docker_version", "")
        docker_installed = bool(docker_version) and docker_version != "not_installed"
        checks.append({
            "name": "docker_installed",
            "passed": docker_installed,
            "feedback": (
                f"Docker Engine {docker_version} is installed."
                if docker_installed
                else f"Docker Engine is not installed. "
                     f"Install with: {DEPENDENCY_INSTALL_COMMANDS['docker']}"
            ),
            "expected": f"Docker Engine >= {MIN_DOCKER_VERSION}",
            "actual": docker_version or "not installed",
        })

        # Check docker-compose v2 installed
        compose_version = result.get("compose_version", "")
        compose_installed = bool(compose_version) and compose_version != "not_installed"
        compose_v2 = False
        if compose_installed:
            try:
                major = int(compose_version.split(".")[0])
                compose_v2 = major >= 2
            except (ValueError, IndexError):
                compose_v2 = False

        checks.append({
            "name": "compose_v2_installed",
            "passed": compose_v2,
            "feedback": (
                f"docker-compose v{compose_version} is installed."
                if compose_v2
                else f"docker-compose v2 is not installed (found: {compose_version or 'none'}). "
                     f"Install with: {DEPENDENCY_INSTALL_COMMANDS['docker-compose']}"
            ),
            "expected": f"docker-compose >= {MIN_COMPOSE_VERSION}",
            "actual": compose_version or "not installed",
        })

        # Check Docker daemon running
        docker_running = result.get("docker_running", False)
        checks.append({
            "name": "docker_daemon_running",
            "passed": docker_running,
            "feedback": (
                "Docker daemon is running."
                if docker_running
                else "Docker daemon is not running. "
                     "Start with: sudo systemctl start docker"
            ),
            "expected": "Docker daemon running",
            "actual": "running" if docker_running else "not running",
        })

        # Check user in docker group
        user_in_group = result.get("user_in_docker_group", False)
        checks.append({
            "name": "user_docker_group",
            "passed": user_in_group,
            "feedback": (
                "Current user is in the docker group."
                if user_in_group
                else "Current user is not in the docker group. "
                     "Add with: sudo usermod -aG docker $USER (then re-login)"
            ),
            "expected": "User in docker group",
            "actual": "in group" if user_in_group else "not in group",
        })

        return checks

    def teardown(self) -> None:
        """No teardown — Docker remains installed."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Follow the official Docker installation guide for Ubuntu.",
            "Use 'docker --version' to verify Docker Engine installation.",
            "Use 'docker compose version' to verify docker-compose v2.",
            "Use 'sudo systemctl status docker' to check if the daemon is running.",
            "After adding yourself to the docker group, log out and back in.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Install Docker Engine and docker-compose v2:\n\n"
            "1. Remove any old Docker packages:\n"
            "   sudo apt-get remove docker docker-engine docker.io containerd runc\n\n"
            "2. Set up the Docker repository and install:\n"
            "   Follow the official docs at https://docs.docker.com/engine/install/ubuntu/\n\n"
            "3. Verify installation:\n"
            "   docker --version\n"
            "   docker compose version\n\n"
            "4. Add your user to the docker group:\n"
            "   sudo usermod -aG docker $USER\n\n"
            "5. Start the Docker daemon:\n"
            "   sudo systemctl enable docker && sudo systemctl start docker\n"
        )

    # --- Private helper methods ---

    @staticmethod
    def _detect_docker_version() -> str:
        """Detect installed Docker Engine version."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Output like: Docker version 24.0.7, build afdd53b
                parts = result.stdout.strip().split()
                if len(parts) >= 3:
                    return parts[2].rstrip(",")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "not_installed"

    @staticmethod
    def _detect_compose_version() -> str:
        """Detect installed docker-compose version."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version", "--short"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip().lstrip("v")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return "not_installed"

    @staticmethod
    def _is_docker_running() -> bool:
        """Check if Docker daemon is running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def _is_user_in_docker_group() -> bool:
        """Check if current user is in the docker group."""
        try:
            result = subprocess.run(
                ["groups"],
                capture_output=True, text=True, timeout=5
            )
            return "docker" in result.stdout.split()
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
