"""Client for the MBIE / Tenancy Services Market Rent API."""

from __future__ import annotations

from typing import Any, Self

import requests

from rmp.config import MarketRentSettings, get_market_rent_settings

DEFAULT_TIMEOUT_SECONDS = 120


class MarketRentAPIError(RuntimeError):
    """Raised when a Market Rent API request fails."""


class MarketRentAPIClient:
    """HTTP client for the Tenancy Services Market Rent API."""

    def __init__(
        self,
        settings: MarketRentSettings | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialise the Market Rent API client."""
        self.settings = settings or get_market_rent_settings()
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Ocp-Apim-Subscription-Key": self.settings.subscription_key,
                "Accept": "application/json",
                "User-Agent": "158888-NZ-Rental-Market-Platform/1.0",
            }
        )

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Send a GET request to the Market Rent API."""
        url = f"{self.settings.base_url}/{endpoint.lstrip('/')}"

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.Timeout as exc:
            raise MarketRentAPIError(
                "Market Rent API request timed out after "
                f"{self.timeout} seconds."
            ) from exc

        except requests.HTTPError as exc:
            status_code = (
                exc.response.status_code
                if exc.response is not None
                else "unknown"
            )

            raise MarketRentAPIError(
                f"Market Rent API returned HTTP {status_code}."
            ) from exc

        except requests.RequestException as exc:
            raise MarketRentAPIError(
                "Unable to connect to the Market Rent API."
            ) from exc

        try:
            return response.json()

        except requests.JSONDecodeError as exc:
            raise MarketRentAPIError(
                "Market Rent API returned a response "
                "that was not valid JSON."
            ) from exc

    def get_area_definitions(self) -> Any:
        """Return geographic area definitions available from the API."""
        return self._get("area-definitions")

    def get_area_definition(
        self,
        area_definition: str,
    ) -> Any:
        """Return details for one geographic area definition."""
        if not area_definition.strip():
            raise ValueError(
                "area_definition must not be empty."
            )

        return self._get(
            f"area-definitions/{area_definition}"
        )

    def get_statistics(
        self,
        period_ending: str,
        num_months: int,
        area_definition: str,
        *,
        include_aggregates: bool = False,
        area_labels: list[str] | None = None,
        area_codes: list[str] | None = None,
    ) -> Any:
        """Retrieve Market Rent statistics."""
        if not 1 <= num_months <= 24:
            raise ValueError(
                "num_months must be between 1 and 24."
            )

        if not period_ending.strip():
            raise ValueError(
                "period_ending must not be empty."
            )

        if not area_definition.strip():
            raise ValueError(
                "area_definition must not be empty."
            )

        params: dict[str, Any] = {
            "period-ending": period_ending,
            "num-months": num_months,
            "area-definition": area_definition,
            "include-aggregates": (
                "true" if include_aggregates else "false"
            ),
        }

        if area_labels:
            params["area-labels"] = ",".join(area_labels)

        if area_codes:
            params["area-codes"] = ",".join(area_codes)

        return self._get(
            "statistics",
            params=params,
        )

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> Self:
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        """Exit the context manager."""
        self.close()
