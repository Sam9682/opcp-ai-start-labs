#!/usr/bin/env bash
# provision.sh - Provision the environment for the modifying-applications lab.
#
# This script prepares the lab environment by:
#   1. Verifying the AI-Powered-Store platform is running
#   2. Ensuring a target application exists and is deployed
#   3. Verifying the AI Developer agent endpoint is accessible
#   4. Setting up a workspace directory for diff operations
#
# Usage:
#   bash provision.sh
#
# Requirements:
#   - AI-Powered-Store platform running (docker-compose up)
#   - At least one application registered and running
#   - Network connectivity to the AI Developer agent endpoint

set -euo pipefail

# --- Configuration ---
PLATFORM_URL="${PLATFORM_URL:-http://localhost:5000}"
AI_DEVELOPER_ENDPOINT="${AI_DEVELOPER_ENDPOINT:-$PLATFORM_URL/api/ai-developer}"
WORKSPACE_DIR="${WORKSPACE_DIR:-/tmp/modifying-applications-lab}"
HEALTH_ENDPOINT="$PLATFORM_URL/health"
TIMEOUT_SECONDS=30

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

# --- Step 1: Verify platform is running ---
log "Verifying AI-Powered-Store platform is accessible..."
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT_SECONDS ]; do
    if curl -sf "$HEALTH_ENDPOINT" > /dev/null 2>&1; then
        log "Platform is healthy at $PLATFORM_URL"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $TIMEOUT_SECONDS ]; then
    error "Platform not reachable at $HEALTH_ENDPOINT after ${TIMEOUT_SECONDS}s. Is docker-compose running?"
fi

# --- Step 2: Verify at least one application is registered ---
log "Checking for registered applications..."
APP_COUNT=$(curl -sf "$PLATFORM_URL/api/apps" 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('apps',[])))" 2>/dev/null || echo "0")

if [ "$APP_COUNT" -eq 0 ]; then
    warn "No applications registered. Please complete the 'Adding Applications' module first."
    warn "Continuing setup - exercises will require a registered application."
fi

log "Found $APP_COUNT registered application(s)."

# --- Step 3: Verify AI Developer agent endpoint ---
log "Checking AI Developer agent endpoint..."
AGENT_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "$AI_DEVELOPER_ENDPOINT" 2>/dev/null || echo "000")

if [ "$AGENT_STATUS" = "000" ]; then
    warn "AI Developer agent endpoint not reachable at $AI_DEVELOPER_ENDPOINT"
    warn "Exercises will need the agent endpoint to be configured."
else
    log "AI Developer agent endpoint responded with HTTP $AGENT_STATUS"
fi

# --- Step 4: Create workspace directory ---
log "Creating workspace directory: $WORKSPACE_DIR"
mkdir -p "$WORKSPACE_DIR"
mkdir -p "$WORKSPACE_DIR/diffs"
mkdir -p "$WORKSPACE_DIR/backups"

# --- Summary ---
log "============================================"
log "Provisioning complete!"
log "============================================"
log "Platform URL:     $PLATFORM_URL"
log "Agent endpoint:   $AI_DEVELOPER_ENDPOINT"
log "Workspace:        $WORKSPACE_DIR"
log "Applications:     $APP_COUNT registered"
log ""
log "Next step: Start Exercise 01 - Invoke AI Developer Agent"
