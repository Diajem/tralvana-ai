# Production Deployment Foundation

T-045 prepares a protected beta deployment without replacing the existing
`tralvana.com` website.

## Deployment shape

| Host | Purpose | Change in T-045 |
|---|---|---|
| `tralvana.com` | Existing public affiliate/content website | No change |
| `app.tralvana.com` | Tralvana AI beta web application | New Render web service |
| `api.tralvana.com` | FastAPI backend | New Render web service |

The root `render.yaml` is a Render Blueprint for the two paid Starter services
and a paid, private-network-only PostgreSQL database in Frankfurt. Deployments
wait for GitHub checks. The API pre-deploy step applies Alembic migrations and
idempotently seeds the 11 already-verified affiliate programmes.

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

1. In Render, create a Blueprint from `Diajem/tralvana-ai` and review the three
   paid resources before confirming charges.
2. Wait for `tralvana-api` and `tralvana-web` to deploy successfully using their
   temporary Render addresses.
3. Add the DNS records Render supplies for `api.tralvana.com` and
   `app.tralvana.com`. Do not alter the root `tralvana.com` records.
4. Wait for both custom-domain certificates to become active.
5. Run the read-only smoke test:

   ```bash
   python scripts/smoke-production.py
   ```

6. Test one disclosed affiliate click in a controlled browser session, then
   verify that the click count increased through
   `GET /internal/commercial/status`. Do not purchase solely for this test.

## Rollback

The existing website is independent, so a beta failure does not affect
`tralvana.com`. Disable or roll back the `tralvana-web`/`tralvana-api` Render
services and remove only the two new subdomain records if rollback is needed.
The PostgreSQL database should be retained for audit history unless deletion is
separately authorised.

## Inputs still needed from the owner

- A Render account/workspace connected to the approved GitHub repository.
- Approval of the displayed monthly cost for two Starter services and one
  Basic-256MB PostgreSQL database.
- Access to the DNS manager for `tralvana.com` when Render provides the exact
  records.

Fresh affiliate IDs are not required for this first beta: the seed contains the
11 verified programmes already carried over from the current website. New or
inactive programmes should be added later only after their tracked links and
account ownership are verified.
