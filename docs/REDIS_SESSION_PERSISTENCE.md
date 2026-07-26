# Redis Conversation Session Persistence

T-035 removes the Conversation Engine's process-local persistence limit while
keeping local development and CI zero-setup.

## Backend selection

| Configuration | Adapter | Intended use |
|---|---|---|
| `REDIS_URL` unset | `InMemorySessionStore` | Local development, unit tests, one-process acceptance |
| `REDIS_URL` set and reachable | `RedisSessionStore` | Multi-worker or multi-instance deployment |
| `REDIS_URL` set but unreachable | Startup/configuration failure | Prevents silent split-brain sessions |

The presence of a URL is the only switch. The application never guesses a
Redis endpoint and never logs or returns the URL.

## Stored state

Each conversation record preserves:

- traveller, Goal, and Trip identifiers;
- complete user/assistant history;
- pending questions and facts gathered across planning turns;
- context summary and active goal;
- the most recent unified Trip Brain recommendation, including module
  results and explainability output.

Records use versioned JSON, not pickle. Unsupported or malformed records are
discarded as cache misses so untrusted serialized Python objects are never
executed.

## Keys and expiry

```text
tralvana:conversation:<conversation_id>
tralvana:conversation:trip:<trip_id>
```

The second key is an O(1) lookup index for `POST /explain` calls that only
have a Trip ID. Both keys are written in one Redis transaction and receive the
same expiry. The default TTL is seven days (`604800` seconds); override it with
`TRALVANA_SESSION_TTL_SECONDS`.

Changing a session's Trip ID removes its old index in the same transaction.
Stale or corrupt indexes are removed when encountered.

## Configuration

```env
REDIS_URL=redis://default:password@private-host:6379/0
TRALVANA_SESSION_TTL_SECONDS=604800
TRALVANA_REDIS_TIMEOUT_SECONDS=2
```

`REDIS_URL` is a secret and belongs in the hosting provider's private
environment settings. Do not add it to `.env.example`, screenshots, logs, or
commits with a real value.

## Deployment boundary

T-035 adds the application adapter and the Redis client. It does not provision
a paid hosted Redis service. The current single-instance free acceptance
deployment can continue using the in-memory adapter. Before increasing the API
replica/worker count, attach a private managed Redis service and set
`REDIS_URL`; otherwise requests routed to different processes will not share
conversation state.

Redis is session state, not the system of record for Goals or Trips. Those
remain in PostgreSQL under T-034.
