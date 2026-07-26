from __future__ import annotations

from typing import Any


class EventReasoner:
    def explain(self, event: dict[str, Any], score: dict[str, Any]) -> str:
        matched = score["interests_matched"]
        if matched:
            fit = f"Matches the stated interest(s): {', '.join(matched)}."
        else:
            fit = "Does not directly match a stated event interest."
        if event.get("_evidence_level") == "LIVE":
            team_context = ""
            if event.get("team_level") == "RESERVE_OR_YOUTH":
                team_context = (
                    " Provider text identifies this as a reserve or youth fixture, "
                    "so it ranks below comparable senior/open listings."
                )
            elif event.get("team_level") == "SENIOR_OR_OPEN":
                team_context = (
                    " Available provider text does not label it as a reserve or "
                    "youth fixture."
                )
            return (
                f"{event['name']} is a live {event['category'].lower()} listing "
                f"from {event['source_name']} for {event['destination']}. {fit}"
                f"{team_context} "
                "The event date comes from the provider; current ticket inventory "
                "and pricing must still be confirmed on the official event page."
            )
        return (
            f"{event['name']} is a curated {event['category'].lower()} idea "
            f"for {event['destination']}. {fit} No exact date, fixture, ticket, "
            "price, or availability has been confirmed."
        )


event_reasoner = EventReasoner()
