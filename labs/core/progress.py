"""Server-side progress tracking with JSON persistence."""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Optional

from labs.core.models import ExerciseStatus, ProgressEntry


class ProgressTracker:
    """Persists exercise completion state server-side in a JSON file.

    Storage schema:
    {
        "students": {
            "<student_id>": {
                "modules": {
                    "<module_name>": {
                        "exercises": {
                            "<exercise_id>": {
                                "timestamp": "2025-01-15T10:30:00+00:00",
                                "result": "pass"
                            }
                        },
                        "completed": false
                    }
                }
            }
        }
    }
    """

    def __init__(self, storage_path: str) -> None:
        """Initialize the progress tracker.

        Args:
            storage_path: Path to the JSON file used for persistence.
        """
        self._storage_path = storage_path
        self._lock = threading.Lock()
        self._data = self._load()

    def _load(self) -> dict:
        """Load progress data from disk, or return empty structure."""
        if os.path.exists(self._storage_path):
            try:
                with open(self._storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "students" in data:
                        return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"students": {}}

    def _save(self) -> None:
        """Persist the current data to disk."""
        directory = os.path.dirname(self._storage_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def record_completion(
        self,
        student_id: str,
        module_name: str,
        exercise_id: str,
        result: str,
    ) -> None:
        """Record an exercise attempt with timestamp.

        Args:
            student_id: Unique identifier for the student.
            module_name: Name/id of the module the exercise belongs to.
            exercise_id: Unique identifier for the exercise within the module.
            result: Outcome of the exercise attempt ("pass" or "fail").
        """
        with self._lock:
            students = self._data["students"]

            if student_id not in students:
                students[student_id] = {"modules": {}}

            modules = students[student_id]["modules"]

            if module_name not in modules:
                modules[module_name] = {"exercises": {}, "completed": False}

            module_data = modules[module_name]
            module_data["exercises"][exercise_id] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result,
            }

            # Update module completed status: true iff all exercises have result "pass"
            exercises = module_data["exercises"]
            module_data["completed"] = (
                len(exercises) > 0
                and all(ex["result"] == "pass" for ex in exercises.values())
            )

            self._save()

    def get_progress(
        self, student_id: str, module_name: Optional[str] = None
    ) -> list[ProgressEntry]:
        """Retrieve progress records, optionally filtered by module.

        Args:
            student_id: Unique identifier for the student.
            module_name: If provided, only return entries for this module.

        Returns:
            List of ProgressEntry records matching the query.
        """
        with self._lock:
            students = self._data.get("students", {})

            if student_id not in students:
                return []

            modules = students[student_id].get("modules", {})
            entries: list[ProgressEntry] = []

            if module_name is not None:
                if module_name not in modules:
                    return []
                modules_to_check = {module_name: modules[module_name]}
            else:
                modules_to_check = modules

            for mod_name, mod_data in modules_to_check.items():
                for ex_id, ex_data in mod_data.get("exercises", {}).items():
                    timestamp = datetime.fromisoformat(ex_data["timestamp"])
                    result_str = ex_data["result"]
                    try:
                        result_status = ExerciseStatus(result_str)
                    except ValueError:
                        result_status = ExerciseStatus.ERROR

                    entries.append(
                        ProgressEntry(
                            student_id=student_id,
                            module_name=mod_name,
                            exercise_id=ex_id,
                            timestamp=timestamp,
                            result=result_status,
                        )
                    )

            return entries

    def is_module_complete(self, student_id: str, module_name: str) -> bool:
        """Check if all exercises in a module are passed.

        Args:
            student_id: Unique identifier for the student.
            module_name: Name/id of the module to check.

        Returns:
            True if the module has at least one exercise and all exercises
            have a "pass" result, False otherwise.
        """
        with self._lock:
            students = self._data.get("students", {})

            if student_id not in students:
                return False

            modules = students[student_id].get("modules", {})

            if module_name not in modules:
                return False

            return modules[module_name].get("completed", False)
