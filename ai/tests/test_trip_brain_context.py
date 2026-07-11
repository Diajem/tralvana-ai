from ai.trip_brain.context import ContextBuilder, TripBrainContext


class TestContextBuilderNoIds:
    def test_no_goal_or_trip_id_leaves_them_none(self):
        builder = ContextBuilder()
        context = builder.build(
            traveller_id="t-1",
            trip_id=None,
            goal_id=None,
            entities={"destination": "Tokyo"},
            profile=None,
        )
        assert context.goal is None
        assert context.trip is None
        assert context.traveller_id == "t-1"
        assert context.entities == {"destination": "Tokyo"}

    def test_unknown_goal_id_is_tolerated(self):
        # goal_service.get() returns None for an unknown id — must not raise.
        builder = ContextBuilder()
        context = builder.build(
            traveller_id="t-1",
            trip_id=None,
            goal_id="nonexistent-goal",
            entities={},
            profile=None,
        )
        assert context.goal is None

    def test_unknown_trip_id_is_tolerated(self):
        builder = ContextBuilder()
        context = builder.build(
            traveller_id="t-1",
            trip_id="nonexistent-trip",
            goal_id=None,
            entities={},
            profile=None,
        )
        assert context.trip is None


class TestTripBrainContextProperties:
    def test_destination_prefers_entities_over_trip(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={"destination": "Osaka"},
            trip={"destination": "Tokyo"},
        )
        assert context.destination == "Osaka"

    def test_destination_falls_back_to_trip(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={}, trip={"destination": "Tokyo"},
        )
        assert context.destination == "Tokyo"

    def test_destination_ignores_placeholder_tbd(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={}, trip={"destination": "TBD"},
        )
        assert context.destination == ""

    def test_has_dates_true_for_date_hint(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={"date_hint": "next month"},
        )
        assert context.has_dates is True

    def test_has_dates_true_for_month(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={"month": "10"},
        )
        assert context.has_dates is True

    def test_has_dates_false_when_absent(self):
        context = TripBrainContext(traveller_id=None, trip_id=None, goal_id=None, entities={})
        assert context.has_dates is False

    def test_nationality_prefers_entities_over_profile(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={"nationality": "Irish"},
            profile={"identity": {"nationality": "NG"}},
        )
        assert context.nationality == "Irish"

    def test_nationality_falls_back_to_profile(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={}, profile={"identity": {"nationality": "NG"}},
        )
        assert context.nationality == "NG"

    def test_goal_has_budget_cap_true_when_max_usd_set(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={}, goal={"budget": {"max_usd": 3000}},
        )
        assert context.goal_has_budget_cap is True

    def test_goal_has_budget_cap_false_when_max_usd_none(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={}, goal={"budget": {"max_usd": None}},
        )
        assert context.goal_has_budget_cap is False

    def test_goal_has_budget_cap_false_without_goal(self):
        context = TripBrainContext(traveller_id=None, trip_id=None, goal_id=None, entities={})
        assert context.goal_has_budget_cap is False

    def test_party_size_known_from_goal_travellers(self):
        context = TripBrainContext(
            traveller_id=None, trip_id=None, goal_id=None,
            entities={}, goal={"travellers": {"adults": 2}},
        )
        assert context.party_size_known is True

    def test_party_size_unknown_without_travellers(self):
        context = TripBrainContext(traveller_id=None, trip_id=None, goal_id=None, entities={})
        assert context.party_size_known is False
