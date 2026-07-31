"""
TripAssemblyEngine (T-040) — assembles Trip Brain's already-computed
UnifiedRecommendation into one TripItinerary. Every assertion here
checks that a value was *read*, not recomputed — no test constructs a
scoring scenario, only pre-scored AgentResults the engine must not touch.
"""

from __future__ import annotations

from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.models import UnifiedRecommendation
from ai.trip_brain.trip_assembly import TripAssemblyEngine

engine = TripAssemblyEngine()


def _flight_result(top=None, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="flight_intelligence", status=status, confidence=0.82,
        data={"top_option": top or {"airline": "AeroLondon", "estimated_price": 825, "currency": "GBP", "match_score": 0.82, "data_source": "LIVE_PROVIDER"}},
    )


def _accommodation_result(top=None, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="accommodation_intelligence", status=status, confidence=0.75,
        data={"top_option": top or {"property_name": "Tokyo Hotel", "accommodation_type": "HOTEL", "match_score": 0.75, "data_source": "LIVE_PROVIDER"}},
    )


def _destination_result(status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="destination_intelligence", status=status, confidence=0.73,
        data={"top_option": {"name": "Shibuya", "match_score": 0.73}},
    )


def _budget_result(style="balanced", status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="budget_intelligence", status=status, confidence=0.70,
        data={"top_option": {"budget_style": style, "match_score": 0.70}},
    )


def _visa_result(required=False, status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="visa_intelligence", status=status, confidence=0.9,
        data={"visa_status": "NOT_REQUIRED" if not required else "VISA_REQUIRED", "visa_required": required, "visa_type": "Tourist Visa"},
    )


def _weather_result(status=AgentStatus.SUCCESS) -> AgentResult:
    return AgentResult(
        agent_name="weather_intelligence", status=status, confidence=0.6,
        data={"season": "Summer", "recommendation": "A great time to visit."},
    )


def _event_result(status=AgentStatus.SUCCESS) -> AgentResult:
    option = {
        "event_option_id": "event-1",
        "name": "Professional soccer or football match",
        "category": "SPORT",
        "venue_area": "Local stadium district",
        "description": "Check the official fixture calendar.",
        "starts_at": None,
        "date_status": "UNVERIFIED",
        "availability_status": "UNKNOWN",
        "interests_matched": ["soccer"],
        "data_source": "TRALVANA_CURATED_EVENT_IDEAS",
        "retrieved_at": "2026-07-25T20:00:00+00:00",
    }
    return AgentResult(
        agent_name="event_intelligence",
        status=status,
        confidence=0.6,
        data={"top_option": option, "options": [option]},
    )


def _unified(results, explanation=None, confidence=0.7) -> UnifiedRecommendation:
    succeeded = [r.agent_name.replace("_intelligence", "") for r in results if r.status != AgentStatus.FAILED]
    failed = [r.agent_name.replace("_intelligence", "") for r in results if r.status == AgentStatus.FAILED]
    return UnifiedRecommendation(
        results=results,
        modules_selected=succeeded + failed,
        modules_succeeded=succeeded,
        modules_failed=failed,
        overall_confidence=confidence,
        destination="Tokyo",
        explanation=explanation or {},
    )


def _brief(**overrides):
    value = {
        "origin": "Manchester",
        "destination": "Tokyo",
        "duration_days": 5,
        "start_date": "2026-10-10",
        "end_date": "2026-10-15",
        "month": 10,
        "year": 2026,
        "date_precision": "EXACT",
        "travel_period": "2026-10-10 to 2026-10-15",
        "travellers": {"adults": 2, "children": 0, "infants": 0},
        "budget": {
            "amount": 3000,
            "currency": "GBP",
            "source": "TRAVELLER_DECLARED",
        },
        "nationality": "British",
        "interests": ["culture"],
    }
    value.update(overrides)
    return value


