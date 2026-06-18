# Requirements Document

## Introduction

This document defines the requirements for the **AI Store Labs** training project — a SkillHub-based interactive learning platform for the OPCP AI-Powered-Store. The project provides a static HTML training website (EN/FR) with guided lessons and a Python-based lab framework for hands-on exercises. The architecture mirrors the reference project `opcp-openstack-first-steps`, adapted to the AI-Powered-Store platform's capabilities (Docker containerization, CLI/API/Web management, GPU sharing, serverless execution, billing, backups, and AI agents).

## Glossary

- **SkillHub**: The static HTML training website serving lesson content with locale support (EN/FR), progress tracking, and responsive navigation.
- **Lab_Framework**: The Python-based engine that executes, validates, and tracks hands-on lab exercises within containerized environments.
- **Lab_Module**: A self-contained training unit within the Lab_Framework containing exercises, solutions, setup scripts, and documentation for a specific topic.
- **Lesson_Catalog**: The JavaScript data structure defining all available lessons with metadata (id, slug, title, difficulty, estimatedMinutes, prerequisites).
- **Progress_Tracker**: The component responsible for persisting user progress through lessons and exercises using localStorage (SkillHub) or server-side state (Lab_Framework).
- **Assessment_Engine**: The Lab_Framework component that evaluates exercise submissions against expected outcomes.
- **Exercise_Validator**: The Lab_Framework component that checks whether a specific exercise step has been completed correctly.
- **Flask_App**: The Python Flask web application serving the SkillHub static files and providing API endpoints for lab operations.
- **AI_Powered_Store**: The target platform providing centralized GenAI agent deployment, Docker management, CLI, REST API, MCP support, WAF, backups, billing, GPU sharing, and serverless execution.
- **MIG_Profile**: A Multi-Instance GPU configuration that partitions a physical GPU into isolated instances for shared workloads.
- **Serverless_Container**: An ephemeral Docker container that executes a task and terminates automatically without persistent allocation.
- **Lab_Config**: The YAML configuration file defining module order, endpoint configuration, session limits, and resource constraints.
- **Navigation_Module**: The JavaScript module handling sidebar navigation, hamburger menu, and lesson routing within SkillHub.
- **I18n_Module**: The JavaScript module managing language detection, locale switching, and URL routing between EN/FR content.

## Requirements

### Requirement 1: SkillHub Static Training Site Structure

**User Story:** As a learner, I want a static HTML training site with bilingual support, so that I can access AI-Powered-Store lessons in English or French.

#### Acceptance Criteria

1. THE SkillHub SHALL provide an `index.html` landing page that detects the user's browser language and redirects to the appropriate locale folder (`en/` or `fr/`), defaulting to `en/` if the browser language is neither English nor French.
2. THE SkillHub SHALL organize lesson content into `en/` and `fr/` locale directories, each containing individual HTML files per lesson.
3. THE SkillHub SHALL include a Lesson_Catalog JavaScript module defining all lessons with id, slug, title, difficulty (one of "beginner", "intermediate", or "advanced"), estimatedMinutes (integer between 1 and 480), and prerequisites (array of lesson ids) fields.
4. THE Navigation_Module SHALL render a sidebar menu listing all lessons grouped by difficulty and provide a hamburger menu for viewports 768px wide or narrower.
5. IF a language preference exists in localStorage, THEN THE I18n_Module SHALL use the stored preference instead of browser language detection when determining the active locale.
6. THE I18n_Module SHALL allow users to switch between English and French at any time and persist the language preference in localStorage.
7. THE SkillHub SHALL apply OVHcloud-branded responsive CSS styling via a single `assets/css/style.css` file.
8. THE SkillHub SHALL include a code syntax highlighting module for rendering code snippets within lesson content.

### Requirement 2: Lesson Progress Tracking

**User Story:** As a learner, I want my lesson progress to be saved locally, so that I can resume where I left off across sessions.

#### Acceptance Criteria

1. WHEN a user clicks the "Mark as Complete" button on a lesson page, THE Progress_Tracker SHALL persist the completion status in localStorage keyed by lesson id.
2. WHEN the SkillHub loads, THE Progress_Tracker SHALL restore previously saved progress and visually indicate completed lessons in the navigation sidebar with a checkmark icon and "completed" CSS class.
3. THE Progress_Tracker SHALL calculate and display an overall completion percentage (rounded to the nearest integer) in the header progress bar based on the ratio of completed lessons to total lessons.
4. IF localStorage is unavailable or throws an error, THEN THE Progress_Tracker SHALL degrade gracefully by operating without persistence and displaying no progress state.

