"""Reference solution for Exercise 02: Docker Installation.

This solution demonstrates the expected learner actions and responses
for installing Docker Engine and docker-compose v2.
"""

# Expected submission for a passing Docker installation
PASSING_SUBMISSION = {
    "docker_version": "24.0.7",
    "compose_version": "2.21.0",
    "docker_running": True,
    "user_in_docker_group": True,
}

# Full installation commands for a clean Ubuntu system
INSTALL_COMMANDS = """
# Remove old Docker packages
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Set up Docker's GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl enable docker
sudo systemctl start docker

# Verify
docker --version
docker compose version
"""
