#!/bin/bash
# Provision script for the Docker Applications with MIG GPU lab module.
#
# This script prepares the lab environment by verifying that:
# 1. The AI-Powered-Store platform is running and accessible
# 2. GPU hardware and drivers are available
# 3. MIG mode is enabled on the GPU
# 4. The platform GPU API endpoint is reachable
#
# Prerequisites:
# - AI-Powered-Store platform installed and running
# - NVIDIA GPU with MIG support (A30, A100, H100)
# - NVIDIA drivers and nvidia-smi installed
# - Network connectivity to the platform

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODULE_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
PLATFORM_API_URL="${PLATFORM_API_URL:-https://store.example.com/api}"
CLI_PATH="${CLI_PATH:-aipoweredstore_cli.py}"
TIMEOUT_SECONDS=30

echo "=== Docker Applications with MIG GPU Lab - Environment Setup ==="
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

# Check 2: Verify NVIDIA drivers and GPU presence
echo "[2/4] Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    if [ -n "$GPU_NAME" ]; then
        echo "  ✓ GPU detected: $GPU_NAME"
    else
        echo "  ✗ nvidia-smi available but no GPU detected"
        echo "  → Ensure NVIDIA GPU is properly installed and drivers are loaded"
        exit 1
    fi
else
    echo "  ✗ nvidia-smi not found"
    echo "  → Install NVIDIA drivers: apt install nvidia-driver-535"
    exit 1
fi

# Check 3: Verify MIG mode is enabled
echo "[3/4] Checking MIG mode status..."
MIG_STATUS=$(nvidia-smi --query-gpu=mig.mode.current --format=csv,noheader 2>/dev/null | head -1)
if [ "$MIG_STATUS" = "Enabled" ]; then
    echo "  ✓ MIG mode is enabled"
else
    echo "  ✗ MIG mode is not enabled (status: ${MIG_STATUS:-unknown})"
    echo "  → Enable MIG: nvidia-smi -i 0 -mig 1 (requires reboot)"
    exit 1
fi

# Check 4: Verify GPU profiles API endpoint
echo "[4/4] Checking GPU profiles API endpoint..."
HTTP_STATUS=$(curl --silent --output /dev/null --write-out "%{http_code}" \
    --max-time "$TIMEOUT_SECONDS" "${PLATFORM_API_URL}/gpu/profiles" 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    PROFILE_COUNT=$(curl --silent --max-time "$TIMEOUT_SECONDS" \
        "${PLATFORM_API_URL}/gpu/profiles" 2>/dev/null | \
        python3 -c "import sys,json; data=json.load(sys.stdin); print(len(data.get('profiles',[])))" 2>/dev/null || echo "0")
    echo "  ✓ GPU profiles endpoint available ($PROFILE_COUNT profiles found)"
else
    echo "  ✗ GPU profiles endpoint returned HTTP $HTTP_STATUS"
    echo "  → Endpoint: ${PLATFORM_API_URL}/gpu/profiles"
    exit 1
fi

echo ""
echo "=== Environment setup complete ==="
echo "All prerequisites satisfied. Ready to begin MIG GPU exercises."
