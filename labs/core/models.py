"""Core data models for the Lab Framework."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ExerciseStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"
    TIMEOUT = "timeout"


class Difficulty(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class ResourceLimits:
    cpu_cores: float       # 0.5 - 4.0
    memory_mb: int         # 128 - 4096
    time_minutes: int      # 1 - 120


@dataclass
class LabModule:
    id: str
    name: str
    order: int
    prerequisites: list[str]
    session_time_limit_minutes: int
    resource_limits: ResourceLimits


@dataclass
class LabConfig:
    version: str
    modules: list[LabModule]
    endpoints: dict[str, str]
    max_concurrent_containers: int
    memory_ceiling_mb: int
    cpu_ceiling_cores: float


@dataclass
class ExerciseResult:
    status: ExerciseStatus
    output_logs: str
    execution_duration_seconds: float
    checks: list['CheckResult'] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class CheckResult:
    name: str
    passed: bool
    feedback: str
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class AssessmentResult:
    status: str            # "pass" | "fail"
    checks: list[CheckResult]
    feedback: str


@dataclass
class ProgressEntry:
    student_id: str
    module_name: str
    exercise_id: str
    timestamp: datetime
    result: ExerciseStatus


@dataclass
class SessionResult:
    session_id: str
    container_id: str
    module_id: str
    student_id: str
    started_at: datetime
    status: str            # "active" | "expired" | "completed"


@dataclass
class ValidationResult:
    step_name: str
    passed: bool
    message: str
    details: Optional[dict] = None


@dataclass
class ErrorResponse:
    error_code: str
    message: str
    details: Optional[dict] = None
    suggestion: Optional[str] = None
