#!/bin/bash
# Provision script for the Stopping Applications lab module.
#
# This script prepares the exercise environment by ensuring a target
# application is deployed and running, ready to be stopped by the learner.
#
# Prerequisites:
# - AI-Powered-Store platform is running
# - CLI tool is available at /usr/local/bin/aipoweredstore_cli.py
# - A test application has been registered (from adding-applications module)

set -euo pipefail

APP_NAME="${APP_NAME:-test-stop-app}"
CLI_PATH="${CLI_PATH:-/usr/local/bin/aipoweredstore_cli.py}"
APP_PORT="${APP_PORT:-8080}"

echo "=== Stopping Applications Lab - Environment Provisioning ==="
echo "Application: ${APP_NAME}"
echo "CLI Path: ${CLI_PATH}"
echo "Port: ${APP_PORT}"
echo ""

# Step 1: Verify CLI tool is available
if [ ! -f "${CLI_PATH}" ]; then
    echo "ERROR: CLI tool not found at ${CLI_PATH}"
    echo "Please complete the installation module first."
    exit 1
fi

# Step 2: Check if application is already registered
echo "Checking if application '${APP_NAME}' is registered..."
if ! "${CLI_PATH}" list 2>/dev/null | grep -q "${APP_NAME}"; then
    echo "Application not registered. Registering test application..."
    "${CLI_PATH}" register \
        --name "${APP_NAME}" \
        --description "Test application for stopping exercises" \
        --git-url "https://github.com/example/test-app.git" \
        --port "${APP_PORT}" || {
        echo "ERROR: Failed to register application"
        exit 1
    }
fi

# Step 3: Start the application if not already running
echo "Checking application status..."
STATUS=$("${CLI_PATH}" status "${APP_NAME}" 2>/dev/null || echo "unknown")

if echo "${STATUS}" | grep -qi "running"; then
    echo "Application is already running."
else
    echo "Starting application '${APP_NAME}'..."
    "${CLI_PATH}" start "${APP_NAME}" || {
        echo "ERROR: Failed to start application"
        exit 1
    }

    # Wait for application to reach running state (max 30s)
    echo "Waiting for application to reach running state..."
    TIMEOUT=30
    ELAPSED=0
    while [ ${ELAPSED} -lt ${TIMEOUT} ]; do
        STATUS=$("${CLI_PATH}" status "${APP_NAME}" 2>/dev/null || echo "unknown")
        if echo "${STATUS}" | grep -qi "running"; then
            echo "Application is running."
            break
        fi
        sleep 2
        ELAPSED=$((ELAPSED + 2))
    done

    if [ ${ELAPSED} -ge ${TIMEOUT} ]; then
        echo "WARNING: Application did not reach running state within ${TIMEOUT}s"
        exit 1
    fi
fi

echo ""
echo "=== Provisioning Complete ==="
echo "The application '${APP_NAME}' is running on port ${APP_PORT}."
echo "You may now proceed with the stopping exercises."
