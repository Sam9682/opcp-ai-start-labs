"""Reference solution for Exercise 03: Repository Cloning.

This solution demonstrates the expected learner actions for cloning
the AI-Powered-Store repository.
"""

# Expected submission for a passing repository clone
PASSING_SUBMISSION = {
    "clone_path": "/opt/ai-powered-store",
    "repo_url": "https://forgejo.example.com/opcp/opcp-storeai.git",
    "files_present": [
        "docker-compose.yml",
        "Dockerfile",
        "requirements.txt",
        "app.py",
        "env_setup.sh",
        "README.md",
    ],
    "dirs_present": [
        "src",
        "labs",
        "skillhub",
        "nginx",
    ],
    "is_git_repo": True,
}

# Commands the learner should run
CLONE_COMMANDS = """
# Create target directory
sudo mkdir -p /opt/ai-powered-store

# Clone the repository
sudo git clone https://forgejo.example.com/opcp/opcp-storeai.git /opt/ai-powered-store

# Set ownership to current user
sudo chown -R $USER:$USER /opt/ai-powered-store

# Navigate to the directory
cd /opt/ai-powered-store

# Verify the clone
ls -la
git status
"""
