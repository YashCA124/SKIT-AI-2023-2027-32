
"""Detect unusual occupancy patterns in individual parking lots."""

from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "lot_id",
    "timestamp",
    "occupancy_count",
    "capacity",
]


def validate_anomaly_input(frame: pd.DataFrame) -> None:
    """Validate the columns required for anomaly detection."""
    missing = [
        column for column in REQUIRED_COLUMNS
        if column not in frame.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns for anomaly detection: {missing}"
        )

    timestamps = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    occupancy = pd.to_numeric(frame["occupancy_count"], errors="coerce")
    capacity = pd.to_numeric(frame["capacity"], errors="coerce")
    invalid = (
        timestamps.isna()
        | occupancy.isna()
        | capacity.isna()
        | (capacity <= 0)
        | (occupancy < 0)
        | (occupancy > capacity)
    )
    if invalid.any():
        raise ValueError(
            f"Anomaly input contains {int(invalid.sum())} invalid occupancy rows."
        )


def calculate_occupancy_percentage(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate utilization percentage safely."""
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(
        data["timestamp"], errors="coerce", utc=True
    )
    data["occupancy_count"] = pd.to_numeric(
        data["occupancy_count"], errors="coerce"
    )
    data["capacity"] = pd.to_numeric(data["capacity"], errors="coerce")

    data["occupancy_pct"] = (
        data["occupancy_count"]
        / data["capacity"].replace(0, np.nan)
    ) * 100

    return data


def calculate_rolling_statistics(
    frame: pd.DataFrame,
    window: int = 24,
    minimum_periods: int = 6,
) -> pd.DataFrame:
    """Compare each lot-hour with earlier matching weekday/weekend records.

    Same-hour history avoids treating normal daily demand cycles as
    anomalies; separating weekdays from weekends avoids flagging their
    expected demand differences. The current observation is excluded.
    """
    if window < 3:
        raise ValueError("window must be at least 3.")

    if minimum_periods < 2 or minimum_periods > window:
        raise ValueError(
            "minimum_periods must be between 2 and window."
        )

    validate_anomaly_input(frame)
    data = calculate_occupancy_percentage(frame)
    data = data.sort_values(
        ["lot_id", "timestamp"]
    ).reset_index(drop=True)
    data["hour_of_day"] = data["timestamp"].dt.hour
    data["is_weekend"] = data["timestamp"].dt.dayofweek.isin([5, 6])

    group_columns = ["lot_id", "hour_of_day", "is_weekend"]
    grouped = data.groupby(group_columns)["occupancy_pct"]

    data["rolling_median"] = grouped.transform(
        lambda values: values.shift(1).rolling(
            window=window,
            min_periods=minimum_periods,
        ).median()
    )

    def rolling_mad(values: pd.Series) -> pd.Series:
        shifted = values.shift(1)

        return shifted.rolling(
            window=window,
            min_periods=minimum_periods,
        ).apply(
            lambda sample: np.median(
                np.abs(sample - np.median(sample))
            ),
            raw=True,
        )

    data["rolling_mad"] = (
        data.groupby(group_columns)["occupancy_pct"]
        .transform(rolling_mad)
    )

    return data


def detect_occupancy_anomalies(
    frame: pd.DataFrame,
    window: int = 24,
    threshold: float = 3.5,
    minimum_periods: int = 6,
) -> pd.DataFrame:
    """Flag unusually high or low occupancy observations.

    A robust modified z-score is calculated from the rolling median
    and rolling MAD. A minimum scale prevents small, rounded occupancy
    changes from looking anomalous when historical MAD is zero.
    """
    validate_anomaly_input(frame)

    if threshold <= 0:
        raise ValueError("threshold must be positive.")

    data = calculate_rolling_statistics(
        frame,
        window=window,
        minimum_periods=minimum_periods,
    )

    mad = data["rolling_mad"].fillna(0)
    difference = data["occupancy_pct"] - data["rolling_median"]

    denominator = 1.4826 * mad
    # Whole-space rounding can otherwise make small changes appear extreme.
    denominator = denominator.clip(lower=3.5)

    data["robust_z_score"] = difference / denominator

    enough_history = data["rolling_median"].notna()
    data["is_anomaly"] = (
        enough_history
        & (data["robust_z_score"].abs() >= threshold)
    )

    data["anomaly_type"] = "normal"
    data.loc[
        data["is_anomaly"] & (difference > 0),
        "anomaly_type",
    ] = "unexpected_spike"

    data.loc[
        data["is_anomaly"] & (difference < 0),
        "anomaly_type",
    ] = "unexpected_drop"

    data["anomaly_severity"] = "none"

    absolute_score = data["robust_z_score"].abs()

    data.loc[
        data["is_anomaly"] & (absolute_score < 5),
        "anomaly_severity",
    ] = "medium"

    data.loc[
        data["is_anomaly"] & (absolute_score >= 5),
        "anomaly_severity",
    ] = "high"

    return data


def get_anomaly_records(
    anomaly_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Return only detected anomaly records."""
    if anomaly_frame.empty:
        return anomaly_frame.copy()

    result = anomaly_frame.loc[
        anomaly_frame["is_anomaly"]
    ].copy()

    columns = [
        "lot_id",
        "timestamp",
        "occupancy_count",
        "capacity",
        "occupancy_pct",
        "rolling_median",
        "rolling_mad",
        "robust_z_score",
        "anomaly_type",
        "anomaly_severity",
    ]

    return result[columns].sort_values(
        "timestamp",
        ascending=False,
    ).reset_index(drop=True)


def summarize_anomalies(
    anomaly_frame: pd.DataFrame,
) -> pd.DataFrame:
    """Create per-lot anomaly counts and severity summaries."""
    if anomaly_frame.empty:
        return pd.DataFrame()

    anomalies = anomaly_frame.loc[
        anomaly_frame["is_anomaly"]
    ].copy()

    if anomalies.empty:
        return pd.DataFrame(
            columns=[
                "lot_id",
                "total_anomalies",
                "high_severity",
                "medium_severity",
                "unexpected_spikes",
                "unexpected_drops",
            ]
        )

    summary = (
        anomalies.groupby("lot_id")
        .agg(
            total_anomalies=("is_anomaly", "sum"),
            high_severity=(
                "anomaly_severity",
                lambda values: (values == "high").sum(),
            ),
            medium_severity=(
                "anomaly_severity",
                lambda values: (values == "medium").sum(),
            ),
            unexpected_spikes=(
                "anomaly_type",
                lambda values: (values == "unexpected_spike").sum(),
            ),
            unexpected_drops=(
                "anomaly_type",
                lambda values: (values == "unexpected_drop").sum(),
            ),
        )
        .reset_index()
    )

    return summary.sort_values(
        "total_anomalies",
        ascending=False,
    ).reset_index(drop=True)


def generate_anomaly_insights(
    anomaly_summary: pd.DataFrame,
) -> list[str]:
    """Translate anomaly statistics into readable observations."""
    insights = []

    if anomaly_summary.empty:
        return ["No unusual occupancy observations were detected."]

    total = int(anomaly_summary["total_anomalies"].sum())
    insights.append(
        f"The analysis detected {total} unusual occupancy observations."
    )

    highest = anomaly_summary.iloc[0]
    insights.append(
        f"{highest['lot_id']} has the highest anomaly count "
        f"({int(highest['total_anomalies'])})."
    )

    high_total = int(anomaly_summary["high_severity"].sum())

    if high_total:
        insights.append(
            f"{high_total} observations were classified as high severity."
        )

    return insights


def run_anomaly_analysis(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Execute the complete anomaly analysis."""
    detected = detect_occupancy_anomalies(frame)
    records = get_anomaly_records(detected)
    summary = summarize_anomalies(detected)
    insights = generate_anomaly_insights(summary)

    return records, summary, insights
