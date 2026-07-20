# ADR-031: Protect the current site and deploy the AI beta on subdomains

**Date**: 2026-07-20

**Status**: Accepted

**Task**: T-045

## Context

`tralvana.com` is already a live content and affiliate website. The AI platform
needs real hosting, PostgreSQL, migrations, readiness checks, and repeatable
deployment, but it is not yet appropriate to replace the established site or
enable supplier booking/payment behaviour.

## Decision

1. Preserve `tralvana.com` unchanged.
2. Deploy the AI web application at `app.tralvana.com` and FastAPI at
   `api.tralvana.com` through one Render Blueprint.
3. Begin hosted acceptance testing on free compute and free PostgreSQL; keep the
   database off the public network and upgrade before public launch.
4. Run migrations and the idempotent verified-affiliate seed at API startup,
   then gate traffic on database/schema/catalogue readiness.
5. Keep every live-provider switch explicitly in mock mode.
6. Promote the AI experience to the root domain only after beta validation,
   legal/commercial readiness, monitoring, and a separate approved cutover.

## Consequences

The current revenue/content site remains the rollback boundary. The AI beta can
be commissioned and tested independently, while ticketing, payments, refunds,
packages, and network-specific commission imports remain outside this task.
The free database is disposable after 30 days and is never the permanent
commission ledger; paid production activation is a separate owner-approved
cutover after hosted acceptance testing.
