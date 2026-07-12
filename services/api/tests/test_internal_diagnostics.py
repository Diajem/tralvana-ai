"""
GET /internal/providers/status — safe diagnostics output, and
confirmation that the Intelligence Gateway integration introduces no
public API regression (docs/INTELLIGENCE_GATEWAY.md).
"""


class TestDiagnosticsOutput:
    def test_returns_200(self, client):
        res = client.get("/internal/providers/status")
        assert res.status_code == 200

    def test_lists_the_three_integrated_providers(self, client):
        body = client.get("/internal/providers/status").json()
        names = {p["provider_name"] for p in body["providers"]}
        assert {"mock_flight_provider", "mock_accommodation_provider", "mock_weather_provider"} <= names

    def test_every_provider_entry_has_safe_fields_only(self, client):
        # Extended in T-026 (Live Provider Framework) to add provider_type,
        # authentication_configured, last_check_time, request_count, and
        # failure_count — additive, not a regression of T-025's shape.
        body = client.get("/internal/providers/status").json()
        for entry in body["providers"]:
            assert set(entry.keys()) == {
                "capability", "provider_name", "provider_type", "environment", "status",
                "health", "priority", "cache_ttl_seconds", "rate_limit",
                "authentication_configured", "last_check_time", "request_count", "failure_count",
            }

    def test_no_secret_or_credential_field_present_anywhere(self, client):
        body = client.get("/internal/providers/status").json()
        serialized = str(body).lower()
        for forbidden in ("secret", "api_key", "apikey", "password", "token", "credential"):
            assert forbidden not in serialized

    def test_top_level_settings_present(self, client):
        body = client.get("/internal/providers/status").json()
        assert "environment" in body
        assert "cache_enabled" in body
        assert "retry_enabled" in body
        assert "healthcheck_enabled" in body

    def test_flight_provider_reports_available_and_healthy(self, client):
        body = client.get("/internal/providers/status").json()
        flight = next(p for p in body["providers"] if p["provider_name"] == "mock_flight_provider")
        assert flight["status"] == "AVAILABLE"
        assert flight["health"] == "healthy"
        assert flight["capability"] == "FLIGHTS"

    def test_mock_providers_reported_as_provider_type_mock(self, client):
        body = client.get("/internal/providers/status").json()
        flight = next(p for p in body["providers"] if p["provider_name"] == "mock_flight_provider")
        assert flight["provider_type"] == "MOCK"
        assert flight["authentication_configured"] is True

    def test_mock_providers_have_zero_request_and_failure_counts_by_default(self, client):
        body = client.get("/internal/providers/status").json()
        flight = next(p for p in body["providers"] if p["provider_name"] == "mock_flight_provider")
        assert flight["request_count"] >= 0
        assert flight["failure_count"] >= 0


class TestNoPublicAPIRegression:
    def test_conversation_message_response_shape_unchanged(self, client):
        res = client.post("/conversation/message", json={"message": "recommend flights to Tokyo"})
        body = res.json()
        assert set(body.keys()) == {
            "conversation_id", "intent", "response", "confidence", "assumptions",
            "missing_information", "next_actions", "recommended_agents", "goal_id", "trip_id",
        }

    def test_flights_recommend_still_works_end_to_end(self, client):
        res = client.post("/flights/recommend", json={"origin": "LON", "destination": "Tokyo"})
        assert res.status_code == 201
        assert len(res.json()["flight_options"]) > 0

    def test_accommodation_recommend_still_works_end_to_end(self, client):
        res = client.post("/accommodation/recommend", json={"destination": "Tokyo"})
        assert res.status_code == 201
        assert len(res.json()["accommodation_options"]) > 0

    def test_weather_analyse_still_works_end_to_end(self, client):
        res = client.post("/weather/analyse", json={"destination": "Japan", "month_of_travel": 10})
        assert res.status_code == 201
        assert res.json()["weather_status"] is not None

    def test_plan_trip_still_synthesizes_across_modules(self, client):
        res = client.post("/conversation/message", json={
            "message": "I want to plan a trip to Tokyo in October",
        })
        body = res.json()
        assert body["intent"] == "PLAN_TRIP"
        assert "**Flights:**" in body["response"]
        assert "**Accommodation:**" in body["response"]
        assert "**Weather:**" in body["response"]
