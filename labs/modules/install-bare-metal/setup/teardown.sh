#!/usr/bin/env bash
# teardown.sh - Clean up the install-bare-metal lab environment.
#
# This script removes all artifacts created during the lab exercises:
#   1. Stops and removes Docker containers
#   2. Removes the platform installation directory
#   3. Optionally removes Docker Engine (if --remove-docker flag is set)
#
# Usage:
#   sudo bash teardown.sh [--remove-docker]
#
# Options:
#   --remove-docker   Also remove Docker Engine and docker-compose

set -euo pipefail

# --- Configuration ---
PLATFORM_DIR="/opt/ai-powered-store"
REMOVE_DOCKER=false

# --- Parse arguments ---
for arg in "$@"; do
    case $arg in
        --remove-docker)
            REMOVE_DOCKER=true
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

# --- Check root privileges ---
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[ERROR]${NC} This script must be run as root (use sudo)."
    exit 1
fi

# --- Stop platform containers ---
log "Stopping platform containers..."
if command -v docker &> /dev/null; then
    if [[ -d "$PLATFORM_DIR" && -f "$PLATFORM_DIR/docker-compose.yml" ]]; then
        cd "$PLATFORM_DIR"
        docker compose down --volumes --remove-orphans 2>/dev/null || true
    fi

    # Stop any remaining lab-related containers
    docker ps -a --filter "label=lab=install-bare-metal" -q | xargs -r docker rm -f 2>/dev/null || true
fi

# --- Remove platform directory ---
if [[ -d "$PLATFORM_DIR" ]]; then
    log "Removing platform directory: $PLATFORM_DIR"
    rm -rf "$PLATFORM_DIR"
else
    warn "Platform directory not found: $PLATFORM_DIR"
fi

# --- Optionally remove Docker ---
if [[ "$REMOVE_DOCKER" == true ]]; then
    log "Removing Docker Engine..."
    apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || true
    rm -rf /var/lib/docker /var/lib/containerd
    rm -f /etc/apt/sources.list.d/docker.list
    rm -f /etc/apt/keyrings/docker.gpg
    log "Docker Engine removed."
else
    log "Docker Engine preserved (use --remove-docker to also remove Docker)."
fi

# --- Clean up Docker resources ---
if command -v docker &> /dev/null && [[ "$REMOVE_DOCKER" != true ]]; then
    log "Pruning unused Docker resources..."
    docker system prune -f 2>/dev/null || true
fi

log "============================================"
log "Teardown complete!"
log "============================================"
log "The install-bare-metal lab environment has been cleaned up."
