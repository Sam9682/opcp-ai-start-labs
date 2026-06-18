#!/usr/bin/env bash
# teardown.sh - Clean up the serverless-execution lab environment.
#
# This script removes all artifacts created during the serverless exercises:
#   1. Terminates any lingering serverless containers
#   2. Removes task records from the platform
#   3. Cleans up any cached images used for testing
#
# Usage:
#   bash teardown.sh [--api-url <url>] [--remove-images]
#
# Options:
#   --remove-images   Also remove Docker images pulled for exercises

set -euo pipefail

# --- Configuration ---
API_BASE_URL="${API_BASE_URL:-http://localhost:5000/api}"
REMOVE_IMAGES=false
CONTAINER_LABEL="lab=serverless-execution"

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_BASE_URL="${2:-$API_BASE_URL}"
            shift 2
            ;;
        --remove-images)
            REMOVE_IMAGES=true
            shift
            ;;
        *)
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
    echo -e "${GREEN}[TEARDOWN]${NC} $*"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

# --- Stop and remove lingering serverless containers ---
log "Stopping lingering serverless containers..."
if command -v docker &> /dev/null; then
    # Find containers with the serverless lab label
    CONTAINERS=$(docker ps -a --filter "label=$CONTAINER_LABEL" -q 2>/dev/null || true)
    if [[ -n "$CONTAINERS" ]]; then
        echo "$CONTAINERS" | xargs -r docker rm -f 2>/dev/null || true
        log "Removed $(echo "$CONTAINERS" | wc -l) serverless container(s)."
    else
        log "No lingering serverless containers found."
    fi

    # Also check for containers with serverless-related names
    SERVERLESS_CONTAINERS=$(docker ps -a --filter "name=serverless-task-" -q 2>/dev/null || true)
    if [[ -n "$SERVERLESS_CONTAINERS" ]]; then
        echo "$SERVERLESS_CONTAINERS" | xargs -r docker rm -f 2>/dev/null || true
        log "Removed additional serverless containers by name prefix."
    fi
else
    warn "Docker not available. Cannot clean up containers."
fi

# --- Notify platform to clean up task records ---
log "Requesting task record cleanup from platform..."
CLEANUP_URL="$API_BASE_URL/serverless/cleanup"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$CLEANUP_URL" 2>/dev/null || echo "000")

if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "204" ]]; then
    log "Platform acknowledged task cleanup."
elif [[ "$HTTP_STATUS" == "000" ]]; then
    warn "Cannot reach platform API. Task records may remain."
else
    warn "Platform cleanup returned HTTP $HTTP_STATUS."
fi

# --- Optionally remove test images ---
if [[ "$REMOVE_IMAGES" == true ]]; then
    log "Removing test Docker images..."
    docker rmi python:3.11-slim 2>/dev/null || true
    docker rmi alpine:latest 2>/dev/null || true
    log "Test images removed."
else
    log "Test images preserved (use --remove-images to remove)."
fi

# --- Prune unused resources ---
if command -v docker &> /dev/null; then
    log "Pruning unused Docker resources..."
    docker system prune -f --filter "label=$CONTAINER_LABEL" 2>/dev/null || true
fi

log "============================================"
log "Teardown complete!"
log "============================================"
log "The serverless-execution lab environment has been cleaned up."
