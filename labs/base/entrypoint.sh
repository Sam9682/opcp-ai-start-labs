#!/bin/bash
set -e

# AI Store Labs - Exercise Container Entrypoint
# Sets up the exercise environment before handing off to the exercise command.

# Ensure results directory exists and is writable
mkdir -p "${LAB_RESULTS_DIR:-/lab/results}"

# Set up exercise environment variables if a config file is mounted
if [ -f /lab/config/exercise.env ]; then
    set -a
    source /lab/config/exercise.env
    set +a
fi

# Run setup script if one is provided for the exercise module
if [ -f /lab/setup/provision.sh ]; then
    echo "[lab-entrypoint] Running module setup script..."
    bash /lab/setup/provision.sh
fi

# Switch to learner user for exercise execution (if not already running as root for Docker access)
if [ "$(id -u)" = "0" ] && [ "${RUN_AS_ROOT:-false}" != "true" ]; then
    chown -R learner:learner /lab
    exec gosu learner "$@"
else
    exec "$@"
fi
