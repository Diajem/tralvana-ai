import pytest

from ai.trip_brain.context import TripBrainContext
from ai.trip_brain.module_selection import (
    BASE_MODULES,
    CORE_WEIGHT,
    SUPPORTING_WEIGHT,
    ModuleSelector,
)


@pytest.fixture
def selector() -> ModuleSelector:
    return ModuleSelector()


def _context(**overrides) -> TripBrainContext:
    defaults = dict(
        traveller_id="t-1",
        trip_id=None,
        goal_id=None,
        entities={},
        profile=None,
        goal=None,
        trip=None,
    )
    defaults.update(overrides)
    return TripBrainContext(**defaults)


class TestModuleSelector:
    def test_no_destination_selects_nothing(self, selector):
        context = _context(entities={})
        assert selector.select(context) == {}

    def test_destination_only_selects_destination_and_weather(self, selector):
        # Nationality matching the destination avoids also triggering the
        # Visa rule, isolating this test to the destination-only signal.
        context = _context(entities={"destination": "Tokyo", "nationality": "Tokyo"})
        weights = selector.select(context)
        assert set(weights.keys()) == {"destination", "weather"}
        assert weights["destination"] == CORE_WEIGHT
        assert weights["weather"] == CORE_WEIGHT

    def test_destination_only_with_unknown_nationality_also_adds_visa(self, selector):
        # docs/TRIP_BRAIN_ARCHITECTURE.md: Visa Intelligence is relevant
        # whenever nationality "differs... (or is unknown)".
        context = _context(entities={"destination": "Tokyo"})
        weights = selector.select(context)
        assert set(weights.keys()) == {"destination", "weather", "visa"}

    def test_destination_and_dates_adds_flight_and_accommodation(self, selector):
        context = _context(
            entities={
                "destination": "Tokyo",
                "start_date": "2026-10-05",
                "end_date": "2026-10-15",
                "nationality": "Tokyo",
            }
        )
        weights = selector.select(context)
        assert set(weights.keys()) == {"destination", "weather", "flight", "accommodation"}

    def test_dates_without_destination_selects_nothing(self, selector):
        context = _context(entities={"date_hint": "in october"})
        assert selector.select(context) == {}

    def test_goal_budget_cap_adds_budget_as_supporting(self, selector):
        context = _context(
            entities={"destination": "Tokyo"},
            goal={"budget": {"max_usd": 3000}, "travellers": {"adults": 1}},
        )
        weights = selector.select(context)
        assert "budget" in weights
        assert weights["budget"] == SUPPORTING_WEIGHT

    def test_no_budget_cap_excludes_budget(self, selector):
        context = _context(
            entities={"destination": "Tokyo"},
            goal={"budget": {"max_usd": None}, "travellers": {"adults": 1}},
        )
        assert "budget" not in selector.select(context)

    def test_unknown_nationality_adds_visa_as_supporting(self, selector):
        context = _context(entities={"destination": "Tokyo"}, profile=None)
        weights = selector.select(context)
        assert "visa" in weights
        assert weights["visa"] == SUPPORTING_WEIGHT

    def test_matching_nationality_and_destination_excludes_visa(self, selector):
        context = _context(entities={"destination": "Tokyo", "nationality": "Tokyo"})
        assert "visa" not in selector.select(context)

    def test_differing_nationality_adds_visa(self, selector):
        context = _context(entities={"destination": "Tokyo", "nationality": "Nigerian"})
        assert "visa" in selector.select(context)

    def test_no_destination_excludes_visa_even_if_nationality_known(self, selector):
        context = _context(entities={"nationality": "Nigerian"})
        assert "visa" not in selector.select(context)

    def test_full_trip_shape_selects_all_six_as_core(self, selector):
        context = _context(
            entities={
                "destination": "Tokyo",
                "start_date": "2026-10-05",
                "end_date": "2026-10-15",
            },
            goal={"budget": {"max_usd": 3000}, "travellers": {"adults": 2}},
            profile={"identity": {"nationality": "GB"}},
        )
        weights = selector.select(context)
        assert set(weights.keys()) == set(BASE_MODULES)
        assert all(w == CORE_WEIGHT for w in weights.values())

    def test_full_trip_shape_forces_all_six_even_without_budget_cap_or_visa_need(self, selector):
        # docs/TRIP_BRAIN_ARCHITECTURE.md's Decision Lifecycle table lists
        # "full trip shape" as its own row selecting all six, independent
        # of whether the Budget/Visa-specific triggers separately fire.
        context = _context(
            entities={
                "destination": "Tokyo",
                "start_date": "2026-10-05",
                "end_date": "2026-10-15",
                "nationality": "Tokyo",
            },
            goal={"budget": {"max_usd": None}, "travellers": {"adults": 1}},
        )
        weights = selector.select(context)
        assert set(weights.keys()) == set(BASE_MODULES)

    def test_party_size_unknown_does_not_force_full_shape(self, selector):
        context = _context(
            entities={
                "destination": "Tokyo",
                "start_date": "2026-10-05",
                "end_date": "2026-10-15",
                "nationality": "Tokyo",
            },
            goal={"budget": {"max_usd": 3000}, "travellers": {}},
        )
        weights = selector.select(context)
        assert set(weights.keys()) == {"destination", "weather", "flight", "accommodation", "budget"}
        assert "visa" not in weights

    def test_event_interest_adds_events_as_core(self, selector):
        context = _context(
            entities={
                "destination": "New York",
                "date_hint": "in august",
                "interests": "fashion,soccer",
                "nationality": "New York",
            }
        )
        weights = selector.select(context)
        assert weights["events"] == CORE_WEIGHT

    def test_non_event_interests_do_not_add_events(self, selector):
        context = _context(
            entities={
                "destination": "New York",
                "interests": "dining,major attractions",
                "nationality": "New York",
            }
        )
        assert "events" not in selector.select(context)

    def test_goal_interests_can_trigger_events(self, selector):
        context = _context(
            entities={"destination": "New York", "nationality": "New York"},
            goal={"interests": ["football"], "travellers": {"adults": 1}},
        )
        assert selector.select(context)["events"] == CORE_WEIGHT
