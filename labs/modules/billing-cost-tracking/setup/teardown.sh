#!/bin/bash
# Teardown script for the Billing and Cost Tracking lab module.
#
# This script cleans up resources created during the lab exercises:
# - Removes budget alerts configured during Exercise 3
# - Clears any simulated overage data
# - Removes generated report artifacts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
PLATFORM_API_URL="${PLATFORM_API_URL:-http://localhost:5000}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
TIMEOUT_SECONDS=30

echo "=== Billing and Cost Tracking Lab - Cleanup ==="
echo ""

# Remove budget alerts created during exercises
echo "[1/3] Removing lab budget alerts..."
if [ -n "$AUTH_TOKEN" ]; then
    ALERTS_RESPONSE=$(curl --silent --max-time "$TIMEOUT_SECONDS" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        "${PLATFORM_API_URL}/api/billing/alerts" 2>/dev/null || echo "")

    if [ -n "$ALERTS_RESPONSE" ]; then
        # Attempt to delete alerts with lab-related names
        for alert_name in "lab-budget-alert" "training-budget-alert" "test-budget-alert"; do
            if curl --silent --max-time "$TIMEOUT_SECONDS" \
                -X DELETE \
                -H "Authorization: Bearer $AUTH_TOKEN" \
                "${PLATFORM_API_URL}/api/billing/alerts?name=${alert_name}" > /dev/null 2>&1; then
                echo "  ✓ Removed alert: $alert_name"
            else
                echo "  - Not found or already removed: $alert_name"
            fi
        done
    else
        echo "  - Could not fetch alerts (API unavailable or no auth token)"
    fi
else
    echo "  - Skipping alert cleanup (no AUTH_TOKEN configured)"
fi

# Clear simulated overage data
echo "[2/3] Clearing simulated billing data..."
if [ -n "$AUTH_TOKEN" ]; then
    if curl --silent --max-time "$TIMEOUT_SECONDS" \
        -X POST \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        "${PLATFORM_API_URL}/api/billing/reset-simulations" > /dev/null 2>&1; then
        echo "  ✓ Simulated billing data cleared"
    else
        echo "  - No simulated data to clear or endpoint unavailable"
    fi
else
    echo "  - Skipping simulation cleanup (no AUTH_TOKEN configured)"
fi

# Remove local report artifacts
echo "[3/3] Cleaning up local report files..."
REPORTS_DIR="${MODULE_DIR}/reports"
if [ -d "$REPORTS_DIR" ]; then
    rm -rf "$REPORTS_DIR"
    echo "  ✓ Removed local reports directory"
else
    echo "  - No local reports directory found"
fi

echo ""
echo "=== Cleanup complete ==="
