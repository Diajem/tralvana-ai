# Commercial Data Foundation

T-042 establishes Tralvana's durable commercial ledger. It records the chain
from a partner and affiliate programme through an attributed outbound click,
vendor conversion, and commission record.

## Scope

The first migration creates five tables:

| Table | Purpose |
|---|---|
| `commercial_partners` | Partner identity and lifecycle state |
| `affiliate_programmes` | Vertical, affiliate identifier, tracking template, currency, and disclosure |
| `outbound_clicks` | Trip/recommendation attribution and the resolved tracking URL |
| `affiliate_conversions` | Vendor booking reference and gross booking value |
| `commission_records` | Expected, approved, rejected, or paid commission amounts |

The domain uses UUID identifiers, decimal monetary values, UTC timestamps,
foreign keys, uniqueness constraints, and non-negative amount constraints.
Only an already-hashed anonymous session reference may be stored on a click;
the schema has no raw IP address, user agent, email, or traveller name fields.

## Running PostgreSQL

The easiest local path is Docker Compose. It starts PostgreSQL, waits for its
health check, runs Alembic to the latest revision, then starts the API:

```bash
cp .env.example .env
docker compose up --build
```

For an existing PostgreSQL instance, set `DATABASE_URL` and run:

```bash
PYTHONPATH=.:services/api python -m alembic -c services/api/alembic.ini upgrade head
```

On Windows PowerShell:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://user:password@localhost:5432/tralvana"
.\scripts\migrate-database.ps1
```

The safe readiness endpoint is `GET /internal/commercial/status`. It reports
only whether storage is configured/reachable, the schema version, and aggregate
row counts. It never returns a hostname, URL, username, or password.

## Deliberate boundaries

- No public booking, redirect, payment, webhook, or administration endpoint is added.
- Affiliate identifiers are commercial routing values; API keys and vendor secrets
  remain environment-backed and are not stored here.
- Goals and Trips remain in memory. T-034 still owns their PostgreSQL migration;
  click records use nullable external references until that work lands.
- SQLite is supported for isolated repository and migration tests only. PostgreSQL
  is the deployment database.
