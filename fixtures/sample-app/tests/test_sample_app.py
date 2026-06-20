"""Unit tests for the sample-app fixture."""

from sample_app.server import HealthHandler


def test_health_handler_class_exists() -> None:
    assert HealthHandler is not None
