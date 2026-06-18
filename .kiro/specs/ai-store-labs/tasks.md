# Implementation Plan: AI Store Labs

## Overview

This implementation plan builds the AI Store Labs training platform incrementally: starting with project scaffolding and configuration, then the core lab framework, SkillHub frontend, Flask application, lab modules, and finally integration and testing. Each task builds on previous work to ensure no orphaned code.

## Tasks

- [x] 1. Set up project structure and configuration
  - [x] 1.1 Create root project files and directory scaffolding
    - Create `app.py` (Flask entry point stub), `Dockerfile` (Python 3.11-slim based), `docker-compose.yml` (Flask + Nginx + Lab containers), `requirements.txt` (Flask and pinned dependencies), `env_setup.sh` (prerequisite validation script), `README.md` (project documentation)
    - Create directory structure: `src/api/`, `skillhub/`, `labs/core/`, `labs/modules/`, `labs/templates/`, `labs/scripts/`, `labs/config/`, `labs/base/`, `labs/tests/`, `nginx/`
    - Add `__init__.py` files for Python packages
    - _Requirements: 15.2, 15.3, 15.4, 15.5, 15.6_

  - [x] 1.2 Implement Lab_Config YAML schema and ConfigLoader
    - Create `labs/config/lab_config.yaml` with module definitions, endpoints, and global resource ceilings
    - Implement `labs/core/config_loader.py` with `ConfigLoader` class: `load()`, `validate()`, `watch()` methods
    - Validate DAG integrity (no circular prerequisites), URL format (HTTP/HTTPS), numeric ranges (session time 5-480 min, CPU 0.5-4 cores, memory 128-4096 MB, time 1-120 min, max containers 1-100, memory ceiling 128-65536 MB, CPU ceiling 0.5-64 cores)
    - Implement hot-reload: watch config file and apply valid changes within 10 seconds
    - On invalid config: reject change, retain last valid config, log specific error
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6_

  - [ ]* 1.3 Write property tests for ConfigLoader
    - **Property 4: Configuration Validation Round-Trip**
    - **Property 5: Invalid Configuration Rejection**
    - **Validates: Requirements 3.2, 16.1, 16.2, 16.3, 16.5**

- [x] 2. Implement Lab Framework core modules
  - [x] 2.1 Implement data models and core types
    - Create `labs/core/models.py` with all dataclasses: `ResourceLimits`, `ExerciseResult`, `CheckResult`, `AssessmentResult`, `ProgressEntry`, `SessionResult`, `ValidationResult`, `LabModule`, `LabConfig`, `ErrorResponse`
    - Implement `ExerciseStatus` and `Difficulty` enums
    - _Requirements: 3.1, 3.3, 3.4, 3.5_

  - [x] 2.2 Implement CredentialHandler
    - Create `labs/core/credential_handler.py` with `CredentialHandler` class
    - Implement `get_credential(key)` reading from env vars or secrets file
    - Implement `inject_into_env(container_env)` to add credentials to container environment
    - Ensure credentials never appear in log output
    - _Requirements: 3.8_

  - [ ]* 2.3 Write property test for CredentialHandler
    - **Property 10: Credential Retrieval and Non-Leakage**
    - **Validates: Requirements 3.8**

  - [x] 2.4 Implement ResourceLimiter
    - Create `labs/core/resource_limiter.py` with `ResourceLimiter` class
    - Implement `get_container_limits(module_id)` to extract limits from config
    - Implement `apply_limits(container_id, limits)` translating to Docker constraints (CPU quota, memory bytes, timeout)
    - Implement `monitor(container_id, limits, on_exceed)` to watch and terminate on limit breach
    - _Requirements: 3.5, 3.6, 14.3_

  - [ ]* 2.5 Write property test for ResourceLimiter
    - **Property 8: Resource Limits Translation**
    - **Validates: Requirements 3.5**

  - [x] 2.6 Implement ExerciseValidator
    - Create `labs/core/validators.py` with `ExerciseValidator` class
    - Implement `validate_step(step, assertion)` checking equality and containment assertions
    - Implement `validate_exercise(exercise_id, steps)` running sequential step validation
    - _Requirements: 3.7_

  - [ ]* 2.7 Write property test for ExerciseValidator
    - **Property 9: Exercise Step Assertion Evaluation**
    - **Validates: Requirements 3.7**

  - [x] 2.8 Implement AssessmentEngine
    - Create `labs/core/assessment.py` with `AssessmentEngine` class
    - Implement `evaluate(exercise_id, submission, expected)` returning `AssessmentResult`
    - Overall status is "pass" iff all checks pass; "fail" if any check fails
    - Always return non-empty checks list and textual feedback
    - _Requirements: 3.3_

  - [ ]* 2.9 Write property test for AssessmentEngine
    - **Property 6: Assessment Result Consistency**
    - **Validates: Requirements 3.3**

  - [x] 2.10 Implement ProgressTracker (server-side)
    - Create `labs/core/progress.py` with `ProgressTracker` class
    - Implement JSON-based persistence: `record_completion(student_id, module_name, exercise_id, result)`
    - Implement `get_progress(student_id, module_name)` with optional module filter
    - Implement `is_module_complete(student_id, module_name)` checking all exercises passed
    - _Requirements: 3.4_

  - [ ]* 2.11 Write property test for ProgressTracker
    - **Property 7: Server-Side Progress Persistence Round-Trip**
    - **Validates: Requirements 3.4**

  - [x] 2.12 Implement LabRunner (core runner)
    - Create `labs/core/runner.py` with `LabRunner` class
    - Implement `start_session(module_id, student_id)` spawning Docker container with resource limits
    - Implement `execute_exercise(session_id, exercise_id, submission)` returning structured `ExerciseResult` (status, output_logs, execution_duration_seconds)
    - Implement `terminate_session(session_id)` stopping and removing container
    - Enforce prerequisite checks before session start
    - _Requirements: 3.1, 4.4, 14.3, 14.4, 14.5_

  - [ ]* 2.13 Write property tests for LabRunner
    - **Property 11: Prerequisite Enforcement**
    - **Property 18: Runner Output Structure Invariant**
    - **Validates: Requirements 3.1, 4.4**

