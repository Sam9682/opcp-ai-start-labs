# Reading an Agent Execution Trace

## Objective

Put the morning fundamentals into practice by reading a real agent execution
trace and annotating it. You will label each step of the Think → Act → Observe
loop, identify which opcp-explorer tools the agent invoked, name the stopping
criterion that ended the run, and spot the guardrail that fired. Being able to
read a trace is the core skill for debugging, auditing, and governing agents.

## Prerequisites

- Completed: The Agentic Loop — Think → Act → Observe and its variants
- Completed: Stopping Criteria — Preventing Infinite Loops
- Completed: Connecting an Agent to opcp-explorer

## Exercises

| # | Exercise Name | Objective |
|---|---------------|-----------|
| 1 | Label the Loop Phases | Annotate each trace step as think, act, or observe |
| 2 | Identify the Tools | List the opcp-explorer tools the agent invoked, in order |
| 3 | Name the Stopping Criterion | Identify which stopping criterion ended the run |
| 4 | Spot the Guardrail Trigger | Identify the guardrail that fired and what it prevented |

## The Trace

The trace is provided as a fixture under `setup/sample_trace.py`. It records a
deployment agent that attempts to deploy and start an application on
opcp-explorer, hits a repeated build failure, and is finally stopped by a
guardrail. Each step has an `id`, a `phase` (hidden from the learner in the
exercise view), the raw `content`, and — for act steps — the `tool` invoked.

## How Validation Works

Each exercise ingests your annotation submission and compares it to the expected
key derived from the trace. You receive per-check feedback showing which phases,
tools, stopping criterion, and guardrail you identified correctly.
