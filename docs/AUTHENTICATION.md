# Clerk Authentication

T-031 delegates account registration, sign-in, recovery, and session management
to Clerk. Tralvana does not store passwords.

## Identity boundary

- Next.js uses `@clerk/nextjs` for the sign-in/sign-up UI and session token.
- Every non-public FastAPI router requires a verified Clerk session.
- FastAPI verifies tokens networklessly with Clerk's PEM public key.
- The verified Clerk `sub` claim is the canonical `traveller_id`; a caller
  cannot choose another account by changing a request body or URL.
- `/`, `/health`, `/health/ready`, the isolated `/demo` scenario, and public
  affiliate catalogue/click redirects remain available without a session.

## Local development

Authentication is disabled by default outside production so the deterministic
test suite and zero-setup local planner continue to work:

```text
TRALVANA_AUTH_MODE=DISABLED
```

To exercise Clerk locally, create one Clerk development application and set:

```text
TRALVANA_AUTH_MODE=CLERK
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=<Clerk publishable key>
CLERK_SECRET_KEY=<Clerk secret key>
CLERK_JWT_KEY=<Clerk PEM public key>
CLERK_AUTHORIZED_PARTIES=http://localhost:3001
```

Do not commit those values. The publishable key is intentionally browser-safe;
the secret key and PEM value still belong in the environment rather than Git.

## Production

Production is fail-closed:

- `TRALVANA_AUTH_MODE=CLERK` is mandatory.
- `CLERK_JWT_KEY` and `CLERK_AUTHORIZED_PARTIES` must be present before the API
  starts.
- The Render Blueprint marks every Clerk key as `sync: false`, so deployment
  waits for secure dashboard entry.
- `/health/ready` reports whether account authentication is configured without
  returning any key, token, claim, or personal data.

## Security behaviour

Missing, expired, wrongly signed, or wrong-origin session tokens return `401`.
An authenticated attempt to read another traveller's Profile, Goal, or Trip
returns `403`. Create and planning operations always overwrite any
client-supplied `traveller_id` with the verified Clerk user ID.
