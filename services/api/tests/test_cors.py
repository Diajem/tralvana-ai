def test_local_planner_port_3015_cors_preflight_succeeds(client):
    response = client.options(
        "/planner/plan",
        headers={
            "Origin": "http://localhost:3015",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3015"
    assert "POST" in response.headers["access-control-allow-methods"]
