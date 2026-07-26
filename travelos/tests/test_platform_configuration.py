import pytest

from travelos.config.configuration_manager import ConfigurationManager


_CONFIG_ENV_VARS = {
    "TRAVELOS_ENV",
    "LOG_LEVEL",
    "API_HOST",
    "API_PORT",
    "CORS_ORIGINS",
    "TRALVANA_PROVIDER_ENVIRONMENT",
    "PROVIDER_ENVIRONMENT",
    "PROVIDER_CACHE_ENABLED",
    "PROVIDER_RETRY_ENABLED",
    "PROVIDER_DEFAULT_PRIORITY",
    "PROVIDER_FLIGHTS",
    "PROVIDER_HTTP_TIMEOUT_SECONDS",
    "PROVIDER_RETRY_MAX_ATTEMPTS",
    "PROVIDER_HEALTHCHECK_ENABLED",
    "TRALVANA_FLIGHT_PROVIDER_MODE",
    "TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED",
    "TRALVANA_ACCOMMODATION_PROVIDER_MODE",
    "TRALVANA_ACCOMMODATION_MOCK_FALLBACK_ENABLED",
    "TRALVANA_EVENT_PROVIDER_MODE",
    "TRALVANA_EVENT_MOCK_FALLBACK_ENABLED",
    "REDIS_URL",
    "TRALVANA_SESSION_TTL_SECONDS",
    "TRALVANA_REDIS_TIMEOUT_SECONDS",
}


@pytest.fixture(autouse=True)
def clean_configuration_environment(monkeypatch):
    for name in _CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    ConfigurationManager.reset()
    yield
    ConfigurationManager.reset()


@pytest.mark.parametrize(
    ("environment", "host", "port", "log_level", "debug"),
    [
        ("development", "localhost", 8000, "DEBUG", True),
        ("test", "localhost", 8001, "WARNING", False),
        ("production", "0.0.0.0", 8000, "INFO", False),
    ],
)
def test_environment_defaults(
    monkeypatch,
    environment,
    host,
    port,
    log_level,
    debug,
):
    monkeypatch.setenv("TRAVELOS_ENV", environment)
    config = ConfigurationManager()

    assert config.environment == environment
    assert config.api_host == host
    assert config.api_port == port
    assert config.log_level == log_level
    assert config.debug is debug
    assert config.is_development is (environment == "development")
    assert config.is_test is (environment == "test")
    assert config.is_production is (environment == "production")


def test_unknown_environment_falls_back_to_development(monkeypatch):
    monkeypatch.setenv("TRAVELOS_ENV", "unknown")

    assert ConfigurationManager().environment == "development"


def test_general_overrides_and_cors_parsing(monkeypatch):
    monkeypatch.setenv("API_HOST", "api.internal")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "error")
    monkeypatch.setenv(
        "CORS_ORIGINS",
        " https://tralvana.com, ,https://www.tralvana.com ",
    )
    config = ConfigurationManager()

    assert config.api_host == "api.internal"
    assert config.api_port == 9000
    assert config.log_level == "ERROR"
    assert config.cors_origins == [
        "https://tralvana.com",
        "https://www.tralvana.com",
    ]
    assert config.get("UNSET_SETTING", "fallback") == "fallback"


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_boolean_settings_accept_documented_truthy_values(monkeypatch, value):
    monkeypatch.setenv("PROVIDER_CACHE_ENABLED", value)
    monkeypatch.setenv("TRALVANA_EVENT_MOCK_FALLBACK_ENABLED", value)
    config = ConfigurationManager()

    assert config.cache_enabled is True
    assert config.event_mock_fallback_enabled is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "anything"])
def test_boolean_settings_fail_closed_for_other_values(monkeypatch, value):
    monkeypatch.setenv("PROVIDER_RETRY_ENABLED", value)
    monkeypatch.setenv("TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED", value)
    config = ConfigurationManager()

    assert config.retry_enabled is False
    assert config.flight_mock_fallback_enabled is False


