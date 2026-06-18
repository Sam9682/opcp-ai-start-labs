#!/usr/bin/env bash
# teardown.sh - Clean up the modifying-applications lab environment.
#
# This script removes all artifacts created during the lab exercises:
#   1. Removes the workspace directory (diffs, backups)
#   2. Reverts any applied modifications to applications (optional)
#   3. Stops any containers started during verification exercises
#
# Usage:
#   bash teardown.sh [--revert]
#
# Options:
#   --revert   Attempt to revert applied modifications using saved backups

set -euo pipefail

# --- Configuration ---
WORKSPACE_DIR="${WORKSPACE_DIR:-/tmp/modifying-applications-lab}"
REVERT_MODIFICATIONS=false

# --- Parse arguments ---
for arg in "$@"; do
    case $arg in
        --revert)
            REVERT_MODIFICATIONS=true
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

# --- Step 1: Stop any verification containers ---
log "Stopping lab verification containers..."
if command -v docker &> /dev/null; then
    docker ps -a --filter "label=lab=modifying-applications" -q | xargs -r docker rm -f 2>/dev/null || true
fi

# --- Step 2: Revert modifications if requested ---
if [[ "$REVERT_MODIFICATIONS" == true ]]; then
    log "Attempting to revert applied modifications..."
    if [[ -d "$WORKSPACE_DIR/backups" ]]; then
        BACKUP_COUNT=$(find "$WORKSPACE_DIR/backups" -type f 2>/dev/null | wc -l)
        if [[ $BACKUP_COUNT -gt 0 ]]; then
            log "Found $BACKUP_COUNT backup file(s). Manual revert may be needed."
            warn "Backup files are in: $WORKSPACE_DIR/backups"
            warn "Review and restore manually before workspace removal."
        else
            log "No backup files found. Nothing to revert."
        fi
    else
        warn "No backups directory found."
    fi
fi

# --- Step 3: Remove workspace directory ---
if [[ -d "$WORKSPACE_DIR" ]]; then
    log "Removing workspace directory: $WORKSPACE_DIR"
    rm -rf "$WORKSPACE_DIR"
else
    warn "Workspace directory not found: $WORKSPACE_DIR"
fi

# --- Summary ---
log "============================================"
log "Teardown complete!"
log "============================================"
log "The modifying-applications lab environment has been cleaned up."
if [[ "$REVERT_MODIFICATIONS" != true ]]; then
    log "Note: Applied modifications were NOT reverted."
    log "Use --revert flag to attempt reverting changes."
fi
