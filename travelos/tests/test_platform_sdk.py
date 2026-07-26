import asyncio
from dataclasses import dataclass
from types import SimpleNamespace

from travelos.sdk.travelos_sdk import TravelOS


class Registry:
    def __init__(self, **services):
        self.services = services

    def get(self, name):
        return self.services[name]


class RecordingService:
    def __init__(self):
        self.calls = []

    def create_profile(self, request):
        self.calls.append(request)
        return request.model_dump()

    def create(self, request):
        self.calls.append(request)
        return request.model_dump()

    def plan(self, request):
        self.calls.append(request)
        return request.model_dump()


def test_sdk_create_traveller_validates_and_delegates():
    service = RecordingService()
    sdk = TravelOS(Registry(traveller_service=service))

    result = sdk.createTraveller(
        {
            "identity": {
                "name": "Test Traveller",
                "email": "traveller@example.com",
            },
            "preferences": {"budget_style": "balanced"},
        }
    )

    assert result["identity"]["name"] == "Test Traveller"
    assert result["preferences"]["budget_style"] == "balanced"
    assert len(service.calls) == 1


def test_sdk_create_goal_and_plan_trip_validate_and_delegate():
    goal_service = RecordingService()
    trip_service = RecordingService()
    sdk = TravelOS(
        Registry(
            goal_service=goal_service,
            trip_planning_service=trip_service,
        )
    )

    goal = sdk.createGoal(
        {
            "traveller_id": "traveller-1",
            "title": "New York holiday",
            "interests": ["fashion", "soccer"],
        }
    )
    trip = sdk.planTrip(
        {
            "traveller_id": "traveller-1",
            "origin": "Leeds",
            "destination": "New York",
            "duration_days": 15,
            "interests": ["fashion", "soccer"],
        }
    )

    assert goal["title"] == "New York holiday"
    assert trip["destination"] == "New York"
    assert trip["duration_days"] == 15


def test_sdk_getters_preserve_missing_values():
    traveller_service = SimpleNamespace(
        get_profile=lambda traveller_id: (
            {"id": traveller_id} if traveller_id == "known" else None
        )
    )
    goal_service = SimpleNamespace(
        get=lambda goal_id: {"goal_id": goal_id} if goal_id == "known" else None
    )
    sdk = TravelOS(
        Registry(
            traveller_service=traveller_service,
            goal_service=goal_service,
        )
    )

    assert sdk.getTraveller("known") == {"id": "known"}
    assert sdk.getTraveller("missing") is None
    assert sdk.getGoal("known") == {"goal_id": "known"}
    assert sdk.getGoal("missing") is None


@dataclass
class KnowledgeEntity:
    name: str
    kind: str


class KnowledgeService:
    def __init__(self):
        self.searches = []

    def search_entities(self, entity_type, query):
        self.searches.append((entity_type, query))
        if entity_type == "City":
            return [KnowledgeEntity("New York", "City")]
        if entity_type == "Attraction":
            return [{"name": "Central Park", "kind": "Attraction"}, "ignored"]
        return []

    def find_entity(self, entity_type, name):
        values = {
            ("City", "New York"): KnowledgeEntity("New York", "City"),
            ("Code", "NYC"): "New York",
        }
        return values.get((entity_type, name))


def test_sdk_knowledge_search_normalises_dataclasses_and_dicts():
    service = KnowledgeService()
    sdk = TravelOS(Registry(knowledge_service=service))

    city_results = sdk.searchKnowledge("New", entity_type="City")
    all_results = sdk.searchKnowledge("New")

    assert city_results == [{"name": "New York", "kind": "City"}]
    assert {"name": "Central Park", "kind": "Attraction"} in all_results
    assert "ignored" not in all_results
    assert len(service.searches) == 8


def test_sdk_get_knowledge_handles_dataclass_dict_scalar_and_missing():
    service = KnowledgeService()
    sdk = TravelOS(Registry(knowledge_service=service))

    assert sdk.getKnowledge("City", "New York") == {
        "name": "New York",
        "kind": "City",
    }
    assert sdk.getKnowledge("Code", "NYC") == {"value": "New York"}
    assert sdk.getKnowledge("City", "Missing") is None


def test_sdk_reason_handles_missing_goal_without_calling_reasoner():
    sdk = TravelOS(Registry(goal_service=SimpleNamespace(get=lambda goal_id: None)))

    assert sdk.reason("missing") == {
        "error": "Goal 'missing' not found",
        "success": False,
    }


def test_sdk_reason_delegates_existing_goal(monkeypatch):
    class Reasoner:
        def reason(self, goal):
            assert goal == {"goal_id": "goal-1"}
            return {"planning_readiness_score": 0.8}

    monkeypatch.setattr("ai.goals.goal_reasoner.GoalReasoner", Reasoner)
    sdk = TravelOS(
        Registry(
            goal_service=SimpleNamespace(
                get=lambda goal_id: {"goal_id": goal_id},
            )
        )
    )

    assert sdk.reason("goal-1") == {
        "success": True,
        "goal_id": "goal-1",
        "planning_readiness_score": 0.8,
    }


def test_sdk_chat_delegates_to_concierge(monkeypatch):
    calls = []

    class Concierge:
        async def handle(self, message, traveller_id=None, conversation_id=None):
            calls.append((message, traveller_id, conversation_id))
            return {"reply": "ready"}

    monkeypatch.setattr(
        "ai.concierge.travel_concierge.travel_concierge",
        Concierge(),
    )
    sdk = TravelOS(Registry())

    result = asyncio.run(
        sdk.chat(
            "Plan New York",
            traveller_id="traveller-1",
            conversation_id="conversation-1",
        )
    )

    assert result == {"reply": "ready"}
    assert calls == [
        ("Plan New York", "traveller-1", "conversation-1"),
    ]
