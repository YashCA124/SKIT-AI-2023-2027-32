
"""Column normalization and data-contract helpers."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List

import pandas as pd

REQUIRED_COLUMNS = [
    "lot_id",
    "timestamp",
    "occupancy_count",
    "capacity",
]
OPTIONAL_COLUMNS = ["bookings_count", "revenue"]

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

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "rows_read": self.rows_read,
            "rows_kept": self.rows_kept,
            "duplicates_removed": self.duplicates_removed,
            "invalid_rows_removed": self.invalid_rows_removed,
            "optional_columns_missing": self.optional_columns_missing,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class ModelMetrics:
    model_name: str
    mae: float
    rmse: float
    r2: float
    training_rows: int
    testing_rows: int

    def to_dict(self) -> dict:
        return asdict(self)


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


def validate_occupancy_data(
    frame: pd.DataFrame,
    source: str = "dataframe",
) -> tuple[pd.DataFrame, ValidationSummary]:
    """Normalize and validate hourly occupancy records."""
    data = normalize_columns(frame)
    rows_read = len(data)
    missing = missing_required_columns(data)
    if missing:
        raise DataContractError(
            f"Missing required occupancy columns: {missing}"
        )

    data = data.copy()
    data["timestamp"] = pd.to_datetime(
        data["timestamp"], errors="coerce", utc=True
    )
    for column in ("occupancy_count", "capacity"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    invalid = (
        data["lot_id"].isna()
        | data["lot_id"].astype(str).str.strip().eq("")
        | data["timestamp"].isna()
        | data["occupancy_count"].isna()
        | data["capacity"].isna()
        | (data["capacity"] <= 0)
        | (data["occupancy_count"] < 0)
        | (data["occupancy_count"] > data["capacity"])
        | (data["occupancy_count"] % 1 != 0)
        | (data["capacity"] % 1 != 0)
    )
    invalid_rows_removed = int(invalid.sum())
    data = data.loc[~invalid].copy()

    exact_duplicates = int(data.duplicated().sum())
    data = data.drop_duplicates()
    duplicate_keys = data.duplicated(
        subset=["lot_id", "timestamp"], keep=False
    )
    if duplicate_keys.any():
        raise DataContractError(
            "Conflicting occupancy records share the same lot_id and timestamp."
        )

    data = data.sort_values(
        ["lot_id", "timestamp"]
    ).reset_index(drop=True)
    if data.empty:
        raise DataContractError("No valid occupancy records remain.")

    warnings = []
    if invalid_rows_removed:
        warnings.append(
            f"Removed {invalid_rows_removed} invalid occupancy rows."
        )
    if exact_duplicates:
        warnings.append(
            f"Removed {exact_duplicates} exact duplicate occupancy rows."
        )

    summary = ValidationSummary(
        source=source,
        rows_read=rows_read,
        rows_kept=len(data),
        duplicates_removed=exact_duplicates,
        invalid_rows_removed=invalid_rows_removed,
        optional_columns_missing=missing_optional_columns(data),
        warnings=warnings,
    )
    return data, summary
