"""Tests for the Market Rent API client."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from rmp.acquisition.market_rent_api import MarketRentAPIClient
from rmp.config import MarketRentSettings


@pytest.fixture
def settings() -> MarketRentSettings:
    """Return test Market Rent API settings."""
    return MarketRentSettings(
        environment="sandbox",
        base_url="https://example.test/v2",
        subscription_key="test-key",
    )


def test_client_sets_required_headers(
    settings: MarketRentSettings,
) -> None:
    """Client should configure required MBIE request headers."""
    client = MarketRentAPIClient(settings=settings)

    assert client.session.headers["Ocp-Apim-Subscription-Key"] == "test-key"

    assert client.session.headers["Accept"] == "application/json"

    client.close()


def test_get_area_definitions(
    settings: MarketRentSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Area definitions endpoint should return parsed JSON."""
    client = MarketRentAPIClient(settings=settings)

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            "code": "example",
            "label": "Example",
        }
    ]

    mock_get = Mock(
        return_value=mock_response,
    )

    monkeypatch.setattr(
        client.session,
        "get",
        mock_get,
    )

    result = client.get_area_definitions()

    assert result == [
        {
            "code": "example",
            "label": "Example",
        }
    ]

    mock_get.assert_called_once_with(
        "https://example.test/v2/area-definitions",
        params=None,
        timeout=120,
    )

    client.close()


def test_statistics_rejects_invalid_num_months(
    settings: MarketRentSettings,
) -> None:
    """Statistics requests must use 1 to 24 months."""
    client = MarketRentAPIClient(settings=settings)

    with pytest.raises(
        ValueError,
        match="between 1 and 24",
    ):
        client.get_statistics(
            period_ending="2026-07",
            num_months=25,
            area_definition="regional-council-2019",
        )

    client.close()


def test_statistics_builds_parameters(
    settings: MarketRentSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Statistics requests should build expected parameters."""
    client = MarketRentAPIClient(settings=settings)

    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "data": [],
    }

    mock_get = Mock(
        return_value=mock_response,
    )

    monkeypatch.setattr(
        client.session,
        "get",
        mock_get,
    )

    result = client.get_statistics(
        period_ending="2026-07",
        num_months=1,
        area_definition="regional-council-2019",
        include_aggregates=True,
    )

    assert result == {
        "data": [],
    }

    mock_get.assert_called_once_with(
        "https://example.test/v2/statistics",
        params={
            "period-ending": "2026-07",
            "num-months": 1,
            "area-definition": "regional-council-2019",
            "include-aggregates": "true",
        },
        timeout=120,
    )

    client.close()
