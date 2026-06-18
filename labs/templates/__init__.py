"""Base template classes for lab module authors.

This package provides abstract base classes that module authors extend
to create new exercises and assessments with a consistent interface.
"""

from labs.templates.exercise_base import Exercise
from labs.templates.assessment_base import Assessment

__all__ = ["Exercise", "Assessment"]
