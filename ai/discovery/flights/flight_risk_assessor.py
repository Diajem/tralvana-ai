from __future__ import annotations

from typing import Any

_LONG_LAYOVER_MINUTES = 240
_SHORT_LAYOVER_MINUTES = 60
_LONG_HAUL_MINUTES = 600


class FlightRiskAssessor:
    """
    Deterministic risk flags for a single mock flight option.

    Sprint 1: rule-based over the flight's own fields (stops, layover,
    refundability, departure time). Sprint 4+: incorporate live disruption
    and on-time-performance data per FlightProvider once one is wired in.
    """

    def assess(self, flight: dict[str, Any]) -> list[str]:
        risks: list[str] = []

        layover_minutes = flight.get("_layover_minutes", 0)
        if flight["stops"] >= 1 and 0 < layover_minutes < _SHORT_LAYOVER_MINUTES:
            risks.append(
                f"Tight connection — {flight['layover_duration']} layover may not "
                "allow enough time if the first leg is delayed."
            )
        if flight["stops"] >= 1 and layover_minutes >= _LONG_LAYOVER_MINUTES:
            risks.append(
                f"Long layover ({flight['layover_duration']}) adds significant travel time and fatigue."
            )
        if flight["stops"] >= 2:
            risks.append("Two connections increase the chance of missed connections or delays.")

        if flight["refundability"] == "non_refundable":
            risks.append("Non-refundable fare — cancellation means losing the full ticket cost.")

        if flight["flexibility"] == "fixed":
            risks.append("Fixed fare — date changes are not permitted or carry a high fee.")

        hour = int(flight["departure_time"].split(":")[0])
        if 0 <= hour < 5:
            risks.append("Red-eye departure — may affect rest before the trip begins.")

        if flight["_total_duration_minutes"] >= _LONG_HAUL_MINUTES and flight["cabin_class"] == "economy":
            risks.append("Long total travel time in economy — consider a break at the layover city.")

        if not flight["baggage_included"]:
            risks.append("Checked baggage not included in the fare — extra cost if needed.")

        return risks


flight_risk_assessor = FlightRiskAssessor()
