from app.config import Settings


def test_default_settings_are_safe():
    settings = Settings(_env_file=None)
    assert settings.app_version == "0.5.0"
    assert settings.discovery_max_results >= settings.discovery_concurrency
    assert settings.database_url.startswith("sqlite")
