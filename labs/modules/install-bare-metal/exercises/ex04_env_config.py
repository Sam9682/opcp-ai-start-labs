"""Exercise 04: Environment Configuration.

Guides the learner through configuring the deployment environment
using deploy.ini and env_setup.sh.
"""

import subprocess
from typing import Optional

from labs.templates.exercise_base import Exercise


REQUIRED_ENV_VARS = [
    "FLASK_SECRET_KEY",
    "POSTGRES_PASSWORD",
    "DOMAIN_URL",
    "ADMIN_EMAIL",
]

DEPLOY_INI_REQUIRED_SECTIONS = [
    "general",
    "database",
    "web",
]


class EnvConfigExercise(Exercise):
    """Configure deployment environment via deploy.ini and env_setup.sh."""

    @property
    def exercise_id(self) -> str:
        return "04_env_config"

    @property
    def name(self) -> str:
        return "Environment Configuration"

    @property
    def description(self) -> str:
        return (
            "Configure the platform deployment environment by editing "
            "deploy.ini and running env_setup.sh to validate prerequisites "
            "and generate environment files."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    @property
    def prerequisites(self) -> list[str]:
        return ["03_repo_clone"]

    def setup(self) -> None:
        """No setup required — learner configures the environment."""
        pass

    def execute(self, submission: dict) -> dict:
        """Verify environment configuration.

        Args:
            submission: Dict with keys:
                - deploy_ini_path: Path to deploy.ini file
                - deploy_ini_sections: List of sections found in deploy.ini
                - env_setup_exit_code: Exit code from running env_setup.sh
                - env_setup_output: Output from env_setup.sh
                - env_vars_set: List of environment variable names that are set
                - python_available: Whether Python 3.9+ is available (bool)
                - docker_available: Whether Docker is available (bool)
                - compose_available: Whether docker-compose v2 is available (bool)

        Returns:
            Dict with configuration verification results.
        """
        result = {
            "deploy_ini_exists": submission.get("deploy_ini_exists", False),
            "deploy_ini_sections": submission.get("deploy_ini_sections", []),
            "env_setup_exit_code": submission.get("env_setup_exit_code"),
            "env_setup_output": submission.get("env_setup_output", ""),
            "env_vars_set": submission.get("env_vars_set", []),
            "python_available": submission.get("python_available") if submission.get("python_available") is not None else self._check_python(),
            "docker_available": submission.get("docker_available") if submission.get("docker_available") is not None else self._check_docker(),
            "compose_available": submission.get("compose_available") if submission.get("compose_available") is not None else self._check_compose(),
        }

        # If no pre-supplied data, try to run env_setup.sh
        if result["env_setup_exit_code"] is None:
            clone_path = submission.get("clone_path", "/opt/ai-powered-store")
            exit_code, output = self._run_env_setup(clone_path)
            result["env_setup_exit_code"] = exit_code
            result["env_setup_output"] = output

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate environment configuration is complete and correct."""
        checks = []

        # Check deploy.ini exists
        ini_exists = result.get("deploy_ini_exists", False)
        checks.append({
            "name": "deploy_ini_exists",
            "passed": ini_exists,
            "feedback": (
                "deploy.ini configuration file is present."
                if ini_exists
                else "deploy.ini configuration file is missing. "
                     "Copy from deploy.ini.example and configure."
            ),
            "expected": "deploy.ini present",
            "actual": "present" if ini_exists else "MISSING",
        })

        # Check deploy.ini sections
        sections = set(result.get("deploy_ini_sections", []))
        for section in DEPLOY_INI_REQUIRED_SECTIONS:
            section_found = section in sections
            checks.append({
                "name": f"deploy_ini_section_{section}",
                "passed": section_found,
                "feedback": (
                    f"deploy.ini contains [{section}] section."
                    if section_found
                    else f"deploy.ini is missing [{section}] section. "
                         f"Add the [{section}] section with required parameters."
                ),
                "expected": f"[{section}] section present",
                "actual": f"[{section}] {'present' if section_found else 'MISSING'}",
            })

        # Check env_setup.sh ran successfully
        exit_code = result.get("env_setup_exit_code")
        setup_passed = exit_code == 0
        checks.append({
            "name": "env_setup_success",
            "passed": setup_passed,
            "feedback": (
                "env_setup.sh completed successfully."
                if setup_passed
                else f"env_setup.sh failed with exit code {exit_code}. "
                     f"Output: {result.get('env_setup_output', 'no output')}"
            ),
            "expected": "Exit code 0",
            "actual": f"Exit code {exit_code}" if exit_code is not None else "not run",
        })

        # Check Python 3.9+ available
        python_ok = result.get("python_available", False)
        checks.append({
            "name": "python_available",
            "passed": python_ok,
            "feedback": (
                "Python 3.9+ is available."
                if python_ok
                else "Python 3.9+ is not available. "
                     "Install with: sudo apt-get install -y python3"
            ),
            "expected": "Python >= 3.9",
            "actual": "available" if python_ok else "NOT available",
        })

        # Check Docker available
        docker_ok = result.get("docker_available", False)
        checks.append({
            "name": "docker_available",
            "passed": docker_ok,
            "feedback": (
                "Docker Engine is available."
                if docker_ok
                else "Docker Engine is not available. "
                     "Ensure Docker is installed and running."
            ),
            "expected": "Docker available",
            "actual": "available" if docker_ok else "NOT available",
        })

        # Check docker-compose v2 available
        compose_ok = result.get("compose_available", False)
        checks.append({
            "name": "compose_available",
            "passed": compose_ok,
            "feedback": (
                "docker-compose v2 is available."
                if compose_ok
                else "docker-compose v2 is not available. "
                     "Install with: sudo apt-get install -y docker-compose-plugin"
            ),
            "expected": "docker-compose v2 available",
            "actual": "available" if compose_ok else "NOT available",
        })

        # Check required environment variables
        env_vars = set(result.get("env_vars_set", []))
        for var in REQUIRED_ENV_VARS:
            var_set = var in env_vars
            checks.append({
                "name": f"env_var_{var.lower()}",
                "passed": var_set,
                "feedback": (
                    f"Environment variable {var} is set."
                    if var_set
                    else f"Missing environment variable: {var}. "
                         f"Set in deploy.ini or export in your shell."
                ),
                "expected": f"{var} set",
                "actual": f"{var} {'set' if var_set else 'NOT set'}",
            })

        return checks

    def teardown(self) -> None:
        """No teardown — configuration remains in place."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Copy deploy.ini.example to deploy.ini and fill in your values.",
            "Run './env_setup.sh' from the project root to validate prerequisites.",
            "Check env_setup.sh output for specific error messages.",
            "Ensure FLASK_SECRET_KEY is a random string (use: python3 -c 'import secrets; print(secrets.token_hex(32))').",
            "DOMAIN_URL should be the URL where you want to access the platform.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Configure the deployment environment:\n\n"
            "1. Copy the example configuration:\n"
            "   cp deploy.ini.example deploy.ini\n\n"
            "2. Edit deploy.ini with your settings:\n"
            "   - Set DOMAIN_URL to your server's hostname or IP\n"
            "   - Set POSTGRES_PASSWORD to a secure password\n"
            "   - Set FLASK_SECRET_KEY to a random string\n"
            "   - Set ADMIN_EMAIL to your email address\n\n"
            "3. Run the environment setup script:\n"
            "   chmod +x env_setup.sh && ./env_setup.sh\n\n"
            "4. Verify it completes with exit code 0:\n"
            "   echo $?\n"
        )

    # --- Private helper methods ---

    @staticmethod
    def _check_python() -> bool:
        """Check if Python 3.9+ is available."""
        try:
            result = subprocess.run(
                ["python3", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                version_str = result.stdout.strip().split()[-1]
                parts = version_str.split(".")
                major, minor = int(parts[0]), int(parts[1])
                return major >= 3 and minor >= 9
        except (subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError):
            pass
        return False

    @staticmethod
    def _check_docker() -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def _check_compose() -> bool:
        """Check if docker-compose v2 is available."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def _run_env_setup(clone_path: str) -> tuple[int, str]:
        """Run env_setup.sh and return (exit_code, output)."""
        try:
            result = subprocess.run(
                ["bash", f"{clone_path}/env_setup.sh"],
                capture_output=True, text=True, timeout=60,
                cwd=clone_path,
            )
            output = result.stdout + result.stderr
            return result.returncode, output.strip()
        except subprocess.TimeoutExpired:
            return -1, "env_setup.sh timed out after 60 seconds."
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            return -1, f"Failed to run env_setup.sh: {e}"