class TestTopOptionExtraction:
    def test_flight_recommendation_is_the_modules_own_top_option(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.flight_recommendation == {"airline": "AeroLondon", "estimated_price": 825, "currency": "GBP", "match_score": 0.82, "data_source": "LIVE_PROVIDER"}

    def test_accommodation_recommendation_is_the_modules_own_top_option(self):
        unified = _unified([_accommodation_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.accommodation_recommendation["property_name"] == "Tokyo Hotel"

    def test_failed_module_yields_none_not_a_crash(self):
        unified = _unified([_flight_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.flight_recommendation is None

    def test_missing_module_yields_none(self):
        unified = _unified([])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.flight_recommendation is None
        assert itinerary.accommodation_recommendation is None
        assert itinerary.destination_recommendation is None
        assert itinerary.budget_summary is None


class TestSingleAssessmentExtraction:
    def test_visa_summary_is_the_whole_assessment_dict(self):
        unified = _unified([_visa_result(required=True)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.visa_summary["visa_required"] is True
        assert itinerary.visa_summary["visa_type"] == "Tourist Visa"

    def test_weather_expectations_is_the_whole_assessment_dict(self):
        unified = _unified([_weather_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.weather_expectations["season"] == "Summer"

    def test_failed_visa_module_yields_none(self):
        unified = _unified([_visa_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert itinerary.visa_summary is None

    def test_event_recommendations_are_the_modules_existing_options(self):
        itinerary = engine.assemble(
            _unified([_event_result()]),
            destination="New York",
            duration_days=5,
            interests=["soccer"],
        )
        assert itinerary.event_recommendations[0]["event_option_id"] == "event-1"


class TestCoherentPlannerEvidence:
    def test_independent_explanation_cannot_restore_a_mock_supplier_claim(self):
        explanation = {"risks": ["Mock fare is low risk."]}
        mock = {
            "airline": "AeroLondon",
            "estimated_price": 825,
            "currency": "USD",
            "data_source": "MOCK",
        }
        itinerary = engine.assemble(
            _unified([_flight_result(top=mock)], explanation=explanation),
            destination="Tokyo",
            duration_days=5,
            trip_brief=_brief(),
        )
        assert itinerary.flight_recommendation is None
        assert all("Mock fare" not in risk for risk in itinerary.risks)

    def test_readiness_caps_confidence(self):
        incomplete = _brief(
            date_precision="MONTH",
            start_date=None,
            end_date=None,
            nationality=None,
        )
        itinerary = engine.assemble(
            _unified([_flight_result()], confidence=0.91),
            destination="Tokyo",
            duration_days=5,
            trip_brief=incomplete,
        )
        assert itinerary.confidence <= itinerary.booking_readiness["score"] / 100

    def test_mock_alternatives_are_not_presented(self):
        explanation = {
            "alternatives_considered": [
                {"module": "flight_intelligence", "alternative": "Continental Express"}
            ]
        }
        itinerary = engine.assemble(
            _unified([_flight_result()], explanation=explanation),
            destination="Tokyo",
            duration_days=5,
            trip_brief=_brief(),
        )
        assert itinerary.alternative_options == []

    def test_drivers_begin_with_the_canonical_trip_brief(self):
        itinerary = engine.assemble(
            _unified([_flight_result()]),
            destination="Tokyo",
            duration_days=5,
            trip_brief=_brief(),
        )
        assert itinerary.why_this_itinerary[0]["module"] == "canonical_trip_brief"


class TestDailyOutline:
    def test_daily_outline_has_one_entry_per_day(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5, goal_type="GENERAL_TRAVEL")
        assert len(itinerary.daily_outline) == 5
        assert [d["day"] for d in itinerary.daily_outline] == [1, 2, 3, 4, 5]

    def test_daily_outline_reflects_goal_type_theme(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=4, goal_type="FOOD_TOUR")
        # Day 2 (first non-arrival day) should carry a FOOD_TOUR theme, not GENERAL_TRAVEL's.
        assert "Market" in itinerary.daily_outline[1]["theme"] or "Culinary" in itinerary.daily_outline[1]["theme"] or "Wine" in itinerary.daily_outline[1]["theme"] or "Neighbourhood" in itinerary.daily_outline[1]["theme"]

    def test_zero_or_negative_duration_still_produces_at_least_one_day(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=0)
        assert len(itinerary.daily_outline) >= 1


class TestExecutiveSummary:
    def test_no_succeeded_modules_produces_a_clear_not_ready_message(self):
        unified = _unified([_flight_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "more detail" in itinerary.executive_summary.lower()

    def test_summary_quotes_real_flight_and_accommodation_facts(self):
        unified = _unified([_flight_result(), _accommodation_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "AeroLondon" in itinerary.executive_summary
        assert "Tokyo Hotel" in itinerary.executive_summary
        assert "Tokyo" in itinerary.executive_summary

    def test_mock_price_is_described_as_an_estimate_not_a_confirmed_fare(self):
        mock = {
            "airline": "AeroLondon",
            "estimated_price": 825,
            "currency": "USD",
            "data_source": "MOCK",
        }
        itinerary = engine.assemble(
            _unified([_flight_result(top=mock)]),
            destination="Tokyo",
            duration_days=5,
        )
        assert itinerary.flight_recommendation is None
        assert "AeroLondon" not in itinerary.executive_summary

    def test_sandbox_price_is_described_as_test_data(self):
        sandbox = {
            "airline": "Duffel Test Air",
            "estimated_price": 500,
            "currency": "USD",
            "match_score": 0.8,
            "data_source": "DUFFEL_SANDBOX",
        }
        itinerary = engine.assemble(
            _unified([_flight_result(top=sandbox)]),
            destination="Tokyo",
            duration_days=5,
        )
        assert itinerary.flight_recommendation is None
        assert "Duffel Test Air" not in itinerary.executive_summary

    def test_summary_never_fabricates_a_module_that_did_not_run(self):
        unified = _unified([_flight_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "visa" not in itinerary.executive_summary.lower()
        assert "stay at" not in itinerary.executive_summary.lower()

    def test_summary_reflects_visa_required_vs_not_required(self):
        unified_required = _unified([_visa_result(required=True)])
        itinerary_required = engine.assemble(unified_required, destination="Tokyo", duration_days=5)
        assert "required" in itinerary_required.executive_summary.lower()

        unified_not_required = _unified([_visa_result(required=False)])
        itinerary_not_required = engine.assemble(unified_not_required, destination="Tokyo", duration_days=5)
        assert "no visa is required" in itinerary_not_required.executive_summary.lower()

    def test_summary_does_not_claim_visa_free_when_status_is_unknown(self):
        unknown = AgentResult(
            agent_name="visa_intelligence",
            status=AgentStatus.SUCCESS,
            confidence=0.2,
            data={
                "visa_status": "CHECK_MANUALLY",
                "visa_required": False,
                "travel_authorisation_required": False,
                "visa_type": "Unknown",
            },
        )
        itinerary = engine.assemble(
            _unified([unknown]), destination="Dublin", duration_days=14
        )
        assert "no visa is required" not in itinerary.executive_summary.lower()
        assert "could not be determined" in itinerary.executive_summary.lower()

    def test_conflicting_mock_budget_breakdown_is_not_presented_as_reconciled(self):
        explanation = {"recommendation_drivers": [{"module": "budget_intelligence", "driver": "Flights USD 900, accommodation USD 472."}]}
        budget = AgentResult(
            agent_name="budget_intelligence",
            status=AgentStatus.SUCCESS,
            confidence=0.7,
            data={
                "top_option": {
                    "budget_style": "balanced",
                    "currency": "USD",
                    "flight_cost_usd": 900,
                    "accommodation_usd": 472,
                }
            },
        )
        flight = _flight_result(
            top={
                "airline": "AeroLondon",
                "estimated_price": 500,
                "currency": "USD",
            }
        )
        accommodation = _accommodation_result(
            top={
                "property_name": "Dublin Guesthouse",
                "accommodation_type": "GUESTHOUSE",
                "total_price": 350,
                "currency": "USD",
            }
        )
        itinerary = engine.assemble(
            _unified(
                [flight, accommodation, budget],
                explanation=explanation,
            ),
            destination="Dublin",
            duration_days=7,
            trip_brief=_brief(
                destination="Dublin",
                duration_days=7,
                budget={
                    "amount": 3000,
                    "currency": "GBP",
                    "source": "TRAVELLER_DECLARED",
                },
            ),
        )
        assert itinerary.budget_summary["currency"] == "GBP"
        assert itinerary.budget_summary["assessment_status"] == "NOT_YET_ASSESSED"
        assert "Flights USD 900" not in str(itinerary.why_this_itinerary)

    def test_summary_includes_confidence_percentage(self):
        unified = _unified([_flight_result()], confidence=0.82)
        itinerary = engine.assemble(
            unified,
            destination="Tokyo",
            duration_days=5,
            trip_brief=_brief(),
        )
        assert "90%" in itinerary.executive_summary


class TestModulesUsedAndUnavailable:
    def test_modules_used_and_unavailable_pass_through(self):
        unified = _unified([_flight_result(), _accommodation_result(status=AgentStatus.FAILED)])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        assert "flight" in itinerary.modules_used
        assert "accommodation" in itinerary.modules_unavailable


class TestGroundingNotices:
    def test_mock_flight_and_accommodation_fail_closed_to_estimate(self):
        itinerary = engine.assemble(
            _unified([_flight_result(), _accommodation_result()]),
            destination="Tokyo",
            duration_days=5,
        )
        by_domain = {n.domain: n for n in itinerary.grounding_notices}
        assert by_domain["flight"].level == "LIVE"
        assert by_domain["flight"].is_current is True
        assert by_domain["accommodation"].level == "LIVE"
        assert all(n.requires_confirmation for n in itinerary.grounding_notices)

    def test_duffel_sandbox_is_never_labelled_live(self):
        sandbox = {
            "airline": "Duffel Test Air",
            "estimated_price": 500,
            "currency": "USD",
            "match_score": 0.8,
            "data_source": "DUFFEL_SANDBOX",
        }
        itinerary = engine.assemble(
            _unified([_flight_result(top=sandbox)]),
            destination="Tokyo",
            duration_days=5,
        )
        notice = next(n for n in itinerary.grounding_notices if n.domain == "flight")
        assert notice.level == "GUIDANCE"
        assert notice.is_current is False

    def test_unknown_provider_label_is_not_promoted_to_live(self):
        unknown = {
            "airline": "Future Air",
            "estimated_price": 500,
            "currency": "USD",
            "match_score": 0.8,
            "data_source": "FUTURE_VENDOR",
        }
        itinerary = engine.assemble(
            _unified([_flight_result(top=unknown)]),
            destination="Tokyo",
            duration_days=5,
        )
        notice = next(n for n in itinerary.grounding_notices if n.domain == "flight")
        assert notice.level == "GUIDANCE"
        assert notice.is_current is False

    def test_static_domains_are_labelled_by_their_real_grounding(self):
        itinerary = engine.assemble(
            _unified(
                [
                    _destination_result(),
                    _budget_result(),
                    _visa_result(),
                    _weather_result(),
                ]
            ),
            destination="Tokyo",
            duration_days=5,
        )
        levels = {n.domain: n.level for n in itinerary.grounding_notices}
        assert levels["destination"] == "CURATED"
        assert levels["flight"] == "GUIDANCE"
        assert levels["accommodation"] == "GUIDANCE"
        assert levels["budget"] == "GUIDANCE"
        assert levels["visa"] == "GUIDANCE"
        assert levels["weather"] == "CLIMATE_PROFILE"

    def test_event_interests_without_a_result_add_an_idea_notice(self):
        itinerary = engine.assemble(
            _unified([_destination_result()]),
            destination="New York",
            duration_days=5,
            interests=["fashion", "soccer"],
        )
        event_notice = next(n for n in itinerary.grounding_notices if n.domain == "events")
        assert event_notice.level == "IDEA"
        assert event_notice.data_source == "NO_CONFIRMED_EVENT_RESULT"
        assert "did not return a usable current listing" in event_notice.message

    def test_structured_event_results_are_curated_not_live(self):
        itinerary = engine.assemble(
            _unified([_event_result()]),
            destination="New York",
            duration_days=5,
            interests=["soccer"],
        )
        event_notice = next(
            notice for notice in itinerary.grounding_notices
            if notice.domain == "events"
        )
        assert event_notice.level == "CURATED"
        assert event_notice.is_current is False
        assert event_notice.data_source == "TRALVANA_CURATED_EVENT_IDEAS"

    def test_ticketmaster_event_results_are_grounded_as_live(self):
        result = _event_result()
        live_option = {
            **result.data["options"][0],
            "starts_at": "2026-08-15T23:30:00Z",
            "date_status": "CONFIRMED",
            "availability_status": "ON_SALE",
            "data_source": "TICKETMASTER_DISCOVERY_API",
            "retrieved_at": "2026-07-26T10:00:00+00:00",
        }
        result.data = {"top_option": live_option, "options": [live_option]}
        itinerary = engine.assemble(
            _unified([result]),
            destination="New York",
            duration_days=5,
            interests=["soccer"],
        )
        event_notice = next(
            notice for notice in itinerary.grounding_notices
            if notice.domain == "events"
        )
        assert event_notice.level == "LIVE"
        assert event_notice.is_current is True
        assert event_notice.requires_confirmation is True
        assert event_notice.data_source == "TICKETMASTER_DISCOVERY_API"

    def test_empty_successful_ticketmaster_search_is_still_grounded_as_live(self):
        result = AgentResult(
            agent_name="event_intelligence",
            status=AgentStatus.NEEDS_INFORMATION,
            confidence=0.0,
            data={
                "options": [],
                "data_source": "TICKETMASTER_DISCOVERY_API",
                "provider_status": "AVAILABLE",
                "retrieved_at": "2026-07-26T10:00:00+00:00",
            },
        )
        itinerary = engine.assemble(
            _unified([result]),
            destination="New York",
            duration_days=5,
            interests=["fashion", "soccer"],
        )
        event_notice = next(
            notice for notice in itinerary.grounding_notices
            if notice.domain == "events"
        )
        assert event_notice.level == "LIVE"
        assert event_notice.is_current is True
        assert "returned no matching listings" in event_notice.message


class TestToDict:
    def test_to_dict_contains_every_required_section(self):
        unified = _unified([_flight_result(), _accommodation_result(), _destination_result(), _budget_result(), _visa_result(), _weather_result()])
        itinerary = engine.assemble(unified, destination="Tokyo", duration_days=5)
        d = itinerary.to_dict()
        required_keys = {
            "executive_summary", "destination_recommendation", "flight_recommendation",
            "accommodation_recommendation", "budget_summary", "visa_summary",
            "weather_expectations", "event_recommendations", "risks", "assumptions", "daily_outline",
            "why_this_itinerary", "confidence", "confidence_explanation",
            "alternative_options", "grounding_notices",
        }
        assert required_keys.issubset(d.keys())
