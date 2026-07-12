# Platform Status — v0.3

**Date:** 2026-07-12
**Repository:** tralvana-ai (main, clean, `7b3c9bf`)
**Tests:** 913/913 passing · Ruff clean · frontend typecheck/build clean

A snapshot of what Tralvana AI's platform actually does today, what still
depends on legacy or mock code, and what isn't built yet. Written from
current repository state — `docs/TASK_TRACKER.md` and
`docs/TECHNICAL_DEBT_REGISTER.md` remain the authoritative, continuously
updated sources; this document is a point-in-time checkpoint between
v0.2.0-beta (Discovery Release) and whatever v0.3 formally ships as.

---

## 1. What Tralvana Is, Today

Tralvana AI is an AI-native travel operating system: one conversational
interface (Tralvana Travel) backed by an orchestration layer (Trip
Brain) that draws on six independent Discovery Intelligence modules,
explains its own recommendations, and — as of this release — has the
infrastructure in place to source data from mock, cached, or (in future)
live external providers without any of the layers above knowing the
difference.

```
Traveller
  → Conversation Engine (intent classification, decision engine)
    → Trip Brain (broad requests: PLAN_TRIP)
    │   → six Discovery Intelligence modules (parallel)
    │   → Explainability Engine (one unified explanation)
    → six narrow Discovery intents (direct, bypass Trip Brain)
    → TravelManager (legacy — MODIFY_TRIP, DESTINATION_QUESTION,
                      TRAVEL_ADVICE, BUDGET_ADVICE only)

  Discovery modules (Flight, Accommodation, Weather)
    → Intelligence Gateway (cache · retry · failover · rate limit)
      → Provider contract (Mock today; Live Provider Framework built,
                            no vendor connected)
```

## 2. Completed Work (T-001 – T-026)

### Core reasoning stack
| Area | Status |
|---|---|
| Traveller DNA + Travel Intelligence Layer | Complete (T-004) |
| Conversation Engine (intent classification, decision engine) | Complete (T-006) |
| Goal Planning Engine | Complete (T-007) |
| Trip Planning Engine (`ai/planning/`) | Complete (T-008) |

### Discovery Layer — all six modules complete
| Module | Task | Pattern |
|---|---|---|
| Flight Intelligence | T-015 | Ranked list |
| Accommodation Intelligence | T-016 | Ranked list, first Provider/Normalizer split |
| Destination Intelligence | T-017 | Dual-mode (city / no-city) |
| Budget Intelligence | T-018 | Ranked list, 5 fixed tiers |
| Visa Intelligence | T-019 | Single assessment, not ranked |
| Weather & Safety Intelligence | T-020 | Dual-mode, structured risk object |

Every module follows the same 7-stage pipeline
(`docs/DISCOVERY_LAYER_PATTERN.md`): Provider → Normalizer → Scorer →
Reasoner → Risk Assessor → Orchestrator → API.

### Orchestration and explainability
| Area | Task | Notes |
|---|---|---|
| Trip Brain | T-021 (architecture), T-022 (implementation) | Orchestrates all six Discovery modules for `PLAN_TRIP` in parallel; merges, resolves presentation conflicts, aggregates confidence |
| Legacy orchestration investigation | T-023 | Found `TravelManager`/`AgentRegistry` still live for 4 intents (not dormant, as originally assumed) — corrected the record rather than deleting live code; see §4 |
| Explainability Engine | T-024 | Turns Trip Brain's merged results into recommendation drivers, trade-offs, confidence explanation, and follow-up Q&A (`EXPLAIN_RECOMMENDATION` intent, `POST /explain`) |

### Provider infrastructure
| Area | Task | Notes |
|---|---|---|
| Intelligence Gateway | T-025 | `travelos/intelligence_gateway/` — provider contract, registry, deterministic selection, cache, retry, failover, rate limiting. Flight/Accommodation/Weather wired through it; Destination/Budget/Visa still call their mock provider directly (TD-019) |
| Live Provider Framework | T-026 | `travelos/live_providers/` — `BaseLiveProvider`, auth strategies (API key / bearer / OAuth2-interface), fake transport, standard error model, health/tracing/metrics. **No live vendor connected** — every provider running today is still a mock |

