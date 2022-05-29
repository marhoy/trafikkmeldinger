from typing import Generator

import pytest
from starlette.testclient import TestClient

from trafikkmeldinger.api import app


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, None, None]:
    """Create a client for test-queries."""
    testclient = TestClient(app)
    yield testclient
