# TravelOS SDK

The `TravelOS` SDK is the single public interface to all TravelOS capabilities.

## Principle

Nothing outside the platform layer should import internal service modules directly. All product code goes through `travelos`:

```python
from travelos.sdk import travelos
```

## Methods

### Traveller

```python
# Create a traveller profile
traveller = travelos.createTraveller({
    "identity": {
        "name": "Alex Okafor",
        "email": "alex@example.com",
        "nationality": "NG",
        "home_city": "Manchester",
        "home_country": "GB",
        "passport_countries": ["NG", "GB"]
    },
    "preferences": {
        "cabin_class": "economy",
        "seat_preference": "window",
        "dietary_requirements": [],
        "accessibility_needs": []
    },
    "loyalty": {
        "frequent_flyer_programs": [],
        "hotel_loyalty_programs": [],
        "credit_card_travel_benefits": []
    }
})

# Retrieve a traveller
traveller = travelos.getTraveller("traveller-id-123")
# Returns dict or None
```

### Goals

```python
# Create a goal
goal = travelos.createGoal({
    "traveller_id": "traveller-id-123",
    "title": "Football & Food Tour â€” Japan",
    "goal_type": "football_travel",
    "destination": "Japan",
    "duration_days": 10,
    "budget_style": "moderate",
    "cabin_class": "economy",
    "adults": 2,
    "children": 0,
    "interests": ["football", "food", "photography"]
})

# Retrieve a goal
goal = travelos.getGoal("goal-id-456")
```

### Trip Planning

```python
# Plan a trip
trip = travelos.planTrip({
    "traveller_id": "traveller-id-123",
    "goal_id": "goal-id-456",
    "origin": "Manchester",
    "destination": "Tokyo",
    "duration_days": 10,
    "budget_style": "moderate",
    "cabin_class": "economy",
    "adults": 2,
    "children": 0,
    "interests": ["football", "food", "photography"]
})

# trip["status"]      â†’ "READY" | "NEEDS_INFORMATION" | "DRAFT"
# trip["confidence"]  â†’ 0.0 â€“ 1.0
# trip["draft_itinerary"]  â†’ list of day dicts
# trip["estimated_budget_breakdown"] â†’ cost breakdown
# trip["risks"]       â†’ list of risk dicts
```

### Conversation (async)

```python
import asyncio

async def main():
    reply = await travelos.chat(
        "I want to plan a football trip to Japan in October",
        traveller_id="traveller-id-123",
    )
    # reply["intent"]          â†’ "PLAN_TRIP"
    # reply["response"]        â†’ AI response text
    # reply["confidence"]      â†’ 0.0 â€“ 1.0
    # reply["goal_id"]         â†’ created goal ID (if triggered)
    # reply["trip_id"]         â†’ created trip ID (if triggered)

asyncio.run(main())
```

### Reasoning

```python
result = travelos.reason("goal-id-456")
# result["planning_readiness_score"]  â†’ 0.0 â€“ 1.0
# result["missing_information"]       â†’ list of missing fields
# result["suitable_agents"]           â†’ list of recommended agents
```

### Knowledge

```python
# Search entities
cities = travelos.searchKnowledge("Tokyo", entity_type="City")
clubs  = travelos.searchKnowledge("Osaka", entity_type="FootballClub")
mixed  = travelos.searchKnowledge("Tokyo")  # searches all entity types

# Get a specific entity
tokyo = travelos.getKnowledge("City", "Tokyo")
# Returns entity dict or None
```

## Singleton

A default `travelos` instance is provided:

```python
from travelos.sdk import travelos          # use the singleton
from travelos.sdk.travelos_sdk import TravelOS  # or construct your own
```

## Testing

In tests, pass a custom `ServiceRegistry` to inject mock services:

```python
from travelos.sdk.travelos_sdk import TravelOS
from travelos.registry.service_registry import ServiceRegistry

registry = ServiceRegistry()
registry.register("goal_service", mock_goal_service)
sdk = TravelOS(registry=registry)
```
