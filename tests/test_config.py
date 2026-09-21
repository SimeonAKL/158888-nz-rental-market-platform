"""Tests for project configuration."""

from rmp.config import get_database_config


def test_database_config_loads_from_environment(monkeypatch):
    """Database settings should load from environment variables."""
    monkeypatch.setenv("SUPABASE_DB_HOST", "localhost")
    monkeypatch.setenv("SUPABASE_DB_PORT", "5432")
    monkeypatch.setenv("SUPABASE_DB_NAME", "postgres")
    monkeypatch.setenv("SUPABASE_DB_USER", "test_user")
    monkeypatch.setenv("SUPABASE_DB_PASSWORD", "test_password")

    config = get_database_config()

    assert config["host"] == "localhost"
    assert config["port"] == 5432
    assert config["database"] == "postgres"
    assert config["user"] == "test_user"
    assert config["password"] == "test_password"