### Requirement 3: Lab Framework Core Architecture

**User Story:** As a platform administrator, I want a Python lab framework that executes and validates exercises in containers, so that learners can practice safely.

#### Acceptance Criteria

1. THE Lab_Framework SHALL include a core runner module that orchestrates exercise execution within Docker containers and returns a structured result containing status (pass/fail/error), output logs, and execution duration.
2. THE Lab_Framework SHALL include a configuration loader that reads Lab_Config YAML files defining module order, endpoints, session limits, and resource limits, and rejects invalid configurations with a descriptive error message.
3. THE Lab_Framework SHALL include an Assessment_Engine that evaluates exercise submissions and returns a result containing pass or fail status, a list of checks performed with individual pass/fail outcomes, and textual feedback per check.
4. THE Lab_Framework SHALL include a Progress_Tracker that persists exercise completion state server-side in a JSON or database store, recording student id, module name, exercise id, timestamp, and pass/fail result.
5. THE Lab_Framework SHALL include a resource limiter that enforces CPU (0.5 to 4 cores), memory (128 MB to 4096 MB), and time (1 to 120 minutes) constraints on exercise containers as defined in Lab_Config.
6. IF an exercise container exceeds a resource limit, THEN THE Lab_Framework SHALL terminate the container and return an error result indicating which limit was exceeded.
7. THE Lab_Framework SHALL include an Exercise_Validator that checks individual exercise steps against expected outcomes defined as JSON assertions.
8. THE Lab_Framework SHALL include a credential handler that manages API keys and authentication tokens by reading them from environment variables or a secrets file, never embedding credentials in source code or logs.

### Requirement 4: Lab Module Structure

**User Story:** As a content author, I want a standardized module structure, so that I can create consistent lab exercises across all topics.

#### Acceptance Criteria

1. THE Lab_Framework SHALL organize each Lab_Module into a directory containing: `README.md`, `exercises/`, `solutions/`, and `setup/` subdirectories.
2. THE Lab_Framework SHALL provide base template classes (Exercise, Assessment) in a `templates/` directory for module authors to extend.
3. THE Lab_Framework SHALL provide utility scripts (`setup_lab.py`, `cleanup_lab.py`, `validate_exercise.py`) in a `scripts/` directory.
4. IF a learner attempts to start a Lab_Module whose prerequisite modules are not marked as completed, THEN THE Lab_Framework SHALL block execution and display a message listing the unmet prerequisite module names.
5. THE Lab_Framework SHALL validate each Lab_Module directory on startup and log a warning for any module missing a required subdirectory or README.md file.
6. EACH Lab_Module README.md SHALL contain a title, objective description, prerequisite list, and a table of exercises with columns for exercise number, exercise name, and objective.

### Requirement 5: Installation on Bare-Metal Ubuntu Lab Module

**User Story:** As a learner, I want a guided lab on installing the AI-Powered-Store on bare-metal Ubuntu, so that I can deploy the platform from scratch.

#### Acceptance Criteria

1. THE Lab_Module for installation SHALL include exercises covering: system prerequisites verification (Ubuntu 22.04 or 24.04 LTS), Docker Engine and docker-compose v2 installation, platform repository cloning, environment configuration via `deploy.ini` and `env_setup.sh`, and initial platform startup via `deployControlPlan.sh`.
2. WHEN the learner completes the platform startup exercise, THE Exercise_Validator SHALL verify that all required services (Flask app, PostgreSQL, Nginx) report healthy status within 120 seconds by checking container health endpoints.
3. THE Lab_Module for installation SHALL include a setup script that provisions a clean Ubuntu environment (with no pre-existing Docker or platform artifacts) for the exercise.
4. IF a required system dependency is missing during validation, THEN THE Exercise_Validator SHALL report the specific missing dependency name and the exact installation command for Ubuntu.
5. THE Lab_Module for installation SHALL include a final validation exercise that confirms the platform web dashboard is accessible at the configured domain URL.

### Requirement 6: Adding New Applications Lab Module

**User Story:** As a learner, I want a guided lab on adding new applications, so that I can register and deploy apps via the CLI, API, and web interface.

#### Acceptance Criteria

