"""Integration tests for the AI Store Labs platform.

These tests exercise real Docker containers and the full request/response
workflow end to end. They are marked with ``@pytest.mark.integration`` and
skip automatically when Docker is unavailable, so the suite still collects
and runs cleanly in environments without a Docker daemon.
"""
