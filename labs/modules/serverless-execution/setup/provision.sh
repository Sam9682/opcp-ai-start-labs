#!/usr/bin/env bash
# provision.sh - Provision environment for the serverless-execution lab module.
#
# This script prepares the platform for serverless container exercises by:
#   1. Verifying the platform is running and healthy
#   2. Confirming the serverless API endpoint is available
#   3. Pulling a lightweight test Docker image for exercises
#   4. Verifying Docker socket access for container management
#
# Usage:
#   bash provision.sh [--api-url <url>]
#
# Requirements:
#   - AI-Powered-Store platform running (install-bare-metal completed)
#   - Docker available with socket access
#   - Network connectivity to the platform API

set -euo pipefail

# --- Configuration ---
API_BASE_URL="${API_BASE_URL:-http://localhost:5000/api}"
TEST_IMAGE="python:3.11-slim"
HEALTH_TIMEOUT_SECONDS=30

# --- Parse arguments ---
for arg in "$@"; do
    case $arg in
        --api-url)
            shift
            API_BASE_URL="${1:-$API_BASE_URL}"
            shift
            ;;
    esac
done

# --- Colors for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[PROVISION]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    exit 1
}

# --- Verify Docker is available ---
log "Checking Docker availability..."
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Complete the install-bare-metal module first."
fi

if ! docker info &> /dev/null; then
    error "Docker daemon is not running or not accessible."
fi
log "Docker is available."

# --- Verify platform health ---
log "Checking platform health at $API_BASE_URL..."
HEALTH_URL="${API_BASE_URL%/api}/health"
START_TIME=$(date +%s)

while true; do
    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [[ $ELAPSED -ge $HEALTH_TIMEOUT_SECONDS ]]; then
        error "Platform health check timed out after ${HEALTH_TIMEOUT_SECONDS}s. Is the platform running?"
    fi

    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo "000")
    if [[ "$HTTP_STATUS" == "200" ]]; then
        log "Platform is healthy."
        break
    fi

    sleep 2
done

# --- Verify serverless API endpoint ---
log "Verifying serverless API endpoint..."
SERVERLESS_URL="$API_BASE_URL/serverless/tasks"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$SERVERLESS_URL" 2>/dev/null || echo "000")

if [[ "$HTTP_STATUS" == "000" ]]; then
    error "Cannot reach serverless API at $SERVERLESS_URL"
fi
log "Serverless API endpoint reachable (HTTP $HTTP_STATUS)."

# --- Pull test Docker image ---
log "Pulling test Docker image: $TEST_IMAGE"
if docker pull "$TEST_IMAGE" &> /dev/null; then
    log "Test image pulled successfully."
else
    warn "Could not pull $TEST_IMAGE. Exercises may still work if the image is cached."
fi

# --- Verify Docker socket access ---
log "Verifying Docker socket access for container management..."
if [[ -S /var/run/docker.sock ]]; then
    log "Docker socket is accessible at /var/run/docker.sock"
else
    warn "Docker socket not found at /var/run/docker.sock. Container operations may fail."
fi

# --- Summary ---
log "============================================"
log "Provisioning complete!"
log "============================================"
log "Environment is ready for serverless-execution exercises."
log "- Platform API: $API_BASE_URL"
log "- Serverless endpoint: $SERVERLESS_URL"
log "- Test image: $TEST_IMAGE"
log ""
log "Next step: Start Exercise 01 - Submit Serverless Task"
