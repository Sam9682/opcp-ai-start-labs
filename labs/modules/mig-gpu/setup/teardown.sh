#!/bin/bash
# Teardown script for the Docker Applications with MIG GPU lab module.
#
# This script cleans up GPU allocations and deployed applications
# created during the lab exercises to restore the platform to its
# pre-exercise state.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
PLATFORM_API_URL="${PLATFORM_API_URL:-https://store.example.com/api}"
CLI_PATH="${CLI_PATH:-aipoweredstore_cli.py}"

# Applications deployed during lab exercises
LAB_APPS=("my-gpu-app" "mig-training-app")

echo "=== Docker Applications with MIG GPU Lab - Cleanup ==="
echo ""

# Step 1: Release GPU allocations
echo "[1/2] Releasing GPU allocations..."
for app_name in "${LAB_APPS[@]}"; do
    echo "  Releasing GPU for: $app_name"
    if "$CLI_PATH" gpu release --app "$app_name" 2>/dev/null; then
        echo "    ✓ GPU released: $app_name"
    else
        echo "    - No active GPU allocation for: $app_name"
    fi
done

# Step 2: Stop and remove deployed applications
echo "[2/2] Stopping deployed applications..."
for app_name in "${LAB_APPS[@]}"; do
    echo "  Stopping: $app_name"
    if "$CLI_PATH" deploy --app "$app_name" --action stop 2>/dev/null; then
        echo "    ✓ Stopped: $app_name"
    else
        echo "    - Not running or already stopped: $app_name"
    fi
done

echo ""
echo "=== Cleanup complete ==="
echo "All GPU allocations released and lab applications stopped."
