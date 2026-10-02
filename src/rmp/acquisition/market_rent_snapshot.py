"""Raw snapshot acquisition for the Market Rent API."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rmp.acquisition.market_rent_api import MarketRentAPIClient
from rmp.config import PROJECT_ROOT

DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "market_rent"


def calculate_sha256(content: bytes) -> str:
    """Return the SHA-256 checksum for byte content."""
    return hashlib.sha256(content).hexdigest()


def _safe_filename_component(value: str) -> str:
    """Convert a string into a safe filename component."""
    cleaned = re.sub(
        r"[^A-Za-z0-9._-]+",
        "-",
        value.strip(),
    )

    return cleaned.strip("-")


def _serialise_json(data: Any) -> bytes:
    """Serialise JSON data consistently as UTF-8 bytes."""
    text = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    )

    return f"{text}\n".encode()


def acquire_market_rent_snapshot(
    *,
    period_ending: str,
    num_months: int,
    area_definition: str,
    include_aggregates: bool = False,
    area_labels: list[str] | None = None,
    area_codes: list[str] | None = None,
    raw_root: Path | None = None,
    client: MarketRentAPIClient | None = None,
    retrieved_at: datetime | None = None,
) -> tuple[Path, Path]:
    """Acquire and save one immutable Market Rent API snapshot.

    Parameters
    ----------
    period_ending:
        Period ending in YYYY-MM format.
    num_months:
        Number of months requested from the API.
    area_definition:
        Geographic area definition such as
        ``regional-council-2019``.
    include_aggregates:
        Whether aggregate records should be requested.
    area_labels:
        Optional list of area labels.
    area_codes:
        Optional list of area codes.
    raw_root:
        Optional alternative raw-data directory.
        Primarily useful for testing.
    client:
        Optional preconfigured Market Rent API client.
    retrieved_at:
        Optional acquisition timestamp.
        Primarily useful for deterministic testing.

    Returns
    -------
    tuple[Path, Path]
        Paths to the raw JSON snapshot and metadata JSON.

    Notes
    -----
    Snapshot files are created using exclusive file creation.
    Existing files are never overwritten.
    """
    acquisition_time = retrieved_at or datetime.now(UTC)

    if acquisition_time.tzinfo is None:
        raise ValueError(
            "retrieved_at must be timezone-aware."
        )

    acquisition_time = acquisition_time.astimezone(UTC)

    root = raw_root or DEFAULT_RAW_ROOT

    snapshot_dir = (
        root
        / acquisition_time.strftime("%Y")
        / acquisition_time.strftime("%m")
        / acquisition_time.strftime("%d")
    )

    snapshot_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = acquisition_time.strftime(
        "%Y%m%dT%H%M%S%fZ"
    )

    safe_area_definition = _safe_filename_component(
        area_definition
    )

    safe_period = _safe_filename_component(
        period_ending
    )

    base_filename = (
        "statistics_"
        f"{safe_area_definition}_"
        f"{safe_period}_"
        f"{timestamp}"
    )

    raw_path = snapshot_dir / f"{base_filename}.json"

    metadata_path = (
        snapshot_dir
        / f"{base_filename}.metadata.json"
    )

    owns_client = client is None

    api_client = client or MarketRentAPIClient()

    try:
        payload = api_client.get_statistics(
            period_ending=period_ending,
            num_months=num_months,
            area_definition=area_definition,
            include_aggregates=include_aggregates,
            area_labels=area_labels,
            area_codes=area_codes,
        )

        raw_bytes = _serialise_json(payload)

        raw_sha256 = calculate_sha256(
            raw_bytes
        )

        request_parameters: dict[str, Any] = {
            "period-ending": period_ending,
            "num-months": num_months,
            "area-definition": area_definition,
            "include-aggregates": (
                "true"
                if include_aggregates
                else "false"
            ),
        }

        if area_labels:
            request_parameters["area-labels"] = (
                area_labels
            )

        if area_codes:
            request_parameters["area-codes"] = (
                area_codes
            )

        metadata = {
            "metadata_schema_version": 1,
            "source": (
                "MBIE / Tenancy Services "
                "Market Rent API"
            ),
            "publisher": (
                "Ministry of Business, "
                "Innovation and Employment"
            ),
            "environment": (
                api_client.settings.environment
            ),
            "endpoint": (
                f"{api_client.settings.base_url}"
                "/statistics"
            ),
            "retrieved_at_utc": (
                acquisition_time.isoformat()
            ),
            "request_parameters": (
                request_parameters
            ),
            "raw_file": raw_path.name,
            "file_size_bytes": len(raw_bytes),
            "sha256": raw_sha256,
        }

        metadata_bytes = _serialise_json(
            metadata
        )

        # Exclusive creation protects immutable raw snapshots.
        with raw_path.open("xb") as raw_file:
            raw_file.write(raw_bytes)

        try:
            with metadata_path.open(
                "xb"
            ) as metadata_file:
                metadata_file.write(
                    metadata_bytes
                )

        except Exception:
            # Avoid leaving an incomplete snapshot pair.
            raw_path.unlink(
                missing_ok=True
            )
            raise

    finally:
        if owns_client:
            api_client.close()

    return raw_path, metadata_path