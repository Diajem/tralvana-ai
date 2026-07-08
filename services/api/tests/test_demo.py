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
