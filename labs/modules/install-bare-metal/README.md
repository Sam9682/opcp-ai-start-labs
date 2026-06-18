# Installation on Bare-Metal Ubuntu

## Objective

This lab module guides learners through the complete installation of the AI-Powered-Store platform on a bare-metal Ubuntu server. By the end of this module, learners will have a fully operational platform with Flask, PostgreSQL, and Nginx services running in Docker containers.

## Prerequisites

- Access to a clean Ubuntu 22.04 or 24.04 LTS machine (physical or virtual)
- Basic Linux command-line proficiency
- Internet connectivity for package downloads

## Exercises

| # | Exercise Name | Objective |
|---|--------------|-----------|
| 1 | System Prerequisites Verification | Verify Ubuntu version, CPU, RAM, and disk space meet minimum requirements |
| 2 | Docker Installation | Install Docker Engine and docker-compose v2 on the target system |
| 3 | Repository Cloning | Clone the AI-Powered-Store platform repository and verify contents |
| 4 | Environment Configuration | Configure `deploy.ini` and run `env_setup.sh` to prepare the deployment environment |
| 5 | Platform Startup | Execute `deployControlPlan.sh` and verify all services (Flask, PostgreSQL, Nginx) are healthy |

## Estimated Duration

120 minutes

## Difficulty

Beginner

## Validation

Each exercise includes automated validation checks that verify the learner has correctly completed the step. The final exercise performs a comprehensive health check ensuring all platform services respond within 120 seconds.
