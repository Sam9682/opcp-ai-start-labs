"""Sample agent execution trace for the trace-reading workshop.

A deployment agent (ReAct loop) attempts to deploy and start an application on
opcp-explorer. The build fails repeatedly; after three identical failures a
guardrail (error-threshold stopping criterion) halts the run.

Each step is a dict with:
    - id:      stable step identifier ("s1", "s2", ...)
    - phase:   "think" | "act" | "observe"  (the answer key for exercise 1)
    - content: the raw trace line shown to the learner
    - tool:    for act steps, the opcp-explorer tool invoked (else None)

The exercises import this fixture and derive their expected answer keys from it,
so the trace is the single source of truth.
"""

TRACE = [
    {
        "id": "s1",
        "phase": "think",
        "content": "Goal: deploy 'demo-api' and confirm it is healthy. "
                   "I'll start by listing current apps.",
        "tool": None,
    },
    {
        "id": "s2",
        "phase": "act",
        "content": "call list_apps()",
        "tool": "list_apps",
    },
    {
        "id": "s3",
        "phase": "observe",
        "content": "apps=[{demo-static: running}]. 'demo-api' is not deployed.",
        "tool": None,
    },
    {
        "id": "s4",
        "phase": "think",
        "content": "'demo-api' is missing. I'll deploy it from the repo.",
        "tool": None,
    },
    {
        "id": "s5",
        "phase": "act",
        "content": "call deploy_app(repo_url=..., app_name='demo-api')",
        "tool": "deploy_app",
    },
    {
        "id": "s6",
        "phase": "observe",
        "content": "state=deploying. Build started.",
        "tool": None,
    },
    {
        "id": "s7",
        "phase": "observe",
        "content": "build FAILED: missing dependency 'libfoo'. attempt 1.",
        "tool": None,
    },
    {
        "id": "s8",
        "phase": "think",
        "content": "Build failed. I'll retry the deploy as-is.",
        "tool": None,
    },
    {
        "id": "s9",
        "phase": "act",
        "content": "call deploy_app(repo_url=..., app_name='demo-api')",
        "tool": "deploy_app",
    },
    {
        "id": "s10",
        "phase": "observe",
        "content": "build FAILED: missing dependency 'libfoo'. attempt 2.",
        "tool": None,
    },
    {
        "id": "s11",
        "phase": "think",
        "content": "Same error. I'll retry once more.",
        "tool": None,
    },
    {
        "id": "s12",
        "phase": "act",
        "content": "call deploy_app(repo_url=..., app_name='demo-api')",
        "tool": "deploy_app",
    },
    {
        "id": "s13",
        "phase": "observe",
        "content": "build FAILED: missing dependency 'libfoo'. attempt 3.",
        "tool": None,
    },
    {
        "id": "s14",
        "phase": "observe",
        "content": "GUARDRAIL error_threshold tripped: same error repeated 3x. "
                   "Run halted. No further deploy attempts permitted.",
        "tool": None,
    },
]


# --- Derived answer keys (single source of truth for the exercises) ----------

def phase_key() -> dict:
    """Map of step id -> correct phase label."""
    return {step["id"]: step["phase"] for step in TRACE}


def tools_in_order() -> list:
    """Ordered list of tools invoked across the trace (act steps only)."""
    return [step["tool"] for step in TRACE if step["phase"] == "act"]


def distinct_tools() -> set:
    """Set of distinct tools invoked."""
    return {step["tool"] for step in TRACE if step["phase"] == "act"}


# The run ended because the same error repeated three times — an error-threshold
# stopping criterion, enforced by a guardrail.
STOPPING_CRITERION = "error_threshold"
STOPPING_CRITERION_ALIASES = {
    "error_threshold",
    "error-threshold",
    "max_errors",
    "repeated_error",
    "repeated-error",
    "consecutive_errors",
}

GUARDRAIL_LAYER = "operational_limits"
GUARDRAIL_LAYER_ALIASES = {
    "operational_limits",
    "operational-limits",
    "operational limits",
    "limits",
    "operational",
}

# The step at which the guardrail fired.
GUARDRAIL_STEP_ID = "s14"


def learner_view() -> list:
    """The trace as shown to the learner, with phase labels removed."""
    return [
        {"id": s["id"], "content": s["content"]}
        for s in TRACE
    ]
