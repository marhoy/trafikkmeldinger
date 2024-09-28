"""Test configuration for pytest."""

import pytest
from starlette.testclient import TestClient

from trafikkmeldinger.api import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """Create a client for test-queries."""
    return TestClient(app)
