# Production Deployment Foundation

T-045 prepares a protected beta deployment without replacing the existing
`tralvana.com` website.

## Deployment shape

| Host | Purpose | Change in T-045 |
|---|---|---|
| `tralvana.com` | Existing public affiliate/content website | No change |
| `app.tralvana.com` | Planned paid-production web host | No DNS change during free acceptance |
| `api.tralvana.com` | Planned paid-production API host | No DNS change during free acceptance |
| `tralvana-web.onrender.com` | Free acceptance web application | Active temporary Render host |
| `tralvana-api.onrender.com` | Free acceptance FastAPI backend | Active temporary Render host |

The root `render.yaml` initially deploys the two services and PostgreSQL on
Render's free plans in Frankfurt so the complete hosted journey can be tested
before any recurring hosting commitment. The API startup applies Alembic
migrations and idempotently seeds the 11 already-verified affiliate programmes.

## Safety defaults

- All Discovery modules remain in `MOCK` mode. A production deployment does
  not become a Duffel sandbox or live-ticketing system merely because a token
  exists elsewhere.
- No OpenAI, Anthropic, Duffel, payment, or affiliate secret is defined by the
  Blueprint.
- The database rejects public network connections.
- `/health` is liveness only. `/health/ready` fails with HTTP 503 until the
  database is reachable, Alembic is at revision `0003`, and the verified
  affiliate catalogue has been seeded.
- Affiliate links retain the disclosure and destination allow-list controls
  implemented in T-043.

## First deployment

1. In Render, create a Blueprint from `Diajem/tralvana-ai`. All three resources
   should show the Free instance type; do not continue if a paid plan appears.
2. Wait for `tralvana-api` and `tralvana-web` to deploy successfully using their
   temporary Render addresses.
3. During free hosted acceptance, use `tralvana-web.onrender.com` and
   `tralvana-api.onrender.com`. Do not add or alter any `tralvana.com` DNS
   records.
4. Confirm `/health/ready` reports the database, schema, and affiliate
   catalogue as ready.
5. Run the read-only smoke test against the temporary Render addresses:

   ```bash
   python scripts/smoke-production.py
   ```

6. Test one disclosed affiliate click in a controlled browser session, then
   verify that the click count increased through
   `GET /internal/commercial/status`. Do not purchase solely for this test.

## Rollback

The existing website is independent, so a beta failure does not affect
`tralvana.com`. Disable or roll back the `tralvana-web`/`tralvana-api` Render
services. No DNS rollback is needed during free acceptance. If custom subdomains
are added at a later paid-production cutover, remove only those two subdomain
records during rollback. The PostgreSQL database should be retained for audit
history unless deletion is separately authorised.

## Free-test limitations

- Free web services sleep when inactive, so the first request can be slow.
- The free PostgreSQL database expires after 30 days and must not become the
  permanent commission ledger.
- Testing uses Render's temporary service addresses first. Custom-domain DNS is
  deferred until the paid production cutover is separately approved.

After hosted acceptance testing passes, change both services to `starter` and
PostgreSQL to `basic-256mb`, then approve the displayed recurring cost before
connecting `app.tralvana.com` and `api.tralvana.com`.

Fresh affiliate IDs are not required for this first beta: the seed contains the
11 verified programmes already carried over from the current website. New or
inactive programmes should be added later only after their tracked links and
account ownership are verified.
