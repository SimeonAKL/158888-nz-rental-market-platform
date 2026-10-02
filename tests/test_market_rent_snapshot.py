"""Tests for Market Rent raw snapshot acquisition."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from rmp.acquisition.market_rent_api import (
    MarketRentAPIClient,
)
from rmp.acquisition.market_rent_snapshot import (
    acquire_market_rent_snapshot,
)
from rmp.config import MarketRentSettings


def make_test_client() -> Mock:
    """Create a mocked Market Rent API client."""
    client = Mock(
        spec=MarketRentAPIClient
    )

    client.settings = MarketRentSettings(
        environment="sandbox",
        base_url="https://example.test/v2",
        subscription_key="secret-test-key",
    )

    client.get_statistics.return_value = {
        "tableName": "statistics",
        "items": [
            {
                "area": "Example Region",
                "med": 600,
                "nLodged": 100,
            }
        ],
    }

    return client


def test_snapshot_creates_raw_and_metadata_files(
    tmp_path: Path,
) -> None:
    """Acquisition should create raw JSON and metadata."""
    client = make_test_client()

    retrieved_at = datetime(
        2026,
        10,
        1,
        1,
        30,
        0,
        tzinfo=UTC,
    )

    raw_path, metadata_path = (
        acquire_market_rent_snapshot(
            period_ending="2026-07",
            num_months=1,
            area_definition=(
                "regional-council-2019"
            ),
            raw_root=tmp_path,
            client=client,
            retrieved_at=retrieved_at,
        )
    )

    assert raw_path.exists()
    assert metadata_path.exists()

    assert (
        raw_path.parent
        == tmp_path / "2026" / "10" / "01"
    )

    raw_data = json.loads(
        raw_path.read_text(
            encoding="utf-8"
        )
    )

    assert raw_data["tableName"] == "statistics"

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata["environment"]
        == "sandbox"
    )

    assert (
        metadata["request_parameters"][
            "period-ending"
        ]
        == "2026-07"
    )

    assert (
        metadata["request_parameters"][
            "num-months"
        ]
        == 1
    )

    assert (
        metadata["request_parameters"][
            "area-definition"
        ]
        == "regional-council-2019"
    )

    assert metadata["raw_file"] == raw_path.name

    # API subscription keys must never
    # appear in metadata.
    metadata_text = metadata_path.read_text(
        encoding="utf-8"
    )

    assert (
        "secret-test-key"
        not in metadata_text
    )


def test_snapshot_checksum_matches_raw_file(
    tmp_path: Path,
) -> None:
    """Metadata checksum should match the raw snapshot."""
    client = make_test_client()

    retrieved_at = datetime(
        2026,
        10,
        1,
        2,
        0,
        0,
        tzinfo=UTC,
    )

    raw_path, metadata_path = (
        acquire_market_rent_snapshot(
            period_ending="2026-07",
            num_months=1,
            area_definition=(
                "regional-council-2019"
            ),
            raw_root=tmp_path,
            client=client,
            retrieved_at=retrieved_at,
        )
    )

    raw_bytes = raw_path.read_bytes()

    expected_sha256 = hashlib.sha256(
        raw_bytes
    ).hexdigest()

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata["sha256"]
        == expected_sha256
    )

    assert (
        metadata["file_size_bytes"]
        == len(raw_bytes)
    )