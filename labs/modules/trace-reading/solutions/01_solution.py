"""Reference solution for Exercise 1: Label the Loop Phases.

The correct phase for every step, derived from the trace fixture.
"""

import importlib

_trace = importlib.import_module(
    "labs.modules.trace-reading.setup.sample_trace"
)


def submission() -> dict:
    return {"labels": _trace.phase_key()}
