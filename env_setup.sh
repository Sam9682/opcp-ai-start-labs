#!/usr/bin/env bash
#
# env_setup.sh - Validates prerequisites for AI Store Labs
#
# Checks:
#   - Python 3.9+ is available
#   - Docker Engine is installed and running
#   - docker-compose v2 is available
#
# Exits with non-zero code and descriptive error if any prerequisite is missing.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

errors=0

echo "=== AI Store Labs - Environment Setup Validation ==="
echo ""

# Check Python 3.9+
echo -n "Checking Python 3.9+ ... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        echo -e "${GREEN}OK${NC} (Python ${PYTHON_VERSION})"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Error: Python 3.9+ is required, but found Python ${PYTHON_VERSION}"
        echo "  Install: sudo apt install python3.11 python3.11-venv"
        errors=$((errors + 1))
    fi
else
    echo -e "${RED}FAIL${NC}"
    echo "  Error: Python 3 is not installed"
    echo "  Install: sudo apt install python3.11 python3.11-venv"
    errors=$((errors + 1))
fi

# Check Docker Engine
echo -n "Checking Docker Engine ... "
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    if docker info &> /dev/null; then
        echo -e "${GREEN}OK${NC} (Docker ${DOCKER_VERSION})"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Error: Docker is installed but the daemon is not running or current user lacks permissions"
        echo "  Fix: sudo systemctl start docker && sudo usermod -aG docker \$USER"
        errors=$((errors + 1))
    fi
else
    echo -e "${RED}FAIL${NC}"
    echo "  Error: Docker Engine is not installed"
    echo "  Install: https://docs.docker.com/engine/install/ubuntu/"
    errors=$((errors + 1))
fi

# Check docker-compose v2
echo -n "Checking docker-compose v2 ... "
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null)
    echo -e "${GREEN}OK${NC} (docker compose ${COMPOSE_VERSION})"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version 2>/dev/null | grep -oP '\d+\.\d+\.\d+' | head -1)
    COMPOSE_MAJOR=$(echo "$COMPOSE_VERSION" | cut -d. -f1)
    if [ "$COMPOSE_MAJOR" -ge 2 ]; then
        echo -e "${GREEN}OK${NC} (docker-compose ${COMPOSE_VERSION})"
    else
        echo -e "${RED}FAIL${NC}"
        echo "  Error: docker-compose v2+ is required, but found v${COMPOSE_VERSION}"
        echo "  Install: https://docs.docker.com/compose/install/"
        errors=$((errors + 1))
    fi
else
    echo -e "${RED}FAIL${NC}"
    echo "  Error: docker-compose v2 is not installed"
    echo "  Install: https://docs.docker.com/compose/install/"
    errors=$((errors + 1))
fi

echo ""

if [ $errors -gt 0 ]; then
    echo -e "${RED}Validation failed: ${errors} prerequisite(s) missing.${NC}"
    exit 1
else
    echo -e "${GREEN}All prerequisites satisfied. Ready to proceed.${NC}"
    exit 0
fi