### Platform layer
| Area | Task | Notes |
|---|---|---|
| SDK, DI container, service registry, config, logging, event bus | T-011 | `travelos/` |
| Testing framework | T-012 | pytest, `services/api/tests/` + `ai/tests/` (+ `travelos/tests/` since T-025) |
| CI/CD | T-013 | GitHub Actions — pytest required, Ruff + frontend lint/build advisory |
| Repository stabilisation | T-014 | Removed dead `ai/orchestration/`, resolved duplicate type definitions |

## 3. Test and Quality Status

| Metric | Value |
|---|---|
| Total tests | 913 (all passing) |
| Test roots | `services/api/tests/`, `ai/tests/`, `travelos/tests/` |
| Ruff | 0 violations |
| Frontend typecheck | Clean |
| Frontend production build | Clean, 21 routes |
| No live network calls anywhere in the test suite | Confirmed (mock providers + `FakeTransport` only) |

Growth: 92 tests at T-012 → 574 at the end of the Discovery Layer (T-020)
→ 649 (Trip Brain) → 723 (Explainability) → 833 (Intelligence Gateway) →
**913** (Live Provider Framework).

## 4. Known Load-Bearing Legacy Code

Not everything old has been retired — this is the most important
correction this release makes to the historical record.

**`ai/manager/TravelManager` + `ai/registry/AgentRegistry` + five
Sprint-1 placeholder agents are still live**, dispatching four intents
(`MODIFY_TRIP`, `DESTINATION_QUESTION`, `TRAVEL_ADVICE`,
`BUDGET_ADVICE`) that return static "pending_live_data" stub output.
Earlier documentation (ADR-017) assumed Trip Brain's T-022 landing would
leave this code dormant; T-023's investigation found it still handles a
quarter of the intent surface and cannot be deleted without breaking
those four flows. Retirement is tracked as **T-032**, blocked on giving
those four intents a real Discovery-module or Trip Brain equivalent
first. See `docs/ADR/ADR-018-legacy-orchestration-retirement.md` and
`docs/TECHNICAL_DEBT_REGISTER.md` TD-018.

## 5. What's Explicitly Not Built Yet

- **No live external provider is connected.** Flights, hotels, weather,
  visa data — all deterministic mocks. The Live Provider Framework
  (T-026) exists to receive a real integration; none has been built.
- **No persistence.** Goals, Trips, and conversation sessions are all
  in-memory — restart the API and they're gone (T-034, T-035 planned).
- **No authentication.** Every endpoint, including the internal
  diagnostics endpoint, is open (T-031 planned).
- **No real HTTP transport** for live providers — only the deterministic
  `FakeTransport` (TD-021).
- **No real OAuth2 token exchange** — the client-credentials strategy is
  an interface only (TD-022).
- **Destination, Budget, and Visa Intelligence** don't go through the
  Intelligence Gateway yet — only Flight, Accommodation, and Weather do
  (TD-019).
- **No Maps, Currency, or Events Discovery module** exists yet, so those
  three Intelligence Gateway capabilities have no registered provider
  (TD-020).

## 6. Architecture Decision Records on File

| ADR | Title |
|---|---|
| 001–016 | Conversation Engine through Weather Intelligence Engine (one per foundational/Discovery component) |
| 017 | Trip Brain architecture |
| 018 | Legacy orchestration retirement (investigation, not deletion) |
| 019 | Explainability Engine |
| 020 | Intelligence Gateway (`travelos/` vs. suggested `platform/` path deviation) |
| 021 | Live Provider Framework |

## 7. Immediate Backlog Priorities

From `docs/TASK_TRACKER.md`, highest-signal open items:

| Task | Priority | Blocked on |
|---|---|---|
| T-032 — Migrate remaining intents off legacy TravelManager | medium | Nothing — unblocked, not started |
| T-012A — Platform layer test coverage (SDK, EventBus, shared types) | medium | Nothing — unblocked, not started |
| T-034 — PostgreSQL persistence (Goals + Trips) | critical | Nothing — unblocked, not started |
| T-031 — Auth layer | high | Nothing — unblocked, not started |
| T-035 — Redis session store | high | Nothing — unblocked, not started |
| TD-019 — Wire Destination/Budget/Visa to the Intelligence Gateway | — | Nothing — same proven pattern as Flight/Accommodation/Weather |

No task is currently blocked by another incomplete task except T-032
(technically unblocked, but its absence is what keeps TD-018 open).

---

*Generated as a point-in-time snapshot. For live status, read
`docs/TASK_TRACKER.md` (task list) and `docs/TECHNICAL_DEBT_REGISTER.md`
(open debt) directly — they change more frequently than this file will
be updated.*
