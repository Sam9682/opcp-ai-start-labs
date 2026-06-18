# AI Store Labs

Interactive training platform for the OPCP AI-Powered-Store. Provides a bilingual (EN/FR) static training website (SkillHub) and a Python-based lab framework for hands-on exercises in Docker containers.

## Architecture Overview

The platform consists of three main components:

1. **SkillHub** — Static HTML training site with bilingual lesson content, progress tracking, and responsive navigation.
2. **Lab Framework** — Python engine that orchestrates, validates, and tracks exercises within isolated Docker containers.
3. **Flask Application** — Serves SkillHub static files and provides REST API endpoints for lab operations.

All services are orchestrated via Docker Compose:

- **Nginx** — Reverse proxy for HTTPS static serving
- **Flask App** (Python 3.11-slim) — Application server with Docker socket access for spawning exercise containers
- **Lab Base** (Python 3.11) — Base image for exercise containers

## Repository Structure

```
opcp-storeai/
├── app.py                  # Flask application entry point
├── Dockerfile              # Flask app container (Python 3.11-slim)
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies (pinned)
├── env_setup.sh            # Prerequisite validation script
├── README.md               # This file
├── src/
│   └── api/                # Flask API blueprints
├── skillhub/               # Static training website
│   ├── index.html          # Landing page with locale detection
│   ├── assets/css/         # OVHcloud-branded styling
│   ├── js/                 # Frontend modules
│   ├── en/                 # English lesson content
│   └── fr/                 # French lesson content
├── labs/
│   ├── core/               # Lab framework core modules
│   ├── modules/            # Lab exercise modules
│   ├── templates/          # Base classes for module authors
│   ├── scripts/            # Utility scripts
│   ├── config/             # YAML configuration
│   ├── base/               # Container base image
│   └── tests/              # Unit and property-based tests
└── nginx/                  # Nginx configuration
```

## Prerequisites

- Python 3.9+
- Docker Engine
- docker-compose v2

Run the validation script to verify all prerequisites:

```bash
chmod +x env_setup.sh
./env_setup.sh
```

## Setup

1. Clone the repository:

```bash
git clone <repo-url> opcp-storeai
cd opcp-storeai
```

2. Validate prerequisites:

```bash
./env_setup.sh
```

3. Start all services:

```bash
docker compose up --build
```

4. Access the platform:
   - SkillHub: https://localhost (via Nginx)
   - Flask API: http://localhost:5000
   - Health check: http://localhost:5000/health

## Development

### Local development (without Docker)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Running tests

```bash
# Python tests (Lab Framework)
pytest labs/tests/ --cov=labs/core --cov-report=term-missing

# JavaScript tests (SkillHub)
npx vitest --run skillhub/tests/
```

## Usage

### SkillHub Training Site

Navigate to the root URL to access the bilingual training site. The site auto-detects your browser language (EN/FR) and provides guided lessons covering:

- Installing the AI-Powered-Store on bare-metal Ubuntu
- Adding, starting, and stopping applications
- Making backups with PostgreSQL and S3
- Modifying applications with AI Developer agent
- Docker applications with MIG GPU profiles
- Serverless Docker execution
- Billing and cost tracking

### Lab Exercises

Lab exercises run in isolated Docker containers. Use the API or web interface to:

1. Start a lab session for a specific module
2. Complete exercises within the containerized environment
3. Submit exercises for automated validation
4. Track progress across modules

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/lab/start` | Start a lab session |
| GET | `/api/lab/status/<session_id>` | Check session status |
| GET | `/api/lab/result/<session_id>/<exercise_id>` | Get exercise result |
| POST | `/api/lab/submit` | Submit exercise for validation |

## License

Internal OPCP training project.
