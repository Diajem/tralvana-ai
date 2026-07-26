# Live Event Search — Ticketmaster Discovery (T-054)

Tralvana can retrieve current public event listings for a destination and
travel-date window through Ticketmaster Discovery API v2.

## Safety boundary

- Search and public event links only.
- No reservation, checkout, payment, ticket purchase, or inventory guarantee.
- A key in `.env` does not enable network calls by itself.
- Live mode fails at startup when its key is missing.
- Live failures return a clear unavailable result by default.
- Optional curated fallback is labelled `MOCK_FALLBACK`; it is never blended
  with live listings.

## Local configuration

Add these values to the repository-root `.env`:

```env
TICKETMASTER_API_KEY=your_consumer_key
TRALVANA_EVENT_PROVIDER_MODE=LIVE
TRALVANA_EVENT_MOCK_FALLBACK_ENABLED=false
```

Do not add quotes or commit `.env`. Restart the API after changing provider
mode. `scripts/start-api.ps1` now passes the repository `.env` to Uvicorn
automatically when the file exists.

`MOCK` remains the default. `LIVE` selects the Ticketmaster production
provider only for `Capability.EVENTS`; Flights, Accommodation, Weather, and
every other capability keep their own provider settings.

## Safe verification

From PowerShell in `C:\Users\Peter\tralvana-ai`:

```powershell
.\.venv\Scripts\python.exe scripts\verify_ticketmaster_live.py
```

The script makes one New York event search for 7–22 August 2026 and prints
only safe diagnostics and up to three public event names. It never prints the
key, request query string, headers, or raw response.

Expected evidence:

- HTTP `200`
- `provider_status: AVAILABLE`
- `data_source: TICKETMASTER_DISCOVERY_API`
- zero or more current listings, depending on provider coverage

Zero listings is a valid live response, not permission failure.

## Public grounding

Live options carry exact dates and public event links only when present in the
provider response. The planner labels them `LIVE`, timestamps the retrieval,
and still tells the traveller to confirm:

- current event status;
- ticket inventory and price;
- venue rules and accessibility;
- schedule changes before buying non-refundable travel.

Ticketmaster's default developer quota is 5,000 calls per day and five
requests per second. Tralvana's existing gateway cache, retry, rate-limit, and
diagnostic layers remain in the path.
