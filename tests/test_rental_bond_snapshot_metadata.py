"""Tests for Rental Bond acquisition snapshot metadata."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from rmp.acquisition.rental_bond_snapshot import (
    RENTAL_BOND_PROVISIONAL,
    RENTAL_BOND_PROVISIONAL_CHECKED,
    RENTAL_BOND_PROVISIONAL_SOURCE,
    acquire_rental_bond_snapshot,
)


class FakeResponse:
    """Minimal successful HTTP response."""

    status_code = 200
    content = b"Period,Location,Median Rent\n2026-07,Auckland,650\n"

    def raise_for_status(self) -> None:
        """Successful fake response does not raise."""


class FakeSession:
    """Minimal requests-like session."""

    def get(
        self,
        url: str,
        *,
        timeout: int,
        headers: dict[str, str],
    ) -> FakeResponse:
        """Return a deterministic fake CSV response."""
        assert url
        assert timeout > 0
        assert "User-Agent" in headers

        return FakeResponse()


def test_snapshot_metadata_records_provisional_provenance(
    tmp_path,
) -> None:
    """Snapshot metadata should preserve official provisional provenance."""
    retrieved_at = datetime(
        2026,
        10,
        6,
        0,
        0,
        tzinfo=UTC,
    )

    snapshot = acquire_rental_bond_snapshot(
        "region",
        raw_root=tmp_path,
        retrieved_at=retrieved_at,
        session=FakeSession(),
    )

    metadata = json.loads(snapshot.metadata_path.read_text(encoding="utf-8"))

    assert metadata["provisional"] is RENTAL_BOND_PROVISIONAL
    assert metadata["provisional_status_source"] == RENTAL_BOND_PROVISIONAL_SOURCE
    assert metadata["provisional_status_checked"] == RENTAL_BOND_PROVISIONAL_CHECKED == "2026-10-06"

    assert metadata["provisional"] is True

    assert metadata["provisional_status_source"] == (
        "https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/"
    )
