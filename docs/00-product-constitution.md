# Product Constitution — Tralvana AI

## Vision

Tralvana is an AI-native travel operating system. It replaces fragmented booking tools with a single intelligent layer that plans, books, and manages travel on behalf of the traveller.

## Core Principles

1. **AI-first** — Every feature is designed around agent orchestration, not manual user flows.
2. **Traveller-centric** — The traveller profile is the single source of truth. Every recommendation is personalised.
3. **Transparent** — AI decisions are explainable. The system shows why it made a recommendation, not just what it recommends.
4. **Composable** — Agents are independent units that can be swapped, upgraded, or replaced without rebuilding the platform.
5. **Privacy by default** — Sensitive traveller data (documents, payment) is never logged or surfaced in AI context unnecessarily.

## What Tralvana Is Not

- Not a search engine for flights or hotels.
- Not a loyalty points aggregator.
- Not a generic travel chatbot.

## User Persona

**Primary:** Frequent business travellers who make 4+ trips per year and want automation over control.

**Secondary:** Travel managers at SMBs coordinating travel for small teams.

## Success Metrics (Sprint 0 baseline)

- Agent latency p95 < 2s
- Traveller profile retrieval < 100ms
- Zero hardcoded API keys in codebase
