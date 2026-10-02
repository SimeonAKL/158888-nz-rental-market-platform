"""Schema validation for Market Rent API snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL_FIELDS = {
    "areaDefinition",
    "items",
    "periodCovered",
}


REQUIRED_ITEM_FIELDS = {
    "area",
    "dwell",
    "nBedrms",
    "nLodged",
    "nClosed",
    "nCurr",
    "mean",
    "lq",
    "med",
    "uq",
    "sd",
    "brr",
    "lmean",
    "lsd",
    "slq",
    "suq",
}


NUMERIC_FIELDS = {
    "nLodged",
    "nClosed",
    "nCurr",
    "mean",
    "lq",
    "med",
    "uq",
    "sd",
    "brr",
    "lmean",
    "lsd",
    "slq",
    "suq",
}


class MarketRentValidationError(ValueError):
    """Raised when a Market Rent snapshot fails validation."""


def validate_market_rent_payload(
    payload: Any,
) -> None:
    """Validate a Market Rent API payload.

    Parameters
    ----------
    payload:
        Parsed JSON object returned by the Market Rent API.

    Raises
    ------
    MarketRentValidationError
        If the payload does not match the expected schema.
    """
    if not isinstance(payload, dict):
        raise MarketRentValidationError(
            "Market Rent payload must be a JSON object."
        )

    missing_top_level = (
        REQUIRED_TOP_LEVEL_FIELDS
        - payload.keys()
    )

    if missing_top_level:
        missing = ", ".join(
            sorted(missing_top_level)
        )

        raise MarketRentValidationError(
            "Market Rent payload is missing "
            f"top-level fields: {missing}"
        )

    items = payload["items"]

    if not isinstance(items, list):
        raise MarketRentValidationError(
            "'items' must be a list."
        )

    if not items:
        raise MarketRentValidationError(
            "'items' must not be empty."
        )

    for index, item in enumerate(items):
        _validate_item(
            item=item,
            index=index,
        )


def _validate_item(
    *,
    item: Any,
    index: int,
) -> None:
    """Validate one Market Rent statistics record."""
    if not isinstance(item, dict):
        raise MarketRentValidationError(
            f"Item {index} must be a JSON object."
        )

    missing_fields = (
        REQUIRED_ITEM_FIELDS
        - item.keys()
    )

    if missing_fields:
        missing = ", ".join(
            sorted(missing_fields)
        )

        raise MarketRentValidationError(
            f"Item {index} is missing fields: "
            f"{missing}"
        )

    for field in (
        "area",
        "dwell",
        "nBedrms",
    ):
        value = item[field]

        if not isinstance(value, str):
            raise MarketRentValidationError(
                f"Item {index} field "
                f"'{field}' must be a string."
            )

        if not value.strip():
            raise MarketRentValidationError(
                f"Item {index} field "
                f"'{field}' must not be empty."
            )

    for field in NUMERIC_FIELDS:
        value = item[field]

        if value is None:
            continue

        if isinstance(value, bool):
            raise MarketRentValidationError(
                f"Item {index} field "
                f"'{field}' must be numeric."
            )

        if not isinstance(
            value,
            (int, float),
        ):
            raise MarketRentValidationError(
                f"Item {index} field "
                f"'{field}' must be numeric."
            )


def validate_market_rent_file(
    path: Path,
) -> dict[str, Any]:
    """Load and validate one Market Rent raw JSON snapshot.

    Parameters
    ----------
    path:
        Path to a raw Market Rent JSON snapshot.

    Returns
    -------
    dict[str, Any]
        Validated parsed JSON payload.

    Raises
    ------
    MarketRentValidationError
        If the file cannot be parsed or fails schema validation.
    """
    if not path.exists():
        raise MarketRentValidationError(
            f"Market Rent file does not exist: {path}"
        )

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as exc:
        raise MarketRentValidationError(
            f"Market Rent file is not valid JSON: {path}"
        ) from exc

    validate_market_rent_payload(
        payload
    )

    return payload