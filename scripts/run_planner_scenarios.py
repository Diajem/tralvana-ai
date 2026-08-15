"""Run a compact, repeatable planner smoke-test matrix.

This script exercises the same FastAPI route used by the production planner
without printing the very long itinerary bodies.  It is intended for release
checks and reports only routing, completion, important trip facts, and modules
that did or did not return a recommendation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
for path in (str(ROOT), str(API_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from app.main import app  # noqa: E402


SCENARIOS = {
    "new_york_complete": (
        "Plan a 7-day trip to New York for 2 Irish adults, departing from "
        "Manchester, from 15 September 2026 to 22 September 2026. We have a "
        "£3,500 balanced budget and want an average central hotel. We like major "
        "attractions, Nigerian and Caribbean restaurants, shopping and a football "
        "game. Include airport transfers, ESTA guidance, weather information and "
        "eSIM options."
    ),
    "montego_bay_couple": (
        "Plan a holiday to Montego Bay from Leeds from 4 October 2026 to 11 October "
        "2026 for 2 British adults with a £2,800 budget. We like beaches, culture, "
        "food and live music."
    ),
    "barcelona_football": (
        "Plan a 3-day trip to Barcelona from London from 6 November 2026 to 9 "
        "November 2026 for 2 Nigerian adults with a £1,500 budget. We like football, "
        "local food and architecture."
    ),
    "dubai_solo_business": (
        "Plan a 5-day business trip to Dubai from Dublin from 12 January 2027 to 17 "
        "January 2027 for 1 Irish adult with a €2,500 budget. Include airport "
        "transfers, a central hotel and two free evenings."
    ),
    "dublin_family": (
        "Plan a relaxing holiday to Dublin from Bradford on 17 October 2026 for two "
        "weeks with 2 British adults and 2 children and a £4,000 budget."
    ),
    "cape_town_culture": (
        "Plan a 10-day trip to Cape Town from Lagos from 2 December 2026 to 12 "
        "December 2026 for 2 Nigerian adults with a $4,500 budget. We like African "
        "history, food, music, nature and beaches."
    ),
    "country_only_follow_up": "Plan a 7-day trip to Japan in October 2026 for 2 adults.",
    "missing_destination_and_date": "Please help me plan a trip.",
    "visa_only": "Do Irish citizens need a visa for the United States?",
    "weather_only": "What is the weather in Marrakech in December?",
}


def summarise(body: dict) -> dict:
    itinerary = body.get("itinerary")
    summary = {
        "intent": body.get("intent"),
        "itinerary_created": itinerary is not None,
        "missing_information": body.get("missing_information", []),
    }
    if itinerary is None:
        summary["response"] = body.get("response", "")[:180]
        return summary

    brief = itinerary.get("trip_brief", {})
    summary.update(
        {
            "from": brief.get("origin"),
            "to": brief.get("destination"),
            "days": brief.get("duration_days"),
            "travellers": brief.get("travellers"),
            "readiness": itinerary.get("confidence"),
            "modules": {
                "destination": itinerary.get("destination_recommendation") is not None,
                "flight": itinerary.get("flight_recommendation") is not None,
                "accommodation": itinerary.get("accommodation_recommendation") is not None,
                "budget": itinerary.get("budget_summary") is not None,
                "visa": itinerary.get("visa_summary") is not None,
                "weather": itinerary.get("weather_expectations") is not None,
                "events": bool(itinerary.get("event_recommendations")),
            },
            "items_needed": itinerary.get("booking_readiness", {}).get("items_needed", []),
        }
    )
    return summary


def main() -> None:
    client = TestClient(app)
    report = {}
    for name, message in SCENARIOS.items():
        response = client.post("/planner/plan", json={"message": message})
        report[name] = {
            "status": response.status_code,
            **summarise(response.json()),
        }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
