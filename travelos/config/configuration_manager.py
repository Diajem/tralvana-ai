from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnvironmentConfig:
    name: str
    api_host: str
    api_port: int
    log_level: str
    debug: bool
    cors_origins: list[str] = field(default_factory=list)


def _cors_from_env(default: list[str]) -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "")
    return [o.strip() for o in raw.split(",") if o.strip()] if raw else default


_DEFAULTS: dict[str, EnvironmentConfig] = {
    "development": EnvironmentConfig(
        name="development",
        api_host="localhost",
        api_port=8000,
        log_level="DEBUG",
        debug=True,
        cors_origins=["http://localhost:3000"],
    ),
    "test": EnvironmentConfig(
        name="test",
        api_host="localhost",
        api_port=8001,
        log_level="WARNING",
        debug=False,
        cors_origins=["http://localhost:3000"],
    ),
    "production": EnvironmentConfig(
        name="production",
        api_host="0.0.0.0",
        api_port=8000,
        log_level="INFO",
        debug=False,
        cors_origins=_cors_from_env([]),
    ),
}


class ConfigurationManager:
    """
    Reads environment-based configuration for TravelOS.

    Active environment is set via TRAVELOS_ENV (default: development).
    Individual settings can be overridden with environment variables.
    """

    _instance: ConfigurationManager | None = None

    def __init__(self) -> None:
        env_name = os.environ.get("TRAVELOS_ENV", "development").lower()
        self._env = _DEFAULTS.get(env_name, _DEFAULTS["development"])

    @classmethod
    def get_instance(cls) -> ConfigurationManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Force re-read of environment. Useful in tests."""
        cls._instance = None

    # ------------------------------------------------------------------
    # Environment identity
    # ------------------------------------------------------------------

    @property
    def environment(self) -> str:
        return self._env.name

    @property
    def is_development(self) -> bool:
        return self._env.name == "development"

    @property
    def is_test(self) -> bool:
        return self._env.name == "test"

    @property
    def is_production(self) -> bool:
        return self._env.name == "production"

    # ------------------------------------------------------------------
    # Settings (environment vars override defaults)
    # ------------------------------------------------------------------

    @property
    def log_level(self) -> str:
        return os.environ.get("LOG_LEVEL", self._env.log_level).upper()

    @property
    def debug(self) -> bool:
        return self._env.debug

    @property
    def api_host(self) -> str:
        return os.environ.get("API_HOST", self._env.api_host)

    @property
    def api_port(self) -> int:
        raw = os.environ.get("API_PORT")
        return int(raw) if raw else self._env.api_port

    @property
    def cors_origins(self) -> list[str]:
        return self._env.cors_origins

    def get(self, key: str, default: Any = None) -> Any:
        """Read any environment variable with an optional default."""
        return os.environ.get(key, default)


config = ConfigurationManager.get_instance()
