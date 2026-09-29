"""Smoke test for the MBIE Market Rent API.

This script performs a real request against the configured API
environment and prints basic response information.

It intentionally does not save data yet.
"""

from __future__ import annotations

import json
import sys

from rmp.acquisition.market_rent_api import (
    MarketRentAPIClient,
    MarketRentAPIError,
)
from rmp.config import get_market_rent_settings


def main() -> int:
    """Run the Market Rent API connectivity test."""

    print("=" * 60)
    print("Market Rent API connectivity test")
    print("=" * 60)

    try:
        settings = get_market_rent_settings()

        print(f"Environment : {settings.environment}")
        print(f"Base URL    : {settings.base_url}")
        print("API key     : configured")
        print()

        with MarketRentAPIClient(
            settings=settings
        ) as client:
            print(
                "Requesting GET /area-definitions ..."
            )

            data = client.get_area_definitions()

        print()
        print("Connection successful.")
        print()
        print("Response type:")
        print(type(data).__name__)

        print()
        print("Response preview:")
        print(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            )[:4000]
        )

        print()
        print("=" * 60)
        print("Market Rent API smoke test PASSED")
        print("=" * 60)

        return 0

    except (
        ValueError,
        MarketRentAPIError,
    ) as exc:
        print()
        print("ERROR:")
        print(exc)

        print()
        print("=" * 60)
        print("Market Rent API smoke test FAILED")
        print("=" * 60)

        return 1


if __name__ == "__main__":
    sys.exit(main())