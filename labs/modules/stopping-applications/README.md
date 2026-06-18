# Stopping Applications Lab Module

## Objective

Learn how to gracefully stop running applications on the AI-Powered-Store platform using
the CLI, REST API, and force-stop mechanisms. Understand graceful shutdown semantics,
process termination verification, and timeout recovery strategies.

## Prerequisites

- Install Bare-Metal (install-bare-metal)
- Adding Applications (adding-applications)
- Starting Applications (starting-applications)

## Exercises

| # | Exercise Name | Objective |
|---|---------------|-----------|
| 1 | Stop Application via CLI | Stop a running application using the `aipoweredstore_cli.py` command-line tool |
| 2 | Stop Application via REST API | Stop a running application using `POST /api/deployments` with action "stop" |
| 3 | Confirm Graceful Shutdown | Verify graceful shutdown: process termination, port refusal, and zero exit code |

## Key Concepts

- **Graceful Shutdown**: The application completes in-flight requests and the process exits
  with a zero exit code.
- **Force Stop**: Immediately terminates the application regardless of in-flight request
  completion. Used as a recovery option when graceful stop times out.
- **Termination Verification**: Confirms the process has terminated and its ports refuse
  new connections within 5 seconds of the stop command completing.
- **Timeout Handling**: If a stop operation does not complete within 30 seconds, the
  learner is informed of the timeout and offered force-stop as a recovery option.