- [x] 3. Checkpoint - Core framework
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Lab Framework templates and scripts
  - [x] 4.1 Create base template classes
    - Create `labs/templates/exercise_base.py` with base `Exercise` class for module authors to extend
    - Create `labs/templates/assessment_base.py` with base `Assessment` class
    - _Requirements: 4.2_

  - [x] 4.2 Create utility scripts
    - Create `labs/scripts/setup_lab.py` for lab environment setup
    - Create `labs/scripts/cleanup_lab.py` for lab environment teardown
    - Create `labs/scripts/validate_exercise.py` for exercise validation
    - _Requirements: 4.3_

  - [x] 4.3 Implement module structure validator
    - Create a validation function that checks each Lab_Module directory for required components: `README.md`, `exercises/`, `solutions/`, `setup/`
    - Log warnings for missing components
    - Validate README.md content for required sections: title, objective, prerequisite list, exercise table
    - _Requirements: 4.5, 4.6_

  - [ ]* 4.4 Write property test for module structure validator
    - **Property 12: Module Structure Validation**
    - **Validates: Requirements 4.5, 4.6**

  - [x] 4.5 Create lab base container
    - Create `labs/base/Dockerfile` (Python 3.11 based)
    - Create `labs/base/entrypoint.sh` (container entrypoint)
    - Create `labs/base/requirements.txt` (pinned dependencies)
    - _Requirements: 14.1, 14.2_

- [x] 5. Implement SkillHub frontend
  - [x] 5.1 Create SkillHub HTML structure and CSS
    - Create `skillhub/index.html` landing page with locale detection and redirect
    - Create `skillhub/assets/css/style.css` with OVHcloud-branded responsive styling
    - Create locale directories `skillhub/en/` and `skillhub/fr/` with placeholder lesson HTML files
    - _Requirements: 1.1, 1.2, 1.7_

  - [x] 5.2 Implement I18n module
    - Create `skillhub/js/i18n.js` with `detectLocale()`, `switchLocale(locale)`, `getStoredLocalePreference()`, `setLocalePreference(locale)`
    - Priority: stored preference > browser language ("fr" for French, "en" for all others)
    - Output always "en" or "fr"
    - _Requirements: 1.1, 1.5, 1.6_

  - [ ]* 5.3 Write property test for I18n module
    - **Property 1: Locale Resolution Priority**
    - **Validates: Requirements 1.1, 1.5**

  - [x] 5.4 Implement Lesson Catalog module
    - Create `skillhub/js/lessons.js` with lesson data structure and helper functions: `getLessonBySlug()`, `getLessonsByDifficulty()`, `getPrerequisiteChain()`
    - Define lessons for all lab module topics with id, slug, bilingual title, difficulty, estimatedMinutes, prerequisites
    - _Requirements: 1.3_

  - [x] 5.5 Implement Progress Tracker module (client-side)
    - Create `skillhub/js/progress.js` with `markLessonComplete(lessonId)`, `isLessonComplete(lessonId)`, `getCompletionPercentage(totalLessons)`, `getCompletedLessons()`, `resetProgress()`
    - Persist to localStorage keyed by lesson id
    - Gracefully degrade if localStorage unavailable
    - Completion percentage: `round(completedCount / totalCount * 100)`, integer in [0, 100]
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 5.6 Write property tests for Progress Tracker
    - **Property 2: Client-Side Progress Persistence Round-Trip**
    - **Property 3: Completion Percentage Calculation**
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [x] 5.7 Implement Navigation module
    - Create `skillhub/js/navigation.js` with `initNavigation()`, `renderSidebar()`, `initHamburgerMenu()`, `navigateToLesson()`
    - Group lessons by difficulty in sidebar
    - Hamburger menu for viewports ≤ 768px
    - Show checkmark icon and "completed" CSS class for completed lessons
    - _Requirements: 1.4, 2.2_

  - [x] 5.8 Implement code highlighting and main bootstrap
    - Create `skillhub/js/code-highlight.js` for syntax highlighting
    - Create `skillhub/js/main.js` for application bootstrap and module initialization
    - _Requirements: 1.8_

