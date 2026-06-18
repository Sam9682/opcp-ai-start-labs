#!/usr/bin/env bash
# provision.sh - Provision a clean Ubuntu environment for the install-bare-metal lab.
#
# This script prepares a fresh Ubuntu 22.04 or 24.04 system for the
# installation exercises by:
#   1. Removing any pre-existing Docker or platform artifacts
#   2. Updating the package index
#   3. Installing minimal base dependencies
#   4. Creating the target directory for the platform
#
# Usage:
#   sudo bash provision.sh
#
# Requirements:
#   - Ubuntu 22.04 or 24.04 LTS
#   - Root or sudo privileges
#   - Internet connectivity

set -euo pipefail

# --- Configuration ---
PLATFORM_DIR="/opt/ai-powered-store"
LOG_FILE="/var/log/lab-provision.log"

# --- Colors for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[PROVISION]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

# --- Check root privileges ---
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root (use sudo)."
fi

# --- Verify Ubuntu version ---
log "Verifying Ubuntu version..."
if command -v lsb_release &> /dev/null; then
    OS_VERSION=$(lsb_release -rs)
    if [[ "$OS_VERSION" != "22.04" && "$OS_VERSION" != "24.04" ]]; then
        error "Unsupported Ubuntu version: $OS_VERSION. Required: 22.04 or 24.04 LTS."
    fi
    log "Ubuntu $OS_VERSION LTS detected."
else
    warn "lsb_release not found. Cannot verify Ubuntu version."
fi

# --- Remove pre-existing Docker artifacts ---
log "Removing pre-existing Docker installations..."
apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
apt-get purge -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin 2>/dev/null || true

# Remove Docker data directories
if [[ -d /var/lib/docker ]]; then
    warn "Removing /var/lib/docker..."
    rm -rf /var/lib/docker
fi

if [[ -d /var/lib/containerd ]]; then
    warn "Removing /var/lib/containerd..."
    rm -rf /var/lib/containerd
fi

# Remove Docker apt sources
rm -f /etc/apt/sources.list.d/docker.list
rm -f /etc/apt/keyrings/docker.gpg

# --- Remove pre-existing platform artifacts ---
log "Removing pre-existing platform artifacts..."
if [[ -d "$PLATFORM_DIR" ]]; then
    warn "Removing existing $PLATFORM_DIR..."
    rm -rf "$PLATFORM_DIR"
fi

# Stop and remove any platform containers
if command -v docker &> /dev/null; then
    docker stop $(docker ps -aq) 2>/dev/null || true
    docker rm $(docker ps -aq) 2>/dev/null || true
    docker network prune -f 2>/dev/null || true
    docker volume prune -f 2>/dev/null || true
fi

# --- Update package index ---
log "Updating package index..."
apt-get update -y

# --- Install minimal base dependencies ---
log "Installing base dependencies..."
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    wget \
    git \
    software-properties-common

# --- Create target directory ---
log "Creating platform directory: $PLATFORM_DIR"
mkdir -p "$PLATFORM_DIR"

# Set ownership to the sudo user (if run via sudo)
if [[ -n "${SUDO_USER:-}" ]]; then
    chown "$SUDO_USER:$SUDO_USER" "$PLATFORM_DIR"
    log "Set ownership of $PLATFORM_DIR to $SUDO_USER."
fi

# --- Clean apt cache ---
log "Cleaning apt cache..."
apt-get clean
rm -rf /var/lib/apt/lists/*

# --- Summary ---
log "============================================"
log "Provisioning complete!"
log "============================================"
log "Environment is ready for the install-bare-metal exercises."
log "- Docker: removed (learner will install)"
log "- Platform directory: $PLATFORM_DIR (empty)"
log "- Base packages: installed"
log ""
log "Next step: Start Exercise 01 - System Prerequisites Verification"
