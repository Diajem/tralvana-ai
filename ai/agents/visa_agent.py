from typing import Any

from ai.shared.agent_context import AgentContext
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus


class VisaAgent:
    """
    Checks visa requirements based on traveller nationality and destination.
    Sprint 1: placeholder output — passport country not yet stored in profile.
    Sprint 5+: live visa data from an immigration API.
    """

    name = "visa_agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context

    async def run(self, input_data: dict[str, Any]) -> AgentResult:
        destination = input_data.get("destination", "")

        passport_country: str | None = None
        if self.context.traveller_profile:
            passport_country = (
                self.context.traveller_profile
                .get("documents", {})
                .get("passport_country")
            )

        if not passport_country:
            return AgentResult(
                agent_name=self.name,
                status=AgentStatus.PARTIAL,
                confidence=0.3,
                data={
                    "destination": destination,
                    "visa_info": "Requires passport country to check.",
                    "note": "Add your passport country to your profile for a personalised visa check.",
                },
                missing_information=[
                    "Passport country required for accurate visa requirements."
                ],
                assumptions=["Unable to determine visa requirements without nationality."],
                recommendations=[
                    f"Check visa requirements for {destination} on the official embassy website.",
                    "Allow at least 4–6 weeks for visa processing if required.",
                ],
                risks=[
                    "Travelling without the correct visa may result in denied boarding or entry.",
                    "Always verify with official government sources — visa rules change frequently.",
                ],
                next_actions=["add_passport_country_to_profile", "check_visa_manually"],
            )

        return AgentResult(
            agent_name=self.name,
            status=AgentStatus.SUCCESS,
            confidence=0.5,
            data={
                "destination": destination,
                "passport_country": passport_country,
                "visa_info": "pending_live_data",
                "note": "Live visa data activates in Sprint 5.",
            },
            assumptions=[f"Checking visa for {passport_country} passport to {destination}."],
            recommendations=[
                f"Verify requirements at the {destination} embassy for {passport_country} nationals.",
                "Apply well in advance — processing times vary.",
            ],
            risks=["Visa data is not live in Sprint 1 — always verify with official sources."],
            next_actions=["verify_visa_requirements_live"],
        )
