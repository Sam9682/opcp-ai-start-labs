"""Lab API routes for the AI Store Labs Flask application."""

import logging
from dataclasses import asdict
from datetime import timezone

from flask import Blueprint, jsonify, request

from labs.core.config_loader import ConfigLoader
from labs.core.credential_handler import CredentialHandler
from labs.core.models import ErrorResponse, ExerciseStatus
from labs.core.runner import (
    LabRunner,
    PrerequisiteError,
    SessionNotFoundError,
)

logger = logging.getLogger(__name__)

lab_routes = Blueprint('lab', __name__)

# Module-level runner instance (lazy-initialized)
_runner: LabRunner | None = None


def _get_runner() -> LabRunner:
    """Get or initialize the LabRunner singleton.

    Returns:
        The shared LabRunner instance.
    """
    global _runner
    if _runner is None:
        config_loader = ConfigLoader("labs/config/lab_config.yaml")
        config = config_loader.load()
        credential_handler = CredentialHandler()
        _runner = LabRunner(config=config, credential_handler=credential_handler)
    return _runner


def _error_response(error_code: str, message: str, status_code: int,
                    details: dict | None = None,
                    suggestion: str | None = None):
    """Build a JSON error response in ErrorResponse format.

    Args:
        error_code: Machine-readable error code.
        message: Human-readable description.
        status_code: HTTP status code to return.
        details: Optional structured details.
        suggestion: Optional actionable recovery suggestion.

    Returns:
        A Flask JSON response tuple (response, status_code).
    """
    error = ErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        suggestion=suggestion,
    )
    return jsonify(asdict(error)), status_code


@lab_routes.route('/lab/start', methods=['POST'])
def start_lab_session():
    """Start a new lab session.

    Expects JSON body with:
        - module_id (str): The module to start.
        - student_id (str): The student starting the session.

    Returns:
        JSON with session_id, container_id, module_id, student_id,
        started_at, and status on success (HTTP 201).
        ErrorResponse on failure.
    """
    data = request.get_json(silent=True)
    if data is None:
        return _error_response(
            error_code="INVALID_REQUEST",
            message="Request body must be valid JSON",
            status_code=400,
            suggestion="Send a JSON body with 'module_id' and 'student_id' fields.",
        )

    module_id = data.get("module_id")
    student_id = data.get("student_id")

    # Validate required fields
    errors = {}
    if not module_id or not isinstance(module_id, str):
        errors["module_id"] = "module_id is required and must be a non-empty string"
    if not student_id or not isinstance(student_id, str):
        errors["student_id"] = "student_id is required and must be a non-empty string"

    if errors:
        return _error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid submission: missing or invalid required fields",
            status_code=400,
            details=errors,
            suggestion="Provide both 'module_id' and 'student_id' as non-empty strings.",
        )

    try:
        runner = _get_runner()
        session = runner.start_session(module_id=module_id, student_id=student_id)
        return jsonify({
            "session_id": session.session_id,
            "container_id": session.container_id,
            "module_id": session.module_id,
            "student_id": session.student_id,
            "started_at": session.started_at.isoformat(),
            "status": session.status,
        }), 201

    except PrerequisiteError as e:
        return _error_response(
            error_code="PREREQUISITE_NOT_MET",
            message=str(e),
            status_code=409,
            details={"unmet_prerequisites": e.unmet_prerequisites},
            suggestion="Complete the listed prerequisite modules before starting this session.",
        )
    except ValueError as e:
        return _error_response(
            error_code="INVALID_MODULE",
            message=str(e),
            status_code=404,
            suggestion="Check the module_id and ensure it exists in the lab configuration.",
        )
    except Exception as e:
        logger.exception("Unexpected error starting lab session")
        return _error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred while starting the lab session",
            status_code=500,
            details={"error_type": type(e).__name__},
            suggestion="Try again later or contact the administrator.",
        )


@lab_routes.route('/lab/status/<session_id>', methods=['GET'])
def get_session_status(session_id: str):
    """Check lab session status.

    Args:
        session_id: The session identifier from the URL path.

    Returns:
        JSON with session_id, module_id, student_id, started_at, status,
        and elapsed_seconds on success (HTTP 200).
        ErrorResponse if session not found.
    """
    try:
        runner = _get_runner()
        session = runner.get_session(session_id)

        if session is None:
            return _error_response(
                error_code="SESSION_NOT_FOUND",
                message=f"Session not found: {session_id}",
                status_code=404,
                details={"session_id": session_id},
                suggestion="Verify the session_id or start a new lab session.",
            )

        from datetime import datetime

        now = datetime.now(timezone.utc)
        elapsed = (now - session.started_at).total_seconds()

        return jsonify({
            "session_id": session.session_id,
            "module_id": session.module_id,
            "student_id": session.student_id,
            "started_at": session.started_at.isoformat(),
            "status": session.status,
            "elapsed_seconds": round(elapsed, 2),
        }), 200

    except Exception as e:
        logger.exception("Unexpected error checking session status")
        return _error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred while checking session status",
            status_code=500,
            details={"error_type": type(e).__name__},
            suggestion="Try again later or contact the administrator.",
        )


