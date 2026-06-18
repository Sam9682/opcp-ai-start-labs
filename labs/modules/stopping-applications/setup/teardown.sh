#!/bin/bash
# Teardown script for the Stopping Applications lab module.
#
# Cleans up the exercise environment after the module is complete.
# Ensures any remaining application processes are terminated and
# resources are released.

set -euo pipefail

APP_NAME="${APP_NAME:-test-stop-app}"
CLI_PATH="${CLI_PATH:-/usr/local/bin/aipoweredstore_cli.py}"

echo "=== Stopping Applications Lab - Environment Teardown ==="
echo "Application: ${APP_NAME}"
echo ""

# Step 1: Force-stop the application if still running
echo "Checking if application is still running..."
STATUS=$("${CLI_PATH}" status "${APP_NAME}" 2>/dev/null || echo "unknown")

if echo "${STATUS}" | grep -qi "running"; then
    echo "Application is still running. Force-stopping..."
    "${CLI_PATH}" force-stop "${APP_NAME}" 2>/dev/null || true
    sleep 2
fi

# Step 2: Verify application is stopped
STATUS=$("${CLI_PATH}" status "${APP_NAME}" 2>/dev/null || echo "stopped")
if echo "${STATUS}" | grep -qi "stopped\|terminated\|unknown"; then
    echo "Application confirmed stopped."
else
    echo "WARNING: Application may still be running. Manual cleanup may be needed."
fi

echo ""
echo "=== Teardown Complete ==="
