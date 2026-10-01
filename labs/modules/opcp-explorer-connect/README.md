# Connecting an Agent to opcp-explorer

## Objective

Learn how an AI agent uses the opcp-explorer platform (AI-Powered-Store) as its
toolset. This module covers the three interfaces an agent can act through — the
REST API, the CLI, and MCP (Model Context Protocol) — how to authenticate with a
scoped token, and how to perform a basic tool call such as listing or deploying
an application. These are the "tools" component from the morning anatomy lesson,
made concrete.

By default every exercise runs against a **simulated** endpoint so the lab works
offline inside the isolated exercise container. An opt-in `live_mode` lets you
point the same exercise at a running opcp-explorer instance.

## Prerequisites

- Completed: Anatomy of an AI Agent (the seven core components)
- Familiarity with REST, CLI, and the idea of MCP tool servers
- (Live mode only) A reachable opcp-explorer instance and a scoped API token

## Exercises

| # | Exercise Name | Objective |
|---|---------------|-----------|
| 1 | Discover the Tool Surface | Enumerate the API/CLI/MCP operations opcp-explorer exposes as agent tools |
| 2 | Authenticate with a Scoped Token | Construct a least-privilege authentication context for the agent |
| 3 | Perform a Basic Tool Call | Build and (simulated) execute a deploy/list operation, then read the result |

## Simulated vs Live Mode

Each exercise accepts a `live_mode` boolean in its submission (default `false`).

- **Simulated (default):** the exercise constructs the request and validates its
  structure and auth context against a built-in fixture. No network is used.
- **Live (opt-in):** the submission additionally carries `base_url` and a token
  reference. The exercise validates the live connection parameters are
  well-formed. Because the exercise container runs with `network_mode="none"`,
  the actual HTTP/CLI/MCP call is expected to be executed by the Flask app /
  adapter layer outside the container. Never embed real secrets in a submission;
  pass a token *reference* (an env var or secret name), not the token value.

## Security note

Live mode trades the container's network isolation for real connectivity. Treat
it as a deliberate, reviewed step: use a least-privilege token, prefer a staging
instance, and keep the simulated path as the default for teaching.
