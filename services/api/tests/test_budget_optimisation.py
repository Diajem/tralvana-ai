def _trip(
    reference,
    destination,
    *,
    preferred_style="comfort",
    minimum_style="budget",
    priority=3,
):
    return {
        "trip_reference": reference,
        "destination": destination,
        "duration_days": 7,
        "adults": 2,
        "children": 0,
        "priority": priority,
        "preferred_style": preferred_style,
        "minimum_style": minimum_style,
    }


def test_budget_optimise_returns_explainable_portfolio(client):
    response = client.post(
        "/budget/optimise",
        json={
            "portfolio_budget_usd": 16_000,
            "trips": [
                _trip("new-york", "New York", priority=5),
                _trip("paris", "Paris", priority=1),
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["feasible"] is True
    assert body["optimised_total_usd"] <= 16_000
    assert len(body["allocations"]) == 2
    assert body["data_source"] == "ESTIMATED_REGIONAL_RATES"
    assert all(item["tradeoff"] for item in body["allocations"])
    assert all(
        item["data_source"] == "ESTIMATED_REGIONAL_RATES"
        for item in body["allocations"]
    )


def test_budget_optimise_reports_infeasible_minimums_without_hiding_them(
    client,
):
    response = client.post(
        "/budget/optimise",
        json={
            "portfolio_budget_usd": 500,
            "trips": [
                _trip(
                    "new-york",
                    "New York",
                    preferred_style="comfort",
                    minimum_style="balanced",
                )
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["feasible"] is False
    assert body["shortfall_usd"] > 0
    assert body["allocations"][0]["selected_style"] == "balanced"


def test_budget_optimise_rejects_duplicate_trip_references(client):
    trip = _trip("duplicate", "Paris")
    response = client.post(
        "/budget/optimise",
        json={
            "portfolio_budget_usd": 10_000,
            "trips": [trip, {**trip, "destination": "London"}],
        },
    )

    assert response.status_code == 422
    assert "trip_reference values must be unique" in response.text


def test_budget_optimise_rejects_minimum_above_preferred(client):
    response = client.post(
        "/budget/optimise",
        json={
            "portfolio_budget_usd": 10_000,
            "trips": [
                _trip(
                    "paris",
                    "Paris",
                    preferred_style="budget",
                    minimum_style="comfort",
                )
            ],
        },
    )

    assert response.status_code == 422
    assert "minimum_style cannot exceed preferred_style" in response.text


def test_budget_optimise_rejects_empty_portfolio(client):
    response = client.post(
        "/budget/optimise",
        json={"portfolio_budget_usd": 10_000, "trips": []},
    )

    assert response.status_code == 422
