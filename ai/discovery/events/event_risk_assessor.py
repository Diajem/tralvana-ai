from __future__ import annotations

from typing import Any


class EventRiskAssessor:
    def assess(self, event: dict[str, Any]) -> list[str]:
        risks = [
            "No live event calendar was queried — confirm that the event exists on the travel dates."
        ]
        if event["availability_status"] == "UNKNOWN":
            risks.append("Ticket or admission availability is unknown.")
        if event.get("requires_ticket"):
            risks.append("Use only the official organiser, venue, club, or authorised ticket seller.")
        return risks


event_risk_assessor = EventRiskAssessor()
