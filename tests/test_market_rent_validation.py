"""Tests for Market Rent snapshot validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rmp.validation.market_rent import (
    MarketRentValidationError,
    validate_market_rent_file,
    validate_market_rent_payload,
)


def make_valid_payload() -> dict:
    """Return a minimal valid Market Rent payload."""
    return {
        "areaDefinition": "regional-council-2019",
        "periodCovered": {
            "start": "2026-07",
            "end": "2026-07",
        },
        "items": [
            {
                "area": "Auckland Region",
                "dwell": "Apartment",
                "nBedrms": "1",
                "nLodged": 609,
                "nClosed": 342,
                "nCurr": 9693,
                "mean": 502,
                "lq": 450,
                "med": 490,
                "uq": 539,
                "sd": 209,
                "brr": 3.84,
                "lmean": 6.1854,
                "lsd": 0.2386,
                "slq": 413,
                "suq": 570,
            }
        ],
    }


def test_valid_payload_passes() -> None:
    """A valid Market Rent payload should pass validation."""
    payload = make_valid_payload()

    validate_market_rent_payload(
        payload
    )


def test_missing_required_item_field_fails() -> None:
    """Missing required statistics fields should fail."""
    payload = make_valid_payload()

    del payload["items"][0]["med"]

    with pytest.raises(
        MarketRentValidationError,
        match="missing fields",
    ):
        validate_market_rent_payload(
            payload
        )


def test_non_numeric_field_fails() -> None:
    """Numeric statistics fields must contain numeric values."""
    payload = make_valid_payload()

    payload["items"][0]["nLodged"] = "invalid"

    with pytest.raises(
        MarketRentValidationError,
        match="must be numeric",
    ):
        validate_market_rent_payload(
            payload
        )


def test_empty_items_fails() -> None:
    """An empty Market Rent dataset should fail validation."""
    payload = make_valid_payload()

    payload["items"] = []

    with pytest.raises(
        MarketRentValidationError,
        match="must not be empty",
    ):
        validate_market_rent_payload(
            payload
        )


def test_validate_file_returns_payload(
    tmp_path: Path,
) -> None:
    """A valid JSON file should be loaded and returned."""
    payload = make_valid_payload()

    path = tmp_path / "market_rent.json"

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    result = validate_market_rent_file(
        path
    )

    assert (
        result["areaDefinition"]
        == "regional-council-2019"
    )

    assert len(result["items"]) == 1