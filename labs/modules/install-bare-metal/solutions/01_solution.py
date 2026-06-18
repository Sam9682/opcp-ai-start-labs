"""Reference solution for Exercise 01: System Prerequisites Verification.

This solution demonstrates the expected learner actions and responses
for verifying system prerequisites.
"""

# Expected submission for a passing system
PASSING_SUBMISSION = {
    "os_version": "24.04",
    "cpu_cores": 4,
    "ram_gb": 8.0,
    "disk_free_gb": 50.0,
    "installed_packages": [
        "curl",
        "git",
        "wget",
        "ca-certificates",
        "gnupg",
        "lsb-release",
    ],
}

# Commands the learner should run to gather system info
COMMANDS = [
    "lsb_release -rs",            # Check Ubuntu version
    "nproc",                       # Check CPU cores
    "free -g | awk '/Mem:/{print $2}'",  # Check RAM in GB
    "df -BG / | awk 'NR==2{print $4}'",  # Check free disk in GB
    "dpkg -l curl git wget ca-certificates gnupg lsb-release",  # Check packages
]

# If packages are missing, install them
INSTALL_MISSING = """
sudo apt-get update
sudo apt-get install -y curl git wget ca-certificates gnupg lsb-release
"""