- [x] 6. Checkpoint - SkillHub frontend
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement Flask application and API
  - [x] 7.1 Implement Flask app and health endpoint
    - Implement `app.py` with static file serving for SkillHub and `/health` endpoint returning `{"status": "healthy"}` with HTTP 200
    - _Requirements: 15.1, 15.7_

  - [x] 7.2 Implement Lab API routes
    - Create `src/api/__init__.py` and `src/api/routes.py`
    - Implement `POST /api/lab/start` (start lab session)
    - Implement `GET /api/lab/status/<session_id>` (check session status)
    - Implement `GET /api/lab/result/<session_id>/<exercise_id>` (retrieve exercise result)
    - Implement `POST /api/lab/submit` (submit exercise for validation)
    - Return proper error responses with ErrorResponse format for invalid submissions
    - _Requirements: 15.1_

  - [x] 7.3 Configure Nginx and Docker Compose
    - Create `nginx/nginx.conf` for reverse proxy (HTTPS + static serving)
    - Finalize `docker-compose.yml` with service definitions, networking, and volume mounts
    - Ensure Flask app container mounts Docker socket for spawning exercise containers
    - _Requirements: 15.2_

- [x] 8. Implement Lab Modules
  - [x] 8.1 Create install-bare-metal module
    - Create `labs/modules/install-bare-metal/` with README.md, exercises/, solutions/, setup/
    - Implement exercises: system prerequisites verification, Docker installation, repository cloning, environment configuration, platform startup
    - Create setup script provisioning clean Ubuntu environment
    - Create validation for service health checks (Flask, PostgreSQL, Nginx within 120s)
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 8.2 Create adding-applications module
    - Create `labs/modules/adding-applications/` with standard structure
    - Implement exercises: CLI registration, REST API registration, web interface registration
    - Implement metadata validation (name 1-64 chars, description non-empty, git_url valid URL)
    - Validate application appears in registry within 30s
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 8.3 Write property test for application metadata validation
    - **Property 13: Application Metadata Validation**
    - **Validates: Requirements 6.3**

  - [x] 8.4 Create starting-applications module
    - Create `labs/modules/starting-applications/` with standard structure
    - Implement exercises: start via CLI, start via REST API, verify running status and health check
    - Validate running state within 120s, port connectivity within 30s
    - Display per-check pass/fail results
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 8.5 Write property test for validation result display
    - **Property 14: Validation Result Display Completeness**
    - **Validates: Requirements 7.5**

  - [x] 8.6 Create stopping-applications module
    - Create `labs/modules/stopping-applications/` with standard structure
    - Implement exercises: stop via CLI, stop via REST API, confirm graceful shutdown
    - Verify process termination and port refusal within 5s
    - Handle 30s timeout with force-stop suggestion
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 8.7 Create making-backups module
    - Create `labs/modules/making-backups/` with standard structure
    - Implement exercises: pg_dump backup, S3 upload, scheduling, integrity verification
    - Validate backup file > 0 bytes, restorable format, S3 metadata, cron registration
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [x] 8.8 Create modifying-applications module
    - Create `labs/modules/modifying-applications/` with standard structure
    - Implement 4+ exercises: invoke AI Developer agent, review changes, apply modifications, verify updated app
    - Validate clean diff application, build success (exit 0 within 120s), health check (within 30s)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [x] 8.9 Create mig-gpu module
    - Create `labs/modules/mig-gpu/` with standard structure
    - Implement exercises: list MIG profiles, deploy with MIG profile, monitor GPU utilization, release GPU resources
    - Validate GPU allocation within 30s, compute accessibility within 60s, profile release within 30s
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [ ]* 8.10 Write property test for MIG profile suggestion
    - **Property 15: MIG Profile Alternative Suggestion**
    - **Validates: Requirements 11.4**

  - [x] 8.11 Create serverless-execution module
    - Create `labs/modules/serverless-execution/` with standard structure
    - Implement 4+ exercises: submit serverless task, monitor status, retrieve output, verify cleanup
    - Validate execution within 60s, container cleanup within 30s, timeout handling
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 8.12 Create billing-cost-tracking module
    - Create `labs/modules/billing-cost-tracking/` with standard structure
    - Implement 4+ exercises: view consumption, calculate costs, set budget alerts, generate reports
    - Validate resource count matching within 1% tolerance, alert triggering within 30s, report completeness
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_

  - [ ]* 8.13 Write property tests for billing module
    - **Property 16: Numeric Tolerance Comparison**
    - **Property 17: Usage Report Field Completeness**
    - **Validates: Requirements 13.2, 13.5, 13.6**

