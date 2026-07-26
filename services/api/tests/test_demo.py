def test_demo_returns_200(client):
    res = client.post("/demo/japan-football-food")
    assert res.status_code == 200


def test_demo_has_all_pipeline_sections(client):
    body = client.post("/demo/japan-football-food").json()
    required_keys = {
        "demo_id", "generated_at", "traveller", "dna",
        "goal", "conversation", "knowledge_insights",
        "trip_plan", "pipeline_summary",
    }
    assert required_keys.issubset(body.keys())


def test_demo_traveller_is_alex_okafor(client):
    body = client.post("/demo/japan-football-food").json()
    assert body["traveller"]["name"] == "Alex Okafor"


def test_demo_dna_has_primary_type(client):
    body = client.post("/demo/japan-football-food").json()
    dna = body["dna"]
    assert "primary_type" in dna
    assert dna["primary_type"]
    assert 0.0 <= dna["confidence"] <= 1.0


def test_demo_trip_plan_has_itinerary(client):
    body = client.post("/demo/japan-football-food").json()
    assert len(body["trip_plan"]["draft_itinerary"]) == 10


def test_demo_pipeline_completes_7_stages(client):
    body = client.post("/demo/japan-football-food").json()
    assert body["pipeline_summary"]["stages_completed"] == 7


def test_demo_knowledge_insights_includes_tokyo(client):
    body = client.post("/demo/japan-football-food").json()
    assert body["knowledge_insights"]["destination_city"] == "Tokyo"


def test_demo_does_not_write_shared_goal_trip_or_conversation_state(client):
    from ai.concierge.conversation_engine import conversation_engine
    from app.domains.goals.service import goal_service
    from app.domains.trips.service import trip_planning_service

    goals_before = goal_service.list_by_traveller("demo-traveller-001")
    trips_before = trip_planning_service.list_by_traveller("demo-traveller-001")

    body = client.post("/demo/japan-football-food").json()

    assert goal_service.list_by_traveller("demo-traveller-001") == goals_before
    assert trip_planning_service.list_by_traveller("demo-traveller-001") == trips_before
    assert conversation_engine.get_session(body["conversation"]["conversation_id"]) is None
