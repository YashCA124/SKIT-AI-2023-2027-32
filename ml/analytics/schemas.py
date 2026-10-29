
"""Column normalization and data-contract helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from config import REQUIRED_COLUMNS, OPTIONAL_COLUMNS

COLUMN_ALIASES: Dict[str, List[str]] = {
    "lot_id": [
        "lot_id", "parking_lot_id", "parking_id", "lot",
        "parking_area_id",
    ],
    "timestamp": [
        "timestamp", "hour_timestamp", "bucket_start", "hour",
        "date_hour", "recorded_at", "datetime",
    ],
    "occupancy_count": [
        "occupancy_count", "occupied_count", "occupied_spaces",
        "occupied_slots", "occupancy", "current_occupancy",
    ],
    "capacity": [
        "capacity", "total_capacity", "total_slots",
        "slot_capacity", "parking_capacity",
    ],
    "bookings_count": [
        "bookings_count", "booking_count", "demand_count",
        "reservations_count", "new_bookings",
    ],
    "revenue": [
        "revenue", "hourly_revenue", "revenue_amount", "paid_revenue",
    ],
}


class DataContractError(ValueError):
    """Raised when source data cannot be mapped to the expected contract."""


@dataclass
class ValidationSummary:
    source: str
    rows_read: int
    rows_kept: int
    duplicates_removed: int
    invalid_rows_removed: int
    optional_columns_missing: List[str]
    warnings: List[str]

    def to_dict(self):
        return {
            "source": self.source,
            "rows_read": self.rows_read,
            "rows_kept": self.rows_kept,
            "duplicates_removed": self.duplicates_removed,
            "invalid_rows_removed": self.invalid_rows_removed,
            "optional_columns_missing": self.optional_columns_missing,
            "warnings": self.warnings,
        }


def normalize_column_name(name: str) -> str:
    return (
        str(name).strip().lower().replace(" ", "_")
        .replace("-", "_").replace("/", "_")
    )


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    lookup = {
        normalize_column_name(column): column
        for column in frame.columns
    }
    rename_map = {}

    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            normalized_alias = normalize_column_name(alias)
            if normalized_alias in lookup:
                rename_map[lookup[normalized_alias]] = canonical
                break

    return frame.rename(columns=rename_map)


def missing_required_columns(frame: pd.DataFrame) -> List[str]:
    return [
        column for column in REQUIRED_COLUMNS
        if column not in frame.columns
    ]


def missing_optional_columns(frame: pd.DataFrame) -> List[str]:
    return [
        column for column in OPTIONAL_COLUMNS
        if column not in frame.columns
    ]