- [x] 9. Checkpoint - Lab modules
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Unit tests and integration
  - [x] 10.1 Set up Python test infrastructure
    - Create `labs/tests/conftest.py` with shared fixtures and mocks (Docker, network, platform)
    - Create `labs/tests/pytest.ini` with test runner configuration
    - Ensure tests run without Docker, network, or live platform access
    - _Requirements: 17.4, 17.5_

  - [x] 10.2 Write unit tests for core modules
    - Create `labs/tests/test_runner.py` (LabRunner unit tests with mocked Docker)
    - Create `labs/tests/test_config_loader.py` (ConfigLoader unit tests)
    - Create `labs/tests/test_assessment.py` (AssessmentEngine unit tests)
    - Create `labs/tests/test_progress.py` (ProgressTracker unit tests)
    - Create `labs/tests/test_resource_limiter.py` (ResourceLimiter unit tests)
    - Create `labs/tests/test_validators.py` (ExerciseValidator unit tests)
    - Create `labs/tests/test_credentials.py` (CredentialHandler unit tests)
    - Target 80% line coverage across all core modules
    - _Requirements: 17.1, 17.2, 17.3_

  - [x] 10.3 Set up JavaScript test infrastructure
    - Create `skillhub/tests/setup.js` with localStorage mock and test environment
    - Configure Vitest or Jest for frontend tests
    - _Requirements: 17.5_

  - [x] 10.4 Write unit tests for SkillHub modules
    - Create `skillhub/tests/i18n.test.js` (locale resolution tests)
    - Create `skillhub/tests/progress.test.js` (progress tracker tests)
    - Create `skillhub/tests/navigation.test.js` (navigation module tests)
    - Create `skillhub/tests/lessons.test.js` (lesson catalog validation)
    - _Requirements: 17.1_

  - [ ]* 10.5 Write integration tests
    - Create `labs/tests/integration/test_docker.py` (container lifecycle with Docker)
    - Create `labs/tests/integration/test_e2e.py` (full workflow end-to-end)
    - Test: docker-compose up → /health returns 200, container spawning with limits, config hot-reload
    - _Requirements: 15.7_

- [-] 11. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Python property tests use Hypothesis; JavaScript property tests use fast-check
- All unit tests must run without Docker, network access, or live platform connectivity (use mocks)
- Target 80% line coverage on lab framework core modules

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "5.1"] },
    { "id": 2, "tasks": ["1.3", "2.1", "5.2", "5.4"] },
    { "id": 3, "tasks": ["2.2", "2.4", "2.6", "2.8", "2.10", "5.3", "5.5"] },
    { "id": 4, "tasks": ["2.3", "2.5", "2.7", "2.9", "2.11", "5.6", "5.7", "5.8"] },
    { "id": 5, "tasks": ["2.12", "4.1", "4.5"] },
    { "id": 6, "tasks": ["2.13", "4.2", "4.3"] },
    { "id": 7, "tasks": ["4.4", "7.1"] },
    { "id": 8, "tasks": ["7.2", "7.3"] },
    { "id": 9, "tasks": ["8.1", "8.2", "8.4", "8.6", "8.7", "8.8", "8.9", "8.11", "8.12"] },
    { "id": 10, "tasks": ["8.3", "8.5", "8.10", "8.13"] },
    { "id": 11, "tasks": ["10.1", "10.3"] },
    { "id": 12, "tasks": ["10.2", "10.4", "10.5"] }
  ]
}
```
