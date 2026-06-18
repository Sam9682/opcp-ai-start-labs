# Serverless Docker Execution Lab Module

## Objective

Learn how to run ephemeral serverless containers on the AI-Powered-Store platform
for one-off tasks. Understand the lifecycle of a Serverless_Container: task submission,
execution monitoring, output retrieval, and automatic resource cleanup.

## Prerequisites

- Install Bare-Metal (install-bare-metal)
- Adding Applications (adding-applications)
- Starting Applications (starting-applications)

## Exercises

| # | Exercise Name | Objective |
|---|---------------|-----------|
| 1 | Submit Serverless Task | Submit a Serverless_Container task for execution and confirm acceptance |
| 2 | Monitor Execution Status | Monitor the execution status of a running serverless task |
| 3 | Retrieve Execution Output | Retrieve the output of a completed serverless task |
| 4 | Verify Automatic Cleanup | Verify that container resources are automatically cleaned up after completion |

## Key Concepts

- **Serverless_Container**: An ephemeral Docker container that executes a task and
  terminates automatically without persistent allocation.
- **Task Submission**: The process of submitting a task definition (Docker image, command,
  and optional environment) for serverless execution.
- **Execution Timeout**: Serverless containers have a configurable time limit. If exceeded,
  the container is terminated and a timeout indication is reported.
- **Automatic Cleanup**: After a serverless task completes (or times out), the platform
  automatically terminates the container and releases all compute and network resources
  within 30 seconds.
- **Output Retrieval**: Task output (stdout/stderr) can be retrieved only after the
  container has completed execution. Retrieving output before completion returns the
  current execution status.
