from __future__ import annotations

from typing import Any


class EventRiskAssessor:
    def assess(self, event: dict[str, Any]) -> list[str]:
        if event.get("_evidence_level") == "LIVE":
            risks = [
                "Live event details can change — recheck the official event page "
                "before booking or changing the itinerary."
            ]
        else:
            risks = [
                "No live event calendar was queried — confirm that the event exists on the travel dates."
            ]
        if event["availability_status"] == "UNKNOWN":
            risks.append("Ticket or admission availability is unknown.")
        elif event["availability_status"] in {
            "OFF_SALE",
            "CANCELLED",
            "POSTPONED",
            "RESCHEDULED",
        }:
            risks.append(
                f"Provider event status is {event['availability_status']}."
            )
        if event.get("requires_ticket"):
            risks.append(
                "Use only the official organiser, venue, club, or authorised ticket seller."
            )
        if event.get("team_level") == "RESERVE_OR_YOUTH":
            risks.append(
                "Provider text identifies a reserve or youth fixture rather than "
                "a senior/open first-team listing."
            )
        return risks


event_risk_assessor = EventRiskAssessor()
