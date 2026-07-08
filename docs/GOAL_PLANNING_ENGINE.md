# Goal Planning Engine

The Goal Planning Engine enables TravelOS to plan around traveller objectives, not just destinations. Before a trip is planned, a Goal captures what the traveller wants to achieve — their purpose, budget, timeframe, and success criteria.

## Architecture Position

```
Traveller Profile (TIP)
       ↓
    Goal
       ↓
  Conversation
       ↓
   Knowledge Graph (TIL)
       ↓
    Reasoning
       ↓
  Trip Planning
```

## Components

### 1. Goal Domain (`services/api/app/domains/goals/`)

| File | Responsibility |
|------|---------------|
| `models.py` | `Goal` dataclass, `GoalType` enum, `GoalStatus` enum |
| `schemas.py` | Pydantic request/response models |
| `repository.py` | In-memory store — PostgreSQL adapter in Sprint 3 |
| `service.py` | Business logic, auto-classification, readiness scoring |
| `router.py` | 4 FastAPI endpoints |

### 2. AI Goals Layer (`ai/goals/`)

| File | Responsibility |
|------|---------------|
| `goal_classifier.py` | Infers `GoalType` from text or interest lists |
| `goal_reasoner.py` | Returns planning readiness analysis |

### 3. Frontend (`apps/web/src/app/goals/`)

| Page | Route | Purpose |
|------|-------|---------|
| `new/page.tsx` | `/goals/new` | Create a new goal (client component with form) |
| `[id]/page.tsx` | `/goals/:id` | View goal summary, readiness score, missing information |

## Goal Types (11)

| Type | Trigger Keywords | Suitable Agents |
|------|-----------------|----------------|
| `RELAXATION` | relax, spa, beach, wellness | Flight, Hotel, Experience |
| `ADVENTURE` | hiking, safari, extreme | Flight, Hotel, Experience, Visa |
| `FOOTBALL_TRAVEL` | football, match, stadium | Flight, Hotel, Experience |
| `FAMILY_TRIP` | family, kids, children | Flight, Hotel, Experience |
| `BUSINESS_TRAVEL` | conference, meeting, client | Flight, Hotel |
| `FOOD_TOUR` | food, cuisine, culinary | Flight, Hotel, Experience |
| `PHOTOGRAPHY` | camera, photography, shoot | Flight, Hotel, Experience |
| `PILGRIMAGE` | pilgrimage, hajj, holy, sacred | Flight, Hotel, Visa, Experience |
| `DIASPORA_TRAVEL` | heritage, roots, homeland | Flight, Hotel, Visa, Experience |
| `ROMANTIC_TRIP` | honeymoon, romantic, couples | Flight, Hotel, Experience |
| `GENERAL_TRAVEL` | default | Flight, Hotel |

## Goal Statuses

| Status | Meaning |
|--------|---------|
| `DRAFT` | Just created, missing key fields |
| `ACTIVE` | Core fields filled (≥75% readiness) |
| `READY_FOR_PLANNING` | Fully specified (≥90% readiness), agents can proceed |
| `PLANNED` | Trip has been planned against this goal |
| `ARCHIVED` | Goal was cancelled or superseded |

Status is automatically promoted by the GoalService based on readiness score.

## Planning Readiness Score

| Field | Weight |
|-------|--------|
| Title set | 15% |
| Goal type ≠ GENERAL_TRAVEL | 10% |
| Budget min + max set | 20% |
| Timeframe earliest + latest set | 20% |
| Travellers ≥ 1 adult | 10% |
| Interests non-empty | 10% |
| Success criteria non-empty | 10% |
| Constraints non-empty | 5% |

Thresholds: `ACTIVE` at 75%; `READY_FOR_PLANNING` at 90%.

## Conversation Integration

When the Conversation Engine detects a `PLAN_TRIP` intent and the session has no active goal, a draft Goal is automatically created and the `goal_id` is:
1. Stored on the `ConversationSession`
2. Returned in the API response as `goal_id`
3. Accessible at `/goals/{goal_id}`

## Sprint Roadmap

| Sprint | Enhancement |
|--------|-------------|
| 1 | In-memory store, keyword classification, readiness scoring (current) |
| 2 | Goal creation from natural language; link Goal→Trip |
| 3 | PostgreSQL persistence; Goal history and versioning |
| 4 | ML goal classification; multi-goal prioritisation |
