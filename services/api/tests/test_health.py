def test_health_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_root_returns_running(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "running"
    assert "Tralvana" in body["message"]
