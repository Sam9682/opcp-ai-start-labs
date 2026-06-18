"""Reference solution for Exercise 05: Platform Startup.

This solution demonstrates the expected learner actions for starting
the platform and verifying service health.
"""

# Expected submission for a passing platform startup
PASSING_SUBMISSION = {
    "clone_path": "/opt/ai-powered-store",
    "deploy_exit_code": 0,
    "deploy_output": "All services started successfully.",
    "flask_status": "healthy",
    "postgresql_status": "healthy",
    "nginx_status": "healthy",
    "dashboard_accessible": True,
    "dashboard_url": "http://localhost",
}

# Commands the learner should run
STARTUP_COMMANDS = """
# Navigate to the project root
cd /opt/ai-powered-store

# Run the deployment control plan
chmod +x deployControlPlan.sh
./deployControlPlan.sh

# Wait for services to start (check every 5 seconds, up to 120s)
echo "Waiting for services to start..."

# Check Docker Compose services
docker compose ps

# Check Flask health endpoint
curl -s http://localhost:5000/health
# Expected: {"status": "healthy"}

# Check PostgreSQL
docker exec postgres pg_isready -U postgres
# Expected: accepting connections

# Check Nginx
curl -sI http://localhost:80
# Expected: HTTP/1.1 200 OK or 301 redirect

# Check web dashboard
curl -s http://localhost | head -20
"""

# Troubleshooting commands if services don't start
TROUBLESHOOTING = """
# View all container logs
docker compose logs

# View specific service logs
docker compose logs flask-app
docker compose logs postgres
docker compose logs nginx

# Check resource usage
docker stats --no-stream

# Restart a specific service
docker compose restart flask-app

# Full restart
docker compose down && docker compose up -d
"""
