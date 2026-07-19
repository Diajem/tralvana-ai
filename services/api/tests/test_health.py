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


def test_local_frontend_origin_is_allowed(client):
    res = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:3001"
