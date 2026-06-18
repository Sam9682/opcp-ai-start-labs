"""Exercises for the install-bare-metal lab module.

Note: This module uses a hyphenated directory name for readability.
Use relative imports within the module, or import exercises directly
by their file paths via the framework's dynamic loader.
"""

from .ex01_system_prereqs import SystemPrereqsExercise
from .ex02_docker_install import DockerInstallExercise
from .ex03_repo_clone import RepoCloneExercise
from .ex04_env_config import EnvConfigExercise
from .ex05_platform_startup import PlatformStartupExercise

__all__ = [
    "SystemPrereqsExercise",
    "DockerInstallExercise",
    "RepoCloneExercise",
    "EnvConfigExercise",
    "PlatformStartupExercise",
]
