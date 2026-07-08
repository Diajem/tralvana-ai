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
| `cors_origins` | `["http://localhost:3000"]` | `["http://localhost:3000"]` | from `CORS_ORIGINS` |

## Environment Variable Overrides

Any default can be overridden with an environment variable:

| Variable | Overrides |
|----------|-----------|
| `TRAVELOS_ENV` | Active environment |
| `LOG_LEVEL` | `config.log_level` |
| `API_HOST` | `config.api_host` |
| `API_PORT` | `config.api_port` |
| `CORS_ORIGINS` | `config.cors_origins` (comma-separated) |

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
config.cors_origins        # â†’ ["http://localhost:3000"]

# Read any env var with a default
config.get("DATABASE_URL", "sqlite:///local.db")
```

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

Add to `_DEFAULTS` in `configuration_manager.py`:

```python
@dataclass
class EnvironmentConfig:
    ...
    redis_url: str = "redis://localhost:6379"

_DEFAULTS = {
    "development": EnvironmentConfig(... redis_url="redis://localhost:6379"),
    "production":  EnvironmentConfig(... redis_url=os.environ.get("REDIS_URL", "")),
}
```

Then add a property:

```python
@property
def redis_url(self) -> str:
    return os.environ.get("REDIS_URL", self._env.redis_url)
```
