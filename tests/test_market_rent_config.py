"""Tests for Market Rent API configuration."""

from __future__ import annotations

import pytest

from rmp.config import (
    MARKET_RENT_PRODUCTION_BASE_URL,
    MARKET_RENT_SANDBOX_BASE_URL,
    get_market_rent_settings,
)


def test_sandbox_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sandbox environment should use sandbox URL and key."""
    monkeypatch.setenv(
        "MARKET_RENT_API_ENV",
        "sandbox",
    )
    monkeypatch.setenv(
        "MARKET_RENT_API_SANDBOX_KEY",
        "test-sandbox-key",
    )

    settings = get_market_rent_settings()

    assert settings.environment == "sandbox"
    assert settings.base_url == MARKET_RENT_SANDBOX_BASE_URL
    assert settings.subscription_key == "test-sandbox-key"
    assert settings.is_sandbox is True


def test_production_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production environment should use production URL and key."""
    monkeypatch.setenv(
        "MARKET_RENT_API_ENV",
        "production",
    )
    monkeypatch.setenv(
        "MARKET_RENT_API_PROD_KEY",
        "test-production-key",
    )

    settings = get_market_rent_settings()

    assert settings.environment == "production"
    assert settings.base_url == MARKET_RENT_PRODUCTION_BASE_URL
    assert settings.subscription_key == "test-production-key"
    assert settings.is_sandbox is False


def test_invalid_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Invalid Market Rent API environment should be rejected."""
    monkeypatch.setenv(
        "MARKET_RENT_API_ENV",
        "invalid",
    )

    with pytest.raises(
        ValueError,
        match="sandbox.*production",
    ):
        get_market_rent_settings()


def test_missing_sandbox_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing sandbox subscription key should raise an error."""
    monkeypatch.setenv(
        "MARKET_RENT_API_ENV",
        "sandbox",
    )
    monkeypatch.delenv(
        "MARKET_RENT_API_SANDBOX_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="MARKET_RENT_API_SANDBOX_KEY",
    ):
        get_market_rent_settings()
