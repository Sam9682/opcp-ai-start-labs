#!/bin/bash
# Teardown script for the Adding Applications lab module.
#
# This script cleans up applications registered during the lab exercises
# to restore the platform to its pre-exercise state.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
PLATFORM_API_URL="${PLATFORM_API_URL:-https://store.example.com/api}"
CLI_PATH="${CLI_PATH:-aipoweredstore_cli.py}"

# Applications registered during lab exercises
LAB_APPS=("my-training-app" "api-registered-app" "web-registered-app")

echo "=== Adding Applications Lab - Cleanup ==="
echo ""

# Remove applications registered during exercises
for app_name in "${LAB_APPS[@]}"; do
    echo "Removing application: $app_name"
    if "$CLI_PATH" app delete --name "$app_name" 2>/dev/null; then
        echo "  ✓ Removed: $app_name"
    else
        echo "  - Not found or already removed: $app_name"
    fi
done

echo ""
echo "=== Cleanup complete ==="
