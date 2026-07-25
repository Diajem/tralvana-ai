from __future__ import annotations

from typing import Any


class EventReasoner:
    def explain(self, event: dict[str, Any], score: dict[str, Any]) -> str:
        matched = score["interests_matched"]
        if matched:
            fit = f"Matches the stated interest(s): {', '.join(matched)}."
        else:
            fit = "Does not directly match a stated event interest."
        return (
            f"{event['name']} is a curated {event['category'].lower()} idea "
            f"for {event['destination']}. {fit} No exact date, fixture, ticket, "
            "price, or availability has been confirmed."
        )


event_reasoner = EventReasoner()
