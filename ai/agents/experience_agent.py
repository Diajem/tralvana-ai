from typing import Any

from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class ExperienceAgent:
    """
    Provides destination highlights, tips, and experience recommendations.
    Sprint 1: curated static knowledge.
    Sprint 4+: live data from destination content APIs.
    """

    name = "experience_agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        destination = input_data.get("destination", "your destination")

        interests: list[str] = []
        if self.context.traveller_profile:
            interests = self.context.traveller_profile.get("preferences", {}).get(
                "travel_interests", []
            )

        highlights = self._highlights_for(interests)
        tips = self._tips_for(destination)

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            confidence=0.65,
            data={
                "destination": destination,
                "highlights": highlights,
                "local_tips": tips,
                "best_seasons": ["Spring (Mar–May)", "Autumn (Sep–Nov)"],
                "interests_applied": interests,
            },
            assumptions=[
                "Destination content is static in Sprint 1 — live data in Sprint 4.",
                f"Highlights personalised for interests: {', '.join(interests) or 'general'}.",
            ],
            recommendations=[
                f"Research current travel advisories for {destination} before booking.",
                "Check entry requirements and visa rules in advance.",
            ],
            risks=["Local conditions may have changed — verify with up-to-date sources."],
            next_actions=["add_destination_to_itinerary", "check_visa_requirements"],
        )

    def _highlights_for(self, interests: list[str]) -> list[str]:
        base = ["Cultural landmarks", "Local cuisine", "Nature and scenery"]
        extras: dict[str, str] = {
            "adventure": "Outdoor activities and adventure sports",
            "beach": "Coastal beaches and water sports",
            "city": "Urban exploration and architecture",
            "wellness": "Spas and wellness retreats",
            "food_drink": "Food tours and local restaurants",
            "luxury": "Luxury experiences and fine dining",
            "sport": "Sports venues and events",
        }
        for interest in interests:
            if interest in extras and extras[interest] not in base:
                base.append(extras[interest])
        return base[:5]

    def _tips_for(self, destination: str) -> list[str]:
        return [
            "Learn a few phrases in the local language — it goes a long way.",
            "Carry local currency for markets and small vendors.",
            "Arrive early at popular sites to avoid crowds.",
        ]