1. THE Lab_Module for adding applications SHALL include exercises covering: application registration via CLI (`aipoweredstore_cli.py`), application registration via REST API (`POST /api/applications`), and application registration via web interface.
2. WHEN a learner completes an application registration exercise, THE Exercise_Validator SHALL confirm within 30 seconds that the registered application appears in the platform's application registry by querying `GET /api/applications`.
3. THE Lab_Module for adding applications SHALL include exercises for configuring application metadata: name (required, string, 1-64 characters), description (required, string), git_url (required, valid URL), and Docker image (optional, string).
4. IF an application registration fails due to invalid parameters, THEN THE Exercise_Validator SHALL display the specific validation error returned by the platform API including the field name and constraint violated.
5. IF the AI_Powered_Store platform is unreachable during an exercise, THEN THE Exercise_Validator SHALL display a connection error message indicating the unreachable endpoint and suggest checking network connectivity.

### Requirement 7: Starting Applications Lab Module

**User Story:** As a learner, I want a guided lab on starting applications, so that I can launch deployed applications on the platform.

#### Acceptance Criteria

1. THE Lab_Module for starting applications SHALL include exercises covering: starting a single application via CLI, starting via REST API (`POST /api/deployments` with action "start"), and verifying that the application reports a running status and responds to a health check.
2. WHEN the learner submits an exercise for validation, THE Exercise_Validator SHALL confirm that the started application reaches a running state by checking the platform's status endpoint within 120 seconds of the start command.
3. WHEN an application starts successfully, THE Exercise_Validator SHALL verify that each of the application's exposed ports accepts a TCP connection within 30 seconds.
4. IF an application does not reach a running state within 120 seconds of the start command, THEN THE Exercise_Validator SHALL report the last 50 lines of container logs and the failure reason returned by the platform's status endpoint.
5. WHEN the Exercise_Validator completes all checks for an exercise, THE Exercise_Validator SHALL display a pass or fail result indicating which specific checks succeeded and which failed.

### Requirement 8: Stopping Applications Lab Module

**User Story:** As a learner, I want a guided lab on stopping applications, so that I can gracefully shut down running applications.

#### Acceptance Criteria

1. THE Lab_Module for stopping applications SHALL include exercises covering: stopping a single application via CLI, stopping via REST API (`POST /api/deployments` with action "stop"), and confirming graceful shutdown where graceful shutdown is defined as the application completing in-flight requests and the process exiting with a zero exit code.
2. WHEN the learner initiates a stop exercise, THE Exercise_Validator SHALL confirm that the target application is running before proceeding with the exercise.
3. WHEN an application is stopped, THE Exercise_Validator SHALL verify within 5 seconds that the application's process has terminated, its ports refuse new connections, and then display a success confirmation to the learner.
4. IF a stop operation does not complete within 30 seconds, THEN THE Exercise_Validator SHALL report the timeout to the learner and suggest force-stop as a recovery option.
5. WHEN the learner completes a stop exercise using force-stop, THE Exercise_Validator SHALL verify that the application's process has terminated and its ports refuse new connections regardless of in-flight request completion.

### Requirement 9: Making Backups Lab Module

**User Story:** As a learner, I want a guided lab on making backups, so that I can protect application data using PostgreSQL pg_dump and S3 storage.

#### Acceptance Criteria

1. THE Lab_Module for backups SHALL include exercises covering: PostgreSQL database backup using pg_dump, uploading backups to S3-compatible storage, scheduling automated backups, and verifying backup integrity.
2. WHEN the learner completes the pg_dump exercise, THE Exercise_Validator SHALL confirm that a backup file greater than 0 bytes is created in pg_dump custom format or plain SQL format and is restorable by executing pg_restore (or psql for plain format) against a test database without errors.
3. WHEN the learner completes the S3 upload exercise, THE Exercise_Validator SHALL verify that the uploaded backup exists in the configured S3 bucket with metadata including content-type, upload timestamp, and source database name.
4. IF a backup operation fails due to insufficient permissions, THEN THE Exercise_Validator SHALL report the specific permission issue and required credentials.
5. WHEN the learner completes the scheduling exercise, THE Exercise_Validator SHALL confirm that a cron job or equivalent scheduled task is registered and produces at least one backup file within 120 seconds of the scheduled trigger time.

### Requirement 10: Modifying Existing Applications Lab Module

**User Story:** As a learner, I want a guided lab on modifying applications using the AI Developer agent, so that I can leverage AI-assisted code changes.

#### Acceptance Criteria

