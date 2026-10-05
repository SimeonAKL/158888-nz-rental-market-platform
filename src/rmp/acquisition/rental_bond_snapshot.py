"""Acquire and snapshot official Tenancy Services Rental Bond CSV files."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "rental_bond"

DEFAULT_TIMEOUT_SECONDS = 120

REGION_URL = (
    "https://www.tenancy.govt.nz/assets/Uploads/"
    "Tenancy/Rental-bond-data/"
    "detailed-monthly-region-tenancy-september.csv"
)

TLA_URL = (
    "https://www.tenancy.govt.nz/assets/Uploads/"
    "Tenancy/Rental-bond-data/"
    "detailed-monthly-tla-tenancy-september.csv"
)

RENTAL_BOND_PROVISIONAL = True

RENTAL_BOND_PROVISIONAL_SOURCE = (
    "https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/"
)

RENTAL_BOND_PROVISIONAL_CHECKED = "2026-10-06"

RentalBondDataset = Literal[
    "region",
    "territorial_authority",
]


class RentalBondAcquisitionError(RuntimeError):
    """Raised when Rental Bond data cannot be acquired."""


@dataclass(frozen=True)
class RentalBondSnapshot:
    """Paths and metadata for one Rental Bond snapshot."""

    dataset: RentalBondDataset
    raw_path: Path
    metadata_path: Path
    sha256: str
    file_size_bytes: int
    retrieved_at_utc: datetime


def calculate_sha256(content: bytes) -> str:
    """Calculate SHA-256 for downloaded content."""
    return hashlib.sha256(content).hexdigest()


def get_dataset_url(
    dataset: RentalBondDataset,
) -> str:
    """Return the official source URL for a Rental Bond dataset."""
    if dataset == "region":
        return REGION_URL

    if dataset == "territorial_authority":
        return TLA_URL

    raise ValueError(f"Unsupported Rental Bond dataset: {dataset}")


def acquire_rental_bond_snapshot(
    dataset: RentalBondDataset,
    *,
    raw_root: Path = DEFAULT_RAW_ROOT,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    retrieved_at: datetime | None = None,
    session: requests.Session | None = None,
) -> RentalBondSnapshot:
    """Download and store one immutable Rental Bond CSV snapshot."""
    source_url = get_dataset_url(dataset)

    retrieval_time = retrieved_at if retrieved_at is not None else datetime.now(UTC)

    if retrieval_time.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware.")

    owns_session = session is None

    http_session = session if session is not None else requests.Session()

    try:
        response = http_session.get(
            source_url,
            timeout=timeout,
            headers={
                "User-Agent": ("158888-nz-rental-market-platform/1.0"),
                "Accept": "text/csv,*/*",
            },
        )

        try:
            response.raise_for_status()

        except requests.HTTPError as exc:
            raise RentalBondAcquisitionError(
                f"Rental Bond download failed with HTTP {response.status_code}."
            ) from exc

        content = response.content

        if not content:
            raise RentalBondAcquisitionError("Rental Bond download returned an empty file.")

    except requests.RequestException as exc:
        raise RentalBondAcquisitionError(f"Rental Bond download failed: {exc}") from exc

    finally:
        if owns_session:
            http_session.close()

    checksum = calculate_sha256(content)

    timestamp = retrieval_time.strftime("%Y%m%dT%H%M%S%fZ")

    day_directory = (
        raw_root
        / retrieval_time.strftime("%Y")
        / retrieval_time.strftime("%m")
        / retrieval_time.strftime("%d")
    )

    day_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename = f"rental_bond_{dataset}_{timestamp}.csv"

    raw_path = day_directory / filename

    metadata_path = raw_path.with_name(f"{raw_path.stem}.metadata.json")

    metadata = {
        "metadata_schema_version": 1,
        "source": ("MBIE / Tenancy Services Rental Bond Data"),
        "publisher": ("Ministry of Business, Innovation and Employment"),
        "dataset": dataset,
        "source_url": source_url,
        "retrieved_at_utc": (retrieval_time.isoformat()),
        "raw_file": raw_path.name,
        "file_size_bytes": len(content),
        "sha256": checksum,
        "provisional": RENTAL_BOND_PROVISIONAL,
        "provisional_status_source": RENTAL_BOND_PROVISIONAL_SOURCE,
        "provisional_status_checked": RENTAL_BOND_PROVISIONAL_CHECKED,
        "notes": (
            "Tenancy Services states that migration to the new bond "
            "management system is continuing. Rental Bond data remains "
            "provisional, may be incomplete or revised, and recent data "
            "may not be directly comparable with earlier periods."
        ),
    }

    try:
        with raw_path.open("xb") as file_handle:
            file_handle.write(content)

        with metadata_path.open(
            "x",
            encoding="utf-8",
        ) as file_handle:
            json.dump(
                metadata,
                file_handle,
                indent=2,
                sort_keys=True,
            )

            file_handle.write("\n")

    except Exception:
        raw_path.unlink(missing_ok=True)

        metadata_path.unlink(missing_ok=True)

        raise

    return RentalBondSnapshot(
        dataset=dataset,
        raw_path=raw_path,
        metadata_path=metadata_path,
        sha256=checksum,
        file_size_bytes=len(content),
        retrieved_at_utc=retrieval_time,
    )
