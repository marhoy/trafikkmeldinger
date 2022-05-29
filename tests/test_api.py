from starlette.testclient import TestClient


def test_api(client: TestClient) -> None:
    r = client.get("/")
    assert r.status_code == 200
