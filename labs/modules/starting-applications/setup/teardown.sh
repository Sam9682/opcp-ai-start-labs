#!/bin/bash
# Teardown script for the Starting Applications lab module.
#
# This script cleans up after the lab exercises:
# - Optionally stops applications that were started during the exercises
# - Removes temporary files

set -e

echo "=== Starting Applications Lab Module - Teardown ==="

# Configuration
CLI_PATH="${AIPS_CLI_PATH:-/usr/local/bin/aipoweredstore_cli.py}"
APP_NAME="${AIPS_TEST_APP:-test-app}"
KEEP_RUNNING="${KEEP_RUNNING:-false}"

echo ""
echo "Configuration:"
echo "  CLI Path:     ${CLI_PATH}"
echo "  Test App:     ${APP_NAME}"
echo "  Keep Running: ${KEEP_RUNNING}"
echo ""

# Optionally stop the test application
if [ "${KEEP_RUNNING}" = "false" ]; then
    echo "[1/2] Stopping test application..."
    if [ -f "${CLI_PATH}" ]; then
        if ${CLI_PATH} app status "${APP_NAME}" 2>/dev/null | grep -qi "running"; then
            ${CLI_PATH} app stop "${APP_NAME}" 2>/dev/null && \
                echo "  OK: Application '${APP_NAME}' stopped" || \
                echo "  WARNING: Failed to stop '${APP_NAME}'"
        else
            echo "  OK: Application '${APP_NAME}' is not running"
        fi
    else
        echo "  SKIP: CLI tool not available"
    fi
else
    echo "[1/2] Keeping application running (KEEP_RUNNING=true)"
fi

# Clean up temporary files
echo "[2/2] Cleaning up temporary files..."
TEMP_DIR="/tmp/starting-applications-lab"
if [ -d "${TEMP_DIR}" ]; then
    rm -rf "${TEMP_DIR}"
    echo "  OK: Removed ${TEMP_DIR}"
else
    echo "  OK: No temporary files to clean"
fi

echo ""
echo "=== Teardown complete ==="