1. THE Lab_Module for modifying applications SHALL include at least 4 sequential exercises covering: invoking the AI Developer agent for code modifications, reviewing proposed changes, approving and applying modifications, and verifying the updated application.
2. THE Exercise_Validator SHALL confirm that the AI Developer agent produces a code diff that applies cleanly to the target file without merge conflicts and contains only syntactically correct code for the requested modification.
3. WHEN a modification is applied, THE Exercise_Validator SHALL verify that the modified application build process exits with code 0 within 120 seconds and the application responds to a health check within 30 seconds of starting.
4. IF the AI Developer agent fails to produce a diff that applies cleanly or contains syntactically correct code, THEN THE Exercise_Validator SHALL display an error message indicating the failure reason and suggest at least 1 alternative prompt to the learner.
5. WHEN the modified application starts, THE Exercise_Validator SHALL verify that the application produces no runtime errors in its output during the first 10 seconds of execution.

### Requirement 11: Docker Applications with MIG GPU Lab Module

**User Story:** As a learner, I want a guided lab on launching Docker applications with shared GPU MIG profiles, so that I can utilize GPU resources efficiently.

#### Acceptance Criteria

1. THE Lab_Module for MIG GPU SHALL include exercises covering: listing available MIG_Profile configurations, deploying a Docker application with a specific MIG_Profile, monitoring GPU utilization, and releasing GPU resources, with each exercise providing a defined completion condition that the Exercise_Validator can evaluate as pass or fail.
2. WHEN a learner deploys a Docker application requesting a specific MIG_Profile, THE Exercise_Validator SHALL query the GPU allocation status within 30 seconds and confirm the deployed application is assigned the requested MIG_Profile by displaying the assigned profile identifier.
3. WHEN a MIG-enabled application is running, THE Exercise_Validator SHALL verify that GPU compute is accessible from within the container by executing a sample compute operation and confirming it completes without error within 60 seconds.
4. IF a requested MIG_Profile is unavailable due to capacity, THEN THE Exercise_Validator SHALL report at least one available alternative profile that matches or is closest in compute capability, along with an indication that the originally requested profile is at capacity.
5. WHEN a learner completes the exercise to release GPU resources, THE Exercise_Validator SHALL verify that the MIG_Profile allocation is removed by confirming the profile no longer appears in the active GPU allocation status within 30 seconds.

### Requirement 12: Serverless Docker Execution Lab Module

**User Story:** As a learner, I want a guided lab on serverless Docker execution, so that I can run ephemeral containers for one-off tasks.

#### Acceptance Criteria

1. THE Lab_Module for serverless execution SHALL include at least 4 exercises covering: submitting a Serverless_Container task, monitoring execution status, retrieving execution output, and verifying automatic cleanup.
2. WHEN the learner submits a Serverless_Container exercise, THE Exercise_Validator SHALL confirm that the container executes the specified task and returns output within 60 seconds.
3. WHEN a Serverless_Container completes, THE Exercise_Validator SHALL verify within 30 seconds that the container is terminated and that no compute or network resources remain allocated to that container.
4. IF a Serverless_Container exceeds its time limit, THEN THE Exercise_Validator SHALL display a timeout indication to the learner and confirm container termination within 30 seconds.
5. IF the learner attempts to retrieve output before the Serverless_Container has completed, THEN THE Exercise_Validator SHALL display a message indicating the task is still in progress and provide the current execution status.

### Requirement 13: Billing and Cost Tracking Lab Module

**User Story:** As a learner, I want a guided lab on the billing system, so that I can understand and manage cost tracking for deployed applications.

#### Acceptance Criteria

1. THE Lab_Module for billing SHALL include at least 4 exercises covering: viewing current resource consumption, applying cost calculation rules to compute expected charges for a given resource set, setting budget alerts, and generating usage reports.
2. THE Exercise_Validator SHALL confirm that resource consumption data matches active containers' billing records with zero discrepancy in resource count and consumption values within a 1% tolerance.
3. WHEN a budget alert threshold is configured, THE Exercise_Validator SHALL verify that the alert triggers within 30 seconds when simulated usage exceeds the configured threshold.
4. IF billing data is unavailable due to a service interruption, THEN THE Exercise_Validator SHALL report an error message indicating the service interruption, display the last known billing state, and indicate the age of the displayed data as time elapsed since last successful retrieval.
5. WHEN a learner completes the usage report exercise, THE Exercise_Validator SHALL verify that the generated report contains resource name, consumption quantity, unit cost, and total cost for each billed resource within the reporting period.
6. WHEN a learner completes the cost calculation exercise, THE Exercise_Validator SHALL verify that the learner-computed charges match the system-computed charges within a 1% tolerance for the given resource set.

### Requirement 14: Containerized Lab Execution Environment

**User Story:** As a platform administrator, I want labs to run in isolated Docker containers, so that learner exercises do not affect the host system.

