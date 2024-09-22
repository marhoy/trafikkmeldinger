"""Test the API."""

from starlette.testclient import TestClient


def test_api(client: TestClient) -> None:
    """Test API endpoint."""
    r = client.get("/")
    assert r.status_code == 200