@lab_routes.route('/lab/result/<session_id>/<exercise_id>', methods=['GET'])
def get_exercise_result(session_id: str, exercise_id: str):
    """Retrieve exercise validation result.

    Args:
        session_id: The session identifier from the URL path.
        exercise_id: The exercise identifier from the URL path.

    Returns:
        JSON with exercise result details on success (HTTP 200).
        ErrorResponse if session not found.
    """
    try:
        runner = _get_runner()
        session = runner.get_session(session_id)

        if session is None:
            return _error_response(
                error_code="SESSION_NOT_FOUND",
                message=f"Session not found: {session_id}",
                status_code=404,
                details={"session_id": session_id},
                suggestion="Verify the session_id or start a new lab session.",
            )

        # Execute the exercise to get the result
        # Note: In a production system, results might be cached.
        # Here we retrieve the result by executing a status check.
        result = runner.execute_exercise(
            session_id=session_id,
            exercise_id=exercise_id,
            submission={"command": f"echo 'Retrieving result for {exercise_id}'"},
        )

        response_data = {
            "session_id": session_id,
            "exercise_id": exercise_id,
            "status": result.status.value,
            "output_logs": result.output_logs,
            "execution_duration_seconds": result.execution_duration_seconds,
        }

        if result.checks:
            response_data["checks"] = [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "feedback": check.feedback,
                    "expected": check.expected,
                    "actual": check.actual,
                }
                for check in result.checks
            ]

        if result.error_message:
            response_data["error_message"] = result.error_message

        return jsonify(response_data), 200

    except SessionNotFoundError:
        return _error_response(
            error_code="SESSION_NOT_FOUND",
            message=f"Session not found: {session_id}",
            status_code=404,
            details={"session_id": session_id},
            suggestion="Verify the session_id or start a new lab session.",
        )
    except Exception as e:
        logger.exception("Unexpected error retrieving exercise result")
        return _error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred while retrieving the exercise result",
            status_code=500,
            details={"error_type": type(e).__name__},
            suggestion="Try again later or contact the administrator.",
        )


@lab_routes.route('/lab/submit', methods=['POST'])
def submit_exercise():
    """Submit an exercise for validation.

    Expects JSON body with:
        - session_id (str): The active session identifier.
        - exercise_id (str): The exercise to validate.
        - submission (dict): The exercise submission data (e.g., command, script).

    Returns:
        JSON with exercise result on success (HTTP 200).
        ErrorResponse on failure.
    """
    data = request.get_json(silent=True)
    if data is None:
        return _error_response(
            error_code="INVALID_REQUEST",
            message="Request body must be valid JSON",
            status_code=400,
            suggestion="Send a JSON body with 'session_id', 'exercise_id', and 'submission' fields.",
        )

    session_id = data.get("session_id")
    exercise_id = data.get("exercise_id")
    submission = data.get("submission")

    # Validate required fields
    errors = {}
    if not session_id or not isinstance(session_id, str):
        errors["session_id"] = "session_id is required and must be a non-empty string"
    if not exercise_id or not isinstance(exercise_id, str):
        errors["exercise_id"] = "exercise_id is required and must be a non-empty string"
    if submission is None or not isinstance(submission, dict):
        errors["submission"] = "submission is required and must be an object"

    if errors:
        return _error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid submission: missing or invalid required fields",
            status_code=400,
            details=errors,
            suggestion="Provide 'session_id', 'exercise_id', and 'submission' with valid values.",
        )

    try:
        runner = _get_runner()
        result = runner.execute_exercise(
            session_id=session_id,
            exercise_id=exercise_id,
            submission=submission,
        )

        response_data = {
            "session_id": session_id,
            "exercise_id": exercise_id,
            "status": result.status.value,
            "output_logs": result.output_logs,
            "execution_duration_seconds": result.execution_duration_seconds,
        }

        if result.checks:
            response_data["checks"] = [
                {
                    "name": check.name,
                    "passed": check.passed,
                    "feedback": check.feedback,
                    "expected": check.expected,
                    "actual": check.actual,
                }
                for check in result.checks
            ]

        if result.error_message:
            response_data["error_message"] = result.error_message

        return jsonify(response_data), 200

    except SessionNotFoundError:
        return _error_response(
            error_code="SESSION_NOT_FOUND",
            message=f"Session not found: {session_id}",
            status_code=404,
            details={"session_id": session_id},
            suggestion="Verify the session_id or start a new lab session.",
        )
    except Exception as e:
        logger.exception("Unexpected error submitting exercise")
        return _error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred while submitting the exercise",
            status_code=500,
            details={"error_type": type(e).__name__},
            suggestion="Try again later or contact the administrator.",
        )
