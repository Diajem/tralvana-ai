# Traveller DNA

Traveller DNA is TravelOS's system for inferring a traveller's core travel archetype from their Traveller Intelligence Profile (TIP). DNA informs every AI agent recommendation — from destination selection to hotel tier to experience curation.

## The 10 DNA Types

| DNA Type | Primary Signals | What TravelOS Does |
|----------|----------------|-------------------|
| **Explorer** | Many diverse interests (3+), open itinerary | Suggests off-beaten-path destinations, multi-city routes |
| **Luxury** | First/business cabin, luxury budget, luxury interests | Recommends 5-star hotels, private transfers, exclusive experiences |
| **Budget** | Backpacker/budget style, hostel accommodation | Finds free activities, budget airlines, hostel options |
| **Football Traveller** | Sport interests, follows leagues | Plans trips around match schedules, flags stadiums |
| **Family Traveller** | Resort accommodation, beach/wellness interests | Child-friendly venues, resort stays, minimal long transfers |
| **Business Traveller** | Business cabin, business interests, airline loyalty | Airport lounge access, city-centre hotels, fast Wi-Fi |
| **Adventure Traveller** | Adventure/nature interests, backpacker style | National parks, trekking, extreme sports |
| **Food Traveller** | food_drink interests, specific meal requirements | Curates restaurants, food tours, culinary events |
| **Photography Traveller** | Nature/culture/city interests | Golden-hour spots, viewpoints, photography-friendly venues |
| **Digital Nomad** | City interests, balanced budget, apartment accommodation | Co-working spaces, long-stay apartments, reliable Wi-Fi |

## Inference Algorithm

DNA inference is deterministic and runs in two phases:

### Phase 1: Trait Scoring

10 trait scores (0.0–1.0) are derived from TIP fields:

| Trait | Primary TIP Signals |
|-------|---------------------|
| `adventure_seeking` | travel_interests: adventure, nature, sport |
| `luxury_orientation` | cabin_class: first/business; budget_style: luxury/comfort |
| `budget_consciousness` | budget_style: backpacker/budget; accommodation: hostel |
| `cultural_curiosity` | travel_interests: culture, history; many diverse interests |
| `food_focus` | travel_interests: food_drink; meal preferences |
| `sport_focus` | travel_interests: sport, adventure |
| `business_orientation` | cabin_class: business; airline loyalty programs |
| `family_orientation` | accommodation: resort; interests: beach, wellness |
| `digital_mobility` | accommodation: apartment; city interests; balanced budget |
| `photography_tendency` | interests: nature, culture, city |

### Phase 2: DNA Type Scoring

Each DNA type receives a weighted score derived from relevant trait scores. The highest-scoring type becomes the **primary DNA**. Types scoring above 0.15 become **secondary types**.

```python
from knowledge.ontology.dna_classifier import dna_inference_service

profile = {
    "id": "traveller_123",
    "preferences": {
        "budget_style": "balanced",
        "cabin_class": "economy",
        "travel_interests": ["adventure", "nature", "food_drink"],
        "accommodation_type": "hotel",
    }
}

dna = dna_inference_service.infer(profile)
print(dna.primary_type)       # "Adventure Traveller"
print(dna.secondary_types)    # ["Food Traveller", "Explorer"]
print(dna.confidence)         # 0.76
print(dna.traits)             # {"adventure_seeking": 0.75, "food_focus": 0.5, ...}
```

## TravellerDNA Entity

```python
@dataclass
class TravellerDNA:
    traveller_id: str
    primary_type: str              # e.g. "Adventure Traveller"
    secondary_types: list[str]     # e.g. ["Food Traveller", "Explorer"]
    confidence: float              # 0.0–1.0
    traits: dict[str, float]       # trait_name → score
    inferred_at: str               # ISO 8601 UTC timestamp
```

## Usage in Agents

The DNA inference service is called by `TravellerIntelligenceService` (in `ai/memory/`) when enriching a TIP. The resulting `TravellerDNA` is included in the agent context passed to all specialist agents.

Example agent personalisation:

- **BudgetAgent**: uses `luxury_orientation` trait to adjust cost estimates up or down
- **ExperienceAgent**: uses `primary_type` to prioritise experience categories
- **HotelAgent**: uses `family_orientation` and `luxury_orientation` to filter accommodation
- **VisaAgent**: unchanged — visa rules are objective, not personalised

## Evolution Roadmap

| Sprint | Enhancement |
|--------|-------------|
| Sprint 1 | Deterministic rule-based inference (current) |
| Sprint 2 | Infer DNA from past trips once booking history is added |
| Sprint 3 | ML model trained on anonymised trip patterns |
| Sprint 4 | Real-time DNA drift detection (DNA evolves as traveller preferences change) |
