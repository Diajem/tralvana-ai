from __future__ import annotations

from typing import Any

_LOW_SAFETY_SCORE = 0.6
_FAR_FROM_CENTRE_KM = 15.0
_LOW_TRANSPORT_SCORE = 0.4
_OFF_SEASON_SCORE = 0.5


class DestinationRiskAssessor:
    """
    Deterministic risk flags for a single normalized destination option.

    Property-intrinsic only — no preferences parameter, matching the same
    pattern as ai/discovery/flights/flight_risk_assessor.py and
    ai/discovery/accommodation/accommodation_risk_assessor.py. Sprint 1:
    rule-based over the normalized fields. Sprint 4+: incorporate live
    travel advisory and crowd-density data per DestinationProvider once
    one is wired in.
    """

    def assess(self, destination: dict[str, Any]) -> list[str]:
        risks: list[str] = []
        d = destination

        if d["safety_score"] < _LOW_SAFETY_SCORE:
            risks.append("Below-average safety rating — check current travel advisories before visiting.")

        if d["distance_from_centre"] > _FAR_FROM_CENTRE_KM:
            risks.append(
                f"{d['distance_from_centre']} km from the centre — factor in significant transport time and cost."
            )

        if d["transport_access_score"] < _LOW_TRANSPORT_SCORE:
            risks.append("Limited public transport access — arranging a taxi or transfer is recommended.")

        if d["season_score"] <= _OFF_SEASON_SCORE:
            risks.append("Outside peak season — some attractions or events may have reduced hours.")

        if d["_popularity"] >= 9:
            risks.append("Very high-profile destination — expect crowds, especially in peak season.")

        return risks


destination_risk_assessor = DestinationRiskAssessor()
