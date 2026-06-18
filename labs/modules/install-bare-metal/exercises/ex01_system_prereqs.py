"""Exercise 01: System Prerequisites Verification.

Verifies that the target system meets the minimum requirements for
installing the AI-Powered-Store platform:
- Ubuntu 22.04 or 24.04 LTS
- Minimum 2 CPU cores
- Minimum 4 GB RAM
- Minimum 20 GB free disk space
"""

import subprocess
from typing import Optional

from labs.templates.exercise_base import Exercise


# Mapping of dependency names to Ubuntu install commands
DEPENDENCY_INSTALL_COMMANDS = {
    "curl": "sudo apt-get install -y curl",
    "git": "sudo apt-get install -y git",
    "wget": "sudo apt-get install -y wget",
    "ca-certificates": "sudo apt-get install -y ca-certificates",
    "gnupg": "sudo apt-get install -y gnupg",
    "lsb-release": "sudo apt-get install -y lsb-release",
}

REQUIRED_DEPENDENCIES = ["curl", "git", "wget", "ca-certificates", "gnupg", "lsb-release"]

SUPPORTED_VERSIONS = ("22.04", "24.04")
MIN_CPU_CORES = 2
MIN_RAM_GB = 4
MIN_DISK_GB = 20


class SystemPrereqsExercise(Exercise):
    """Verify system prerequisites for AI-Powered-Store installation."""

    @property
    def exercise_id(self) -> str:
        return "01_system_prereqs"

    @property
    def name(self) -> str:
        return "System Prerequisites Verification"

    @property
    def description(self) -> str:
        return (
            "Verify that the target Ubuntu system meets minimum hardware "
            "and software requirements for the AI-Powered-Store platform."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    def setup(self) -> None:
        """No setup required for prerequisite verification."""
        pass

    def execute(self, submission: dict) -> dict:
        """Collect system information for validation.

        The submission may contain pre-collected data (for testing) or
        the exercise will attempt to gather it from the live system.

        Args:
            submission: Optional dict with keys:
                - os_version: Ubuntu version string (e.g., "22.04")
                - cpu_cores: Number of CPU cores (int)
                - ram_gb: Available RAM in GB (float)
                - disk_free_gb: Free disk space in GB (float)
                - installed_packages: List of installed package names

        Returns:
            Dict with system information gathered or provided.
        """
        result = {}

        # Use provided values or attempt system detection
        result["os_version"] = submission.get("os_version") or self._detect_os_version()
        result["cpu_cores"] = submission.get("cpu_cores") or self._detect_cpu_cores()
        result["ram_gb"] = submission.get("ram_gb") or self._detect_ram_gb()
        result["disk_free_gb"] = submission.get("disk_free_gb") or self._detect_disk_free_gb()
        result["installed_packages"] = submission.get(
            "installed_packages"
        ) or self._detect_installed_packages()

        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate system meets all prerequisites.

        Returns per-check results with specific missing dependency
        information and installation commands when applicable.
        """
        checks = []

        # Check OS version
        os_version = result.get("os_version", "unknown")
        os_passed = os_version in SUPPORTED_VERSIONS
        checks.append({
            "name": "os_version_check",
            "passed": os_passed,
            "feedback": (
                f"Ubuntu {os_version} detected."
                if os_passed
                else f"Unsupported OS version: {os_version}. "
                     f"Required: Ubuntu {' or '.join(SUPPORTED_VERSIONS)} LTS."
            ),
            "expected": f"Ubuntu {' or '.join(SUPPORTED_VERSIONS)}",
            "actual": f"Ubuntu {os_version}",
        })

        # Check CPU cores
        cpu_cores = result.get("cpu_cores", 0)
        cpu_passed = cpu_cores >= MIN_CPU_CORES
        checks.append({
            "name": "cpu_cores_check",
            "passed": cpu_passed,
            "feedback": (
                f"{cpu_cores} CPU cores detected (minimum: {MIN_CPU_CORES})."
                if cpu_passed
                else f"Insufficient CPU cores: {cpu_cores}. "
                     f"Minimum required: {MIN_CPU_CORES} cores."
            ),
            "expected": f">= {MIN_CPU_CORES} cores",
            "actual": f"{cpu_cores} cores",
        })

        # Check RAM
        ram_gb = result.get("ram_gb", 0)
        ram_passed = ram_gb >= MIN_RAM_GB
        checks.append({
            "name": "ram_check",
            "passed": ram_passed,
            "feedback": (
                f"{ram_gb:.1f} GB RAM detected (minimum: {MIN_RAM_GB} GB)."
                if ram_passed
                else f"Insufficient RAM: {ram_gb:.1f} GB. "
                     f"Minimum required: {MIN_RAM_GB} GB."
            ),
            "expected": f">= {MIN_RAM_GB} GB",
            "actual": f"{ram_gb:.1f} GB",
        })

        # Check disk space
        disk_free_gb = result.get("disk_free_gb", 0)
        disk_passed = disk_free_gb >= MIN_DISK_GB
        checks.append({
            "name": "disk_space_check",
            "passed": disk_passed,
            "feedback": (
                f"{disk_free_gb:.1f} GB free disk space (minimum: {MIN_DISK_GB} GB)."
                if disk_passed
                else f"Insufficient disk space: {disk_free_gb:.1f} GB. "
                     f"Minimum required: {MIN_DISK_GB} GB."
            ),
            "expected": f">= {MIN_DISK_GB} GB",
            "actual": f"{disk_free_gb:.1f} GB",
        })

        # Check required dependencies
        installed = set(result.get("installed_packages", []))
        for dep in REQUIRED_DEPENDENCIES:
            dep_passed = dep in installed
            install_cmd = DEPENDENCY_INSTALL_COMMANDS.get(dep, f"sudo apt-get install -y {dep}")
            checks.append({
                "name": f"dependency_{dep}",
                "passed": dep_passed,
                "feedback": (
                    f"Dependency '{dep}' is installed."
                    if dep_passed
                    else f"Missing dependency: '{dep}'. "
                         f"Install with: {install_cmd}"
                ),
                "expected": f"{dep} installed",
                "actual": f"{dep} {'installed' if dep_passed else 'NOT installed'}",
            })

        return checks

    def teardown(self) -> None:
        """No teardown required for prerequisite verification."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Use 'lsb_release -rs' to check your Ubuntu version.",
            "Use 'nproc' to check available CPU cores.",
            "Use 'free -g' to check available RAM in GB.",
            "Use 'df -BG /' to check free disk space.",
            "Use 'dpkg -l <package>' to check if a package is installed.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Verify that your system meets the minimum requirements:\n"
            f"- Ubuntu {' or '.join(SUPPORTED_VERSIONS)} LTS\n"
            f"- At least {MIN_CPU_CORES} CPU cores\n"
            f"- At least {MIN_RAM_GB} GB RAM\n"
            f"- At least {MIN_DISK_GB} GB free disk space\n"
            f"- Required packages: {', '.join(REQUIRED_DEPENDENCIES)}\n\n"
            "Run the system checks and ensure all requirements are met "
            "before proceeding to Docker installation."
        )

    # --- Private helper methods for live system detection ---

    @staticmethod
    def _detect_os_version() -> str:
        """Detect Ubuntu version from the system."""
        try:
            result = subprocess.run(
                ["lsb_release", "-rs"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            return "unknown"

    @staticmethod
    def _detect_cpu_cores() -> int:
        """Detect number of CPU cores."""
        try:
            result = subprocess.run(
                ["nproc"],
                capture_output=True, text=True, timeout=5
            )
            return int(result.stdout.strip())
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            return 0

    @staticmethod
    def _detect_ram_gb() -> float:
        """Detect available RAM in GB."""
        try:
            result = subprocess.run(
                ["free", "-b"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if line.startswith("Mem:"):
                    total_bytes = int(line.split()[1])
                    return total_bytes / (1024 ** 3)
        except (subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError):
            pass
        return 0.0

    @staticmethod
    def _detect_disk_free_gb() -> float:
        """Detect free disk space in GB on root partition."""
        try:
            result = subprocess.run(
                ["df", "-B1", "/"],
                capture_output=True, text=True, timeout=5
            )
            lines = result.stdout.splitlines()
            if len(lines) >= 2:
                free_bytes = int(lines[1].split()[3])
                return free_bytes / (1024 ** 3)
        except (subprocess.SubprocessError, FileNotFoundError, ValueError, IndexError):
            pass
        return 0.0

    @staticmethod
    def _detect_installed_packages() -> list[str]:
        """Detect which required packages are installed."""
        installed = []
        for dep in REQUIRED_DEPENDENCIES:
            try:
                result = subprocess.run(
                    ["dpkg", "-l", dep],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and "ii" in result.stdout:
                    installed.append(dep)
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        return installed
