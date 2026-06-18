#!/bin/bash
# Provision script for the Starting Applications lab module.
#
# This script ensures the exercise environment is ready:
# - Platform CLI is accessible
# - API endpoint is reachable
# - At least one application is registered (prerequisite from adding-applications module)

set -e

echo "=== Starting Applications Lab Module - Environment Provisioning ==="

# Configuration (can be overridden by environment variables)
CLI_PATH="${AIPS_CLI_PATH:-/usr/local/bin/aipoweredstore_cli.py}"
API_BASE_URL="${AIPS_API_URL:-https://store.example.com}"
APP_NAME="${AIPS_TEST_APP:-test-app}"

echo ""
echo "Configuration:"
echo "  CLI Path:     ${CLI_PATH}"
echo "  API Base URL: ${API_BASE_URL}"
echo "  Test App:     ${APP_NAME}"
echo ""

# Check 1: CLI tool exists
echo "[1/4] Checking CLI tool availability..."
if [ -f "${CLI_PATH}" ]; then
    echo "  OK: CLI tool found at ${CLI_PATH}"
else
    echo "  WARNING: CLI tool not found at ${CLI_PATH}"
    echo "  Some exercises may not work without the CLI tool."
fi

# Check 2: API endpoint reachable
echo "[2/4] Checking API endpoint..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${API_BASE_URL}/health" 2>/dev/null || echo "000")
    if [ "${HTTP_CODE}" = "200" ]; then
        echo "  OK: API endpoint is healthy (HTTP ${HTTP_CODE})"
    elif [ "${HTTP_CODE}" = "000" ]; then
        echo "  WARNING: Cannot reach API endpoint at ${API_BASE_URL}"
        echo "  Exercises requiring API access will report connection errors."
    else
        echo "  WARNING: API returned HTTP ${HTTP_CODE} (expected 200)"
    fi
else
    echo "  SKIP: curl not available, cannot check API endpoint"
fi

# Check 3: Application is registered (prerequisite)
echo "[3/4] Checking for registered test application..."
if [ -f "${CLI_PATH}" ]; then
    if ${CLI_PATH} app list 2>/dev/null | grep -q "${APP_NAME}"; then
        echo "  OK: Application '${APP_NAME}' is registered"
    else
        echo "  WARNING: Application '${APP_NAME}' not found in registry"
        echo "  Complete the 'Adding Applications' module first."
    fi
else
    echo "  SKIP: Cannot verify without CLI tool"
fi

# Check 4: Python requests library available
echo "[4/4] Checking Python dependencies..."
if python3 -c "import requests" 2>/dev/null; then
    echo "  OK: Python 'requests' library available"
else
    echo "  WARNING: Python 'requests' library not installed"
    echo "  Install with: pip install requests"
fi

echo ""
echo "=== Provisioning complete ==="
echo ""
echo "To start the exercises, ensure:"
echo "  1. You have completed the 'Adding Applications' module"
echo "  2. At least one application is registered"
echo "  3. The platform API is accessible"
