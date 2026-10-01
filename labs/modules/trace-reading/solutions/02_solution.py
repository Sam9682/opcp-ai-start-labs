"""Reference solution for Exercise 2: Identify the Tools."""

import importlib

_trace = importlib.import_module(
    "labs.modules.trace-reading.setup.sample_trace"
)


def submission() -> dict:
    return {"tools_in_order": _trace.tools_in_order()}
