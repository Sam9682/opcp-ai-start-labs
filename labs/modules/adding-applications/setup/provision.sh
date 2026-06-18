#!/bin/bash
# Provision script for the Adding Applications lab module.
#
# This script prepares the lab environment by verifying that:
# 1. The AI-Powered-Store platform is running and accessible
# 2. The CLI tool (aipoweredstore_cli.py) is available
# 3. The REST API endpoint is reachable
# 4. The web interface is accessible
#
# Prerequisites:
# - AI-Powered-Store platform installed and running
# - Network connectivity to the platform
# - Valid API credentials configured

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
PLATFORM_API_URL="${PLATFORM_API_URL:-https://store.example.com/api}"
PLATFORM_WEB_URL="${PLATFORM_WEB_URL:-https://store.example.com}"
CLI_PATH="${CLI_PATH:-aipoweredstore_cli.py}"
TIMEOUT_SECONDS=30

echo "=== Adding Applications Lab - Environment Setup ==="
echo ""

# Check 1: Verify CLI tool is accessible
echo "[1/4] Checking CLI tool availability..."
if command -v "$CLI_PATH" &> /dev/null; then
    echo "  ✓ CLI tool found: $(which "$CLI_PATH")"
else
    echo "  ✗ CLI tool not found: $CLI_PATH"
    echo "  → Ensure the AI-Powered-Store is installed and $CLI_PATH is in PATH"
    exit 1
fi

# Check 2: Verify platform API is reachable
echo "[2/4] Checking platform API connectivity..."
if curl --silent --max-time "$TIMEOUT_SECONDS" "${PLATFORM_API_URL}/health" > /dev/null 2>&1; then
    echo "  ✓ Platform API reachable at: $PLATFORM_API_URL"
else
    echo "  ✗ Platform API unreachable at: $PLATFORM_API_URL"
    echo "  → Check network connectivity and ensure the platform is running"
    exit 1
fi

# Check 3: Verify applications endpoint is available
echo "[3/4] Checking applications API endpoint..."
HTTP_STATUS=$(curl --silent --output /dev/null --write-out "%{http_code}" \
    --max-time "$TIMEOUT_SECONDS" "${PLATFORM_API_URL}/applications" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ]; then
    echo "  ✓ Applications endpoint available (HTTP $HTTP_STATUS)"
else
    echo "  ✗ Applications endpoint returned HTTP $HTTP_STATUS"
    echo "  → Endpoint: ${PLATFORM_API_URL}/applications"
    exit 1
fi

# Check 4: Verify web interface is accessible
echo "[4/4] Checking web interface accessibility..."
if curl --silent --max-time "$TIMEOUT_SECONDS" "$PLATFORM_WEB_URL" > /dev/null 2>&1; then
    echo "  ✓ Web interface accessible at: $PLATFORM_WEB_URL"
else
    echo "  ✗ Web interface unreachable at: $PLATFORM_WEB_URL"
    echo "  → Check network connectivity and ensure Nginx is running"
    exit 1
fi

echo ""
echo "=== Environment setup complete ==="
echo "All prerequisites satisfied. Ready to begin exercises."