def test_provider_environment_precedence_and_production_default(monkeypatch):
    monkeypatch.setenv("PROVIDER_ENVIRONMENT", "sandbox")
    assert ConfigurationManager().provider_environment == "SANDBOX"

    monkeypatch.setenv("TRALVANA_PROVIDER_ENVIRONMENT", "mock")
    assert ConfigurationManager().provider_environment == "MOCK"

    monkeypatch.delenv("PROVIDER_ENVIRONMENT")
    monkeypatch.delenv("TRALVANA_PROVIDER_ENVIRONMENT")
    monkeypatch.setenv("TRAVELOS_ENV", "production")
    assert ConfigurationManager().provider_environment == "PRODUCTION"


def test_provider_numeric_and_override_settings(monkeypatch):
    monkeypatch.setenv("PROVIDER_DEFAULT_PRIORITY", "25")
    monkeypatch.setenv("PROVIDER_FLIGHTS", "duffel")
    monkeypatch.setenv("PROVIDER_HTTP_TIMEOUT_SECONDS", "2.5")
    monkeypatch.setenv("PROVIDER_RETRY_MAX_ATTEMPTS", "4")
    config = ConfigurationManager()

    assert config.default_provider_priority == 25
    assert config.provider_override_for("flights") == "duffel"
    assert config.provider_override_for("weather") is None
    assert config.provider_http_timeout_seconds == 2.5
    assert config.provider_retry_max_attempts == 4
    assert config.provider_healthcheck_enabled is True


def test_conversation_session_persistence_settings(monkeypatch):
    config = ConfigurationManager()
    assert config.redis_url is None
    assert config.conversation_session_ttl_seconds == 604800
    assert config.redis_socket_timeout_seconds == 2.0

    monkeypatch.setenv("REDIS_URL", " redis://private-host:6379/0 ")
    monkeypatch.setenv("TRALVANA_SESSION_TTL_SECONDS", "3600")
    monkeypatch.setenv("TRALVANA_REDIS_TIMEOUT_SECONDS", "1.5")
    config = ConfigurationManager()
    assert config.redis_url == "redis://private-host:6379/0"
    assert config.conversation_session_ttl_seconds == 3600
    assert config.redis_socket_timeout_seconds == 1.5


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("TRALVANA_SESSION_TTL_SECONDS", "0"),
        ("TRALVANA_REDIS_TIMEOUT_SECONDS", "-1"),
    ],
)
def test_conversation_session_numeric_settings_reject_non_positive_values(
    monkeypatch, name, value
):
    monkeypatch.setenv(name, value)
    config = ConfigurationManager()

    property_name = {
        "TRALVANA_SESSION_TTL_SECONDS": "conversation_session_ttl_seconds",
        "TRALVANA_REDIS_TIMEOUT_SECONDS": "redis_socket_timeout_seconds",
    }[name]
    with pytest.raises(ValueError):
        getattr(config, property_name)


@pytest.mark.parametrize(
    ("name", "valid", "invalid", "expected"),
    [
        ("TRALVANA_FLIGHT_PROVIDER_MODE", "live_sandbox", "live", "LIVE_SANDBOX"),
        (
            "TRALVANA_ACCOMMODATION_PROVIDER_MODE",
            "live_sandbox",
            "production",
            "LIVE_SANDBOX",
        ),
        ("TRALVANA_EVENT_PROVIDER_MODE", "live", "sandbox", "LIVE"),
    ],
)
def test_capability_modes_normalise_valid_values_and_fail_closed(
    monkeypatch,
    name,
    valid,
    invalid,
    expected,
):
    property_name = {
        "TRALVANA_FLIGHT_PROVIDER_MODE": "flight_provider_mode",
        "TRALVANA_ACCOMMODATION_PROVIDER_MODE": "accommodation_provider_mode",
        "TRALVANA_EVENT_PROVIDER_MODE": "event_provider_mode",
    }[name]

    monkeypatch.setenv(name, valid)
    assert getattr(ConfigurationManager(), property_name) == expected

    monkeypatch.setenv(name, invalid)
    assert getattr(ConfigurationManager(), property_name) == "MOCK"


def test_singleton_reset_reloads_environment(monkeypatch):
    monkeypatch.setenv("TRAVELOS_ENV", "development")
    first = ConfigurationManager.get_instance()
    assert first.environment == "development"

    monkeypatch.setenv("TRAVELOS_ENV", "test")
    assert ConfigurationManager.get_instance() is first

    ConfigurationManager.reset()
    second = ConfigurationManager.get_instance()
    assert second is not first
    assert second.environment == "test"
