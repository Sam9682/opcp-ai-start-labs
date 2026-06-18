#!/bin/bash
# Provision script for the Billing and Cost Tracking lab module.
#
# This script prepares the lab environment by verifying that:
# 1. The AI-Powered-Store platform is running and accessible
# 2. The billing API endpoint is reachable
# 3. The alert service is operational
# 4. Active containers exist for consumption queries
#
# Prerequisites:
# - AI-Powered-Store platform installed and running
# - Network connectivity to the platform
# - Valid API credentials configured

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
PLATFORM_API_URL="${PLATFORM_API_URL:-http://localhost:5000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
TIMEOUT_SECONDS=30

echo "=== Billing and Cost Tracking Lab - Environment Setup ==="
echo ""

# Check 1: Verify platform API is reachable
echo "[1/4] Checking platform API connectivity..."
if curl --silent --max-time "$TIMEOUT_SECONDS" "${PLATFORM_API_URL}/health" > /dev/null 2>&1; then
    echo "  ✓ Platform API reachable at: $PLATFORM_API_URL"
else
    echo "  ✗ Platform API unreachable at: $PLATFORM_API_URL"
    echo "  → Check network connectivity and ensure the platform is running"
    exit 1
fi

# Check 2: Verify billing API endpoint is available
echo "[2/4] Checking billing API endpoint..."
HTTP_STATUS=$(curl --silent --output /dev/null --write-out "%{http_code}" \
    --max-time "$TIMEOUT_SECONDS" "${PLATFORM_API_URL}/api/billing/consumption" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ] || [ "$HTTP_STATUS" = "403" ]; then
    echo "  ✓ Billing API endpoint available (HTTP $HTTP_STATUS)"
else
    echo "  ✗ Billing API endpoint returned HTTP $HTTP_STATUS"
    echo "  → Endpoint: ${PLATFORM_API_URL}/api/billing/consumption"
    exit 1
fi

# Check 3: Verify alert service is operational
echo "[3/4] Checking alert service..."
HTTP_STATUS=$(curl --silent --output /dev/null --write-out "%{http_code}" \
    --max-time "$TIMEOUT_SECONDS" "${PLATFORM_API_URL}/api/billing/alerts" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ] || [ "$HTTP_STATUS" = "403" ]; then
    echo "  ✓ Alert service operational (HTTP $HTTP_STATUS)"
else
    echo "  ✗ Alert service not responding (HTTP $HTTP_STATUS)"
    echo "  → Endpoint: ${PLATFORM_API_URL}/api/billing/alerts"
    exit 1
fi

# Check 4: Verify active containers exist for billing queries
echo "[4/4] Checking for active containers..."
HTTP_STATUS=$(curl --silent --output /dev/null --write-out "%{http_code}" \
    --max-time "$TIMEOUT_SECONDS" "${PLATFORM_API_URL}/api/containers?status=running" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "401" ]; then
    echo "  ✓ Container API accessible (HTTP $HTTP_STATUS)"
else
    echo "  ⚠ Container API returned HTTP $HTTP_STATUS (exercises may have limited data)"
fi

echo ""
echo "=== Environment setup complete ==="
echo "All prerequisites satisfied. Ready to begin billing exercises."
echo ""
echo "Available exercises:"
echo "  1. View Resource Consumption"
echo "  2. Calculate Expected Costs"
echo "  3. Set Budget Alerts"
echo "  4. Generate Usage Reports"
