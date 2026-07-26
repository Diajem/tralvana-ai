# TravelOS Configuration

The `ConfigurationManager` provides environment-aware configuration for all TravelOS services.

## Environments

| Environment | Key | Default |
|-------------|-----|---------|
| Development | `development` | Used when `TRAVELOS_ENV` is unset |
| Test | `test` | Used in CI and unit tests |
| Production | `production` | Requires `TRAVELOS_ENV=production` |

Set the active environment:

```bash
export TRAVELOS_ENV=production
```

## Defaults per Environment

| Setting | Development | Test | Production |
|---------|------------|------|------------|
| `api_host` | `localhost` | `localhost` | `0.0.0.0` |
| `api_port` | `8000` | `8001` | `8000` |
| `log_level` | `DEBUG` | `WARNING` | `INFO` |
| `debug` | `True` | `False` | `False` |
| `cors_origins` | `["http://localhost:3001"]` | `["http://localhost:3001"]` | from `CORS_ORIGINS` |

## Environment Variable Overrides

Any default can be overridden with an environment variable:

| Variable | Overrides |
|----------|-----------|
| `TRAVELOS_ENV` | Active environment |
| `LOG_LEVEL` | `config.log_level` |
| `API_HOST` | `config.api_host` |
| `API_PORT` | `config.api_port` |
| `CORS_ORIGINS` | `config.cors_origins` (comma-separated) |
| `DATABASE_URL` | SQLAlchemy PostgreSQL connection URL used by Alembic and commercial persistence |
| `REDIS_URL` | Private Redis URL; explicitly enables distributed conversation sessions |
| `TRALVANA_SESSION_TTL_SECONDS` | Conversation/session-index expiry; defaults to `604800` |
| `TRALVANA_REDIS_TIMEOUT_SECONDS` | Redis connect/operation timeout; defaults to `2` |

## Usage

```python
from travelos.config import config

# Check environment
config.environment         # â†’ "development"
config.is_production       # â†’ False
config.is_development      # â†’ True
config.is_test             # â†’ False

# Read settings
config.log_level           # â†’ "DEBUG"
config.debug               # â†’ True
config.api_host            # â†’ "localhost"
config.api_port            # â†’ 8000
config.cors_origins        # → ["http://localhost:3001"]

# Read any env var with a default
config.get("DATABASE_URL")
```

Production and Docker use a `postgresql+psycopg://` URL. SQLite is supported
only by isolated automated tests; see `docs/COMMERCIAL_DATA_FOUNDATION.md`.

`REDIS_URL` is optional for local/test operation. When absent, conversations
use the in-memory adapter. When present, it must be reachable; Tralvana fails
clearly instead of silently falling back to process-local state. See
`docs/REDIS_SESSION_PERSISTENCE.md`.

## Singleton

`ConfigurationManager` is a singleton â€” `config` is always the same instance:

```python
from travelos.config import config         # use the default singleton
from travelos.config import ConfigurationManager

# Force re-read (useful in tests)
ConfigurationManager.reset()
config2 = ConfigurationManager.get_instance()
```

## Adding New Settings

Add environment-specific defaults to `_DEFAULTS` only when a setting genuinely
differs by environment. Secret-backed or universal settings should normally be
properties that read their environment variable directly.

```python
@property
def example_timeout_seconds(self) -> float:
    raw = os.environ.get("EXAMPLE_TIMEOUT_SECONDS")
    return float(raw) if raw else 2.0
```
