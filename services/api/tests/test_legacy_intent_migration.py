from pathlib import Path


def test_destination_question_uses_destination_intelligence(client):
    response = client.post(
        "/conversation/message",
        json={"message": "tell me about Tokyo"},
    ).json()

    assert response["intent"] == "DESTINATION_QUESTION"
    assert "**Destinations:**" in response["response"]
    assert response["recommended_agents"] == ["destination_intelligence"]


def test_travel_advice_uses_destination_intelligence(client):
    response = client.post(
        "/conversation/message",
        json={"message": "travel tips for Tokyo"},
    ).json()

    assert response["intent"] == "TRAVEL_ADVICE"
    assert "**Destinations:**" in response["response"]
    assert response["recommended_agents"] == ["destination_intelligence"]


def test_budget_advice_uses_budget_intelligence(client):
    response = client.post(
        "/conversation/message",
        json={"message": "how expensive is Tokyo"},
    ).json()

    assert response["intent"] == "BUDGET_ADVICE"
    assert "**Budget:**" in response["response"]
    assert response["recommended_agents"] == ["budget_intelligence"]


def test_modify_trip_reuses_active_trip_and_reruns_trip_brain(client):
    original = client.post(
        "/conversation/message",
        json={"message": "plan a trip to Tokyo in October"},
    ).json()

    modified = client.post(
        "/conversation/message",
        json={
            "message": "change my flight to 15 November",
            "conversation_id": original["conversation_id"],
        },
    ).json()

    assert modified["intent"] == "MODIFY_TRIP"
    assert modified["trip_id"] == original["trip_id"]
    # A single changed departure date is not an exact travel window, so the
    # planner must not fabricate a supplier recommendation.
    assert "**Flights:**" not in modified["response"]
    assert "**Weather:**" in modified["response"]
    assert "Sprint 4" not in modified["response"]
    assert modified["recommended_agents"] == ["trip_brain"]


def test_legacy_orchestration_packages_and_imports_are_retired():
    repository_root = Path(__file__).parents[3]
    for relative_path in ("ai/agents", "ai/manager", "ai/registry"):
        assert not list((repository_root / relative_path).glob("*.py"))

    forbidden_imports = ("ai.manager", "ai.registry", "ai.agents")
    production_roots = ("ai", "services/api/app", "travelos")
    violations: list[str] = []
    for production_root in production_roots:
        for source_file in (repository_root / production_root).rglob("*.py"):
            source = source_file.read_text(encoding="utf-8")
            if any(forbidden in source for forbidden in forbidden_imports):
                violations.append(str(source_file.relative_to(repository_root)))

    assert violations == []