#### Acceptance Criteria

1. THE Lab_Framework SHALL provide a Dockerfile and entrypoint script in a `base/` directory that defines the containerized execution environment based on Python 3.11.
2. THE Lab_Framework SHALL include a `requirements.txt` in the `base/` directory specifying all Python dependencies for the container image with pinned versions.
3. THE Lab_Framework SHALL enforce resource limits (CPU, memory, disk) per exercise container as defined in Lab_Config, terminating any container that exceeds its allocated resources.
4. WHEN a lab session exceeds the configured session time limit, THE Lab_Framework SHALL terminate the session container, preserve the current progress state, and notify the learner with a message indicating the session expired and how to resume.
5. THE Lab_Framework SHALL ensure container isolation such that each exercise container has no network access to other exercise containers and no filesystem access to the host beyond its mounted volumes.

### Requirement 15: Flask Application and Docker Orchestration

**User Story:** As a platform administrator, I want a Flask application with Docker Compose orchestration, so that the entire training platform can be deployed with a single command.

#### Acceptance Criteria

1. THE Flask_App SHALL serve SkillHub static files under the root path and provide REST API endpoints for lab operations including: starting a lab session, checking session status, and retrieving exercise results.
2. THE project SHALL include a `docker-compose.yml` at the root that orchestrates the Flask_App, Nginx for HTTPS static serving, and Lab_Framework containers, with all services starting from a single `docker-compose up` command.
3. THE project SHALL include a root `Dockerfile` defining the Flask_App container image based on Python 3.11-slim.
4. THE project SHALL include an `env_setup.sh` script that validates Python 3.9+ availability, Docker Engine presence, and docker-compose v2 presence, exiting with a non-zero code and descriptive error if any prerequisite is missing.
5. THE project SHALL include a root `requirements.txt` listing Flask and all server-side Python dependencies with pinned versions.
6. THE project SHALL include a root `README.md` documenting project setup, architecture overview, repository structure, and usage instructions.
7. WHEN `docker-compose up` completes, THE Flask_App SHALL respond to a `/health` endpoint with HTTP 200 and a JSON payload containing `{"status": "healthy"}` within 60 seconds.

### Requirement 16: Lab Configuration Management

**User Story:** As a content author, I want a centralized YAML configuration, so that I can define module order, endpoints, and resource limits in one place.

#### Acceptance Criteria

1. THE Lab_Config SHALL define the ordered list of Lab_Modules (minimum 1, maximum 50 modules) with their prerequisite dependencies expressed as module identifiers, forming a directed acyclic graph.
2. THE Lab_Config SHALL specify platform API endpoint URLs for exercise validation against a live or simulated AI_Powered_Store instance, with each URL validated as a well-formed HTTP or HTTPS URL on configuration load.
3. THE Lab_Config SHALL define session time limits per module (between 5 and 480 minutes) and global resource ceilings: max concurrent containers (between 1 and 100), memory ceiling (between 128 MB and 65536 MB), and CPU ceiling (between 0.5 and 64 cores).
4. WHEN the Lab_Config file is saved to disk with valid content, THE Lab_Framework SHALL apply the updated configuration within 10 seconds without requiring a service restart.
5. IF the Lab_Config contains invalid YAML syntax, undefined module references, circular prerequisite dependencies, or out-of-range resource values, THEN THE Lab_Framework SHALL reject the configuration change, retain the last valid configuration, and log an error message indicating the specific validation failure.
6. IF a configured API endpoint URL is unreachable at configuration load time, THEN THE Lab_Framework SHALL log a warning indicating the unreachable endpoint and continue operating with the remaining valid endpoints.

### Requirement 17: Unit Testing

**User Story:** As a developer, I want unit tests for the lab framework, so that I can verify core functionality remains correct during development.

#### Acceptance Criteria

1. THE project SHALL include a `tests/` directory within the `labs/` folder containing unit tests for the core runner, assessment engine, progress tracker, and exercise validator.
2. THE unit tests SHALL achieve a minimum of 80% line coverage across all public methods in the Lab_Framework core modules, as measured by a Python coverage tool.
3. WHEN a unit test fails, THE test output SHALL display the failing module name, method name, assertion expression, and expected versus actual values.
4. THE unit tests SHALL execute without requiring running Docker containers, network access, or live AI_Powered_Store platform connectivity, using mocks or stubs for external dependencies.
5. THE project SHALL include a test runner configuration file in the `labs/tests/` directory that allows executing the full test suite with a single command.
