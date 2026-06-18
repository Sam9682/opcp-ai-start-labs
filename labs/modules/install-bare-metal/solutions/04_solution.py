"""Reference solution for Exercise 04: Environment Configuration.

This solution demonstrates the expected learner actions for configuring
deploy.ini and running env_setup.sh.
"""

# Expected submission for a passing environment configuration
PASSING_SUBMISSION = {
    "deploy_ini_exists": True,
    "deploy_ini_sections": ["general", "database", "web"],
    "env_setup_exit_code": 0,
    "env_setup_output": "All prerequisites met. Environment ready.",
    "env_vars_set": [
        "FLASK_SECRET_KEY",
        "POSTGRES_PASSWORD",
        "DOMAIN_URL",
        "ADMIN_EMAIL",
    ],
    "python_available": True,
    "docker_available": True,
    "compose_available": True,
}

# Example deploy.ini content
DEPLOY_INI_EXAMPLE = """
[general]
project_name = ai-powered-store
admin_email = admin@example.com

[database]
postgres_host = localhost
postgres_port = 5432
postgres_user = storeai
postgres_password = <secure-random-password>
postgres_db = storeai_db

[web]
domain_url = https://store.example.com
flask_secret_key = <random-hex-string>
flask_port = 5000
nginx_port = 80
nginx_ssl_port = 443
"""

# Commands the learner should run
CONFIG_COMMANDS = """
# Navigate to the project root
cd /opt/ai-powered-store

# Copy the example config
cp deploy.ini.example deploy.ini

# Edit the configuration (use your preferred editor)
nano deploy.ini

# Generate a secret key
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Run the setup script
chmod +x env_setup.sh
./env_setup.sh

# Verify exit code
echo $?  # Should print 0
"""
