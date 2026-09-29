"""Project configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Repository root:
# src/rmp/config.py -> rmp -> src -> repository root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Load local environment variables.
# Existing environment variables are not overwritten.
load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# Database configuration
# ============================================================


def get_database_config() -> dict[str, str | int]:
    """Return Supabase PostgreSQL connection settings."""

    # Keep this call for compatibility with the Phase 1 implementation.
    load_dotenv()

    config: dict[str, str | int | None] = {
        "host": os.getenv("SUPABASE_DB_HOST"),
        "port": int(os.getenv("SUPABASE_DB_PORT", "5432")),
        "database": os.getenv("SUPABASE_DB_NAME", "postgres"),
        "user": os.getenv("SUPABASE_DB_USER"),
        "password": os.getenv("SUPABASE_DB_PASSWORD"),
    }

    required_fields = [
        "host",
        "database",
        "user",
        "password",
    ]

    missing = [
        field
        for field in required_fields
        if not config[field]
    ]

    if missing:
        missing_names = ", ".join(missing)

        raise ValueError(
            "Missing required database configuration: "
            f"{missing_names}"
        )

    # Required fields have been validated above.
    return {
        "host": str(config["host"]),
        "port": int(config["port"]),
        "database": str(config["database"]),
        "user": str(config["user"]),
        "password": str(config["password"]),
    }


# ============================================================
# Market Rent API configuration
# ============================================================


MARKET_RENT_SANDBOX_BASE_URL = (
    "https://api.business.govt.nz/"
    "sandbox/tenancy-services/market-rent/v2"
)

MARKET_RENT_PRODUCTION_BASE_URL = (
    "https://api.business.govt.nz/"
    "gateway/tenancy-services/market-rent/v2"
)


@dataclass(frozen=True)
class MarketRentSettings:
    """Configuration for the MBIE Market Rent API."""

    environment: str
    base_url: str
    subscription_key: str

    @property
    def is_sandbox(self) -> bool:
        """Return True when using the sandbox environment."""

        return self.environment == "sandbox"


def get_market_rent_settings() -> MarketRentSettings:
    """Load and validate Market Rent API settings.

    Returns
    -------
    MarketRentSettings
        Validated Market Rent API configuration.

    Raises
    ------
    ValueError
        If the API environment is invalid or the required
        subscription key is missing.
    """

    environment = os.getenv(
        "MARKET_RENT_API_ENV",
        "sandbox",
    ).strip().lower()

    if environment not in {
        "sandbox",
        "production",
    }:
        raise ValueError(
            "MARKET_RENT_API_ENV must be either "
            "'sandbox' or 'production'."
        )

    if environment == "sandbox":
        base_url = MARKET_RENT_SANDBOX_BASE_URL

        subscription_key = os.getenv(
            "MARKET_RENT_API_SANDBOX_KEY",
            "",
        ).strip()

        key_variable = (
            "MARKET_RENT_API_SANDBOX_KEY"
        )

    else:
        base_url = MARKET_RENT_PRODUCTION_BASE_URL

        subscription_key = os.getenv(
            "MARKET_RENT_API_PROD_KEY",
            "",
        ).strip()

        key_variable = (
            "MARKET_RENT_API_PROD_KEY"
        )

    if not subscription_key:
        raise ValueError(
            f"{key_variable} is not configured. "
            "Add the API subscription key to "
            "your local .env file."
        )

    return MarketRentSettings(
        environment=environment,
        base_url=base_url.rstrip("/"),
        subscription_key=subscription_key,
    )