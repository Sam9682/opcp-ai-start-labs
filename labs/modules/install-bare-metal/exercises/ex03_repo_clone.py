"""Exercise 03: Repository Cloning.

Guides the learner through cloning the AI-Powered-Store platform
repository and verifying the expected directory structure.
"""

import subprocess
from typing import Optional

from labs.templates.exercise_base import Exercise


REQUIRED_FILES = [
    "docker-compose.yml",
    "Dockerfile",
    "requirements.txt",
    "app.py",
    "env_setup.sh",
    "README.md",
]

REQUIRED_DIRS = [
    "src",
    "labs",
    "skillhub",
    "nginx",
]

DEFAULT_REPO_URL = "https://forgejo.example.com/opcp/opcp-storeai.git"
DEFAULT_CLONE_PATH = "/opt/ai-powered-store"


class RepoCloneExercise(Exercise):
    """Clone the AI-Powered-Store platform repository."""

    @property
    def exercise_id(self) -> str:
        return "03_repo_clone"

    @property
    def name(self) -> str:
        return "Repository Cloning"

    @property
    def description(self) -> str:
        return (
            "Clone the AI-Powered-Store platform repository to the target "
            "directory and verify that all expected files and directories are present."
        )

    @property
    def timeout_minutes(self) -> int:
        return 10

    @property
    def prerequisites(self) -> list[str]:
        return ["02_docker_install"]

    def setup(self) -> None:
        """No setup required — learner performs the clone."""
        pass

    def execute(self, submission: dict) -> dict:
        """Verify the cloned repository structure.

        Args:
            submission: Dict with keys:
                - clone_path: Path where the repository was cloned
                - repo_url: (optional) Repository URL that was cloned
                - files_present: (optional) List of files found at clone_path
                - dirs_present: (optional) List of directories found at clone_path

        Returns:
            Dict with verification results.
        """
        clone_path = submission.get("clone_path", DEFAULT_CLONE_PATH)
        repo_url = submission.get("repo_url", DEFAULT_REPO_URL)

        result = {
            "clone_path": clone_path,
            "repo_url": repo_url,
            "files_present": submission.get("files_present") or self._check_files(clone_path),
            "dirs_present": submission.get("dirs_present") or self._check_dirs(clone_path),
            "is_git_repo": submission.get("is_git_repo") if submission.get("is_git_repo") is not None else self._is_git_repo(clone_path),
        }
        return result

    def validate(self, result: dict) -> list[dict]:
        """Validate that the repository was cloned correctly."""
        checks = []

        # Check it's a git repository
        is_git = result.get("is_git_repo", False)
        checks.append({
            "name": "is_git_repository",
            "passed": is_git,
            "feedback": (
                f"Directory '{result.get('clone_path')}' is a valid git repository."
                if is_git
                else f"Directory '{result.get('clone_path')}' is not a git repository. "
                     f"Clone with: git clone {result.get('repo_url', DEFAULT_REPO_URL)} {result.get('clone_path', DEFAULT_CLONE_PATH)}"
            ),
            "expected": "Valid git repository",
            "actual": "git repo" if is_git else "not a git repo",
        })

        # Check required files
        files_present = set(result.get("files_present", []))
        for req_file in REQUIRED_FILES:
            file_found = req_file in files_present
            checks.append({
                "name": f"file_{req_file.replace('.', '_').replace('/', '_')}",
                "passed": file_found,
                "feedback": (
                    f"Required file '{req_file}' is present."
                    if file_found
                    else f"Missing required file: '{req_file}'. "
                         f"Ensure the repository was cloned completely."
                ),
                "expected": f"{req_file} present",
                "actual": f"{req_file} {'present' if file_found else 'MISSING'}",
            })

        # Check required directories
        dirs_present = set(result.get("dirs_present", []))
        for req_dir in REQUIRED_DIRS:
            dir_found = req_dir in dirs_present
            checks.append({
                "name": f"dir_{req_dir}",
                "passed": dir_found,
                "feedback": (
                    f"Required directory '{req_dir}/' is present."
                    if dir_found
                    else f"Missing required directory: '{req_dir}/'. "
                         f"Ensure the repository was cloned completely."
                ),
                "expected": f"{req_dir}/ present",
                "actual": f"{req_dir}/ {'present' if dir_found else 'MISSING'}",
            })

        return checks

    def teardown(self) -> None:
        """No teardown — cloned repository remains."""
        pass

    def get_hints(self) -> list[str]:
        return [
            f"Use 'git clone {DEFAULT_REPO_URL} {DEFAULT_CLONE_PATH}' to clone the repo.",
            "Use 'ls' to verify files and directories are present.",
            "If git clone fails, check your network connectivity and git credentials.",
            "Ensure you have write permissions to the target directory.",
        ]

    def get_instructions(self) -> Optional[str]:
        return (
            "Clone the AI-Powered-Store platform repository:\n\n"
            f"1. Clone the repository:\n"
            f"   git clone {DEFAULT_REPO_URL} {DEFAULT_CLONE_PATH}\n\n"
            f"2. Navigate to the cloned directory:\n"
            f"   cd {DEFAULT_CLONE_PATH}\n\n"
            "3. Verify the directory structure:\n"
            "   ls -la\n\n"
            "Expected files: " + ", ".join(REQUIRED_FILES) + "\n"
            "Expected directories: " + ", ".join(f"{d}/" for d in REQUIRED_DIRS) + "\n"
        )

    # --- Private helper methods ---

    @staticmethod
    def _check_files(clone_path: str) -> list[str]:
        """Check which required files exist in the clone path."""
        found = []
        for filename in REQUIRED_FILES:
            try:
                result = subprocess.run(
                    ["test", "-f", f"{clone_path}/{filename}"],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    found.append(filename)
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        return found

    @staticmethod
    def _check_dirs(clone_path: str) -> list[str]:
        """Check which required directories exist in the clone path."""
        found = []
        for dirname in REQUIRED_DIRS:
            try:
                result = subprocess.run(
                    ["test", "-d", f"{clone_path}/{dirname}"],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    found.append(dirname)
            except (subprocess.SubprocessError, FileNotFoundError):
                pass
        return found

    @staticmethod
    def _is_git_repo(clone_path: str) -> bool:
        """Check if the path is a valid git repository."""
        try:
            result = subprocess.run(
                ["git", "-C", clone_path, "rev-parse", "--git-dir"],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
