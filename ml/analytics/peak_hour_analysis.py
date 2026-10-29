
"""Peak-hour analysis for each parking lot and the complete system."""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from config import (
    HIGH_OCCUPANCY_THRESHOLD,
    MEDIUM_OCCUPANCY_THRESHOLD,
    PEAK_TOP_N_HOURS,
)


def add_occupancy_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    """Add occupancy percentage, hour, weekday, and status features."""
    data = frame.copy()

    data["occupancy_pct"] = (
        data["occupancy_count"]
        / data["capacity"].replace(0, np.nan)
    ).clip(lower=0, upper=1)

    data["occupancy_pct_100"] = (data["occupancy_pct"] * 100).round(2)

    def classify(value):
        if pd.isna(value):
            return "unknown"
        if value >= HIGH_OCCUPANCY_THRESHOLD:
            return "high"
        if value >= MEDIUM_OCCUPANCY_THRESHOLD:
            return "moderate"
        return "low"

    data["occupancy_level"] = data["occupancy_pct"].apply(classify)
    data["hour_of_day"] = data["timestamp"].dt.hour
    data["day_of_week"] = data["timestamp"].dt.dayofweek
    data["day_name"] = data["timestamp"].dt.day_name()
    data["is_weekend"] = data["day_of_week"].isin([5, 6])

    return data


def summarize_peak_hours(
    frame: pd.DataFrame,
    top_n: int = PEAK_TOP_N_HOURS,
) -> pd.DataFrame:
    """Rank clock hours by average occupancy across the dataset."""
    if frame.empty:
        return pd.DataFrame()

    data = add_occupancy_metrics(frame)

    summary = (
        data.groupby("hour_of_day", as_index=False)
        .agg(
            mean_occupancy_pct=("occupancy_pct_100", "mean"),
            median_occupancy_pct=("occupancy_pct_100", "median"),
            max_occupancy_pct=("occupancy_pct_100", "max"),
            mean_occupied_spaces=("occupancy_count", "mean"),
            mean_capacity=("capacity", "mean"),
            observed_lot_hours=("lot_id", "count"),
            high_occupancy_share=(
                "occupancy_level",
                lambda values: (values == "high").mean(),
            ),
        )
    )

    numeric_columns = [
        "mean_occupancy_pct",
        "median_occupancy_pct",
        "max_occupancy_pct",
        "mean_occupied_spaces",
        "mean_capacity",
    ]
    summary[numeric_columns] = summary[numeric_columns].round(2)
    summary["high_occupancy_share"] = (
        summary["high_occupancy_share"] * 100
    ).round(2)

    summary = summary.sort_values(
        ["mean_occupancy_pct", "high_occupancy_share"],
        ascending=[False, False],
    ).reset_index(drop=True)

    summary.insert(0, "rank", np.arange(1, len(summary) + 1))
    summary["is_top_peak_hour"] = summary["rank"] <= top_n

    return summary


def summarize_peak_hours_by_lot(
    frame: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    """Rank clock hours separately for every parking lot."""
    if frame.empty:
        return pd.DataFrame()

    data = add_occupancy_metrics(frame)

    summary = (
        data.groupby(["lot_id", "hour_of_day"], as_index=False)
        .agg(
            mean_occupancy_pct=("occupancy_pct_100", "mean"),
            max_occupancy_pct=("occupancy_pct_100", "max"),
            average_occupied_spaces=("occupancy_count", "mean"),
            average_capacity=("capacity", "mean"),
            observations=("timestamp", "count"),
        )
    )

    numeric_columns = [
        "mean_occupancy_pct",
        "max_occupancy_pct",
        "average_occupied_spaces",
        "average_capacity",
    ]
    summary[numeric_columns] = summary[numeric_columns].round(2)

    summary = summary.sort_values(
        ["lot_id", "mean_occupancy_pct"],
        ascending=[True, False],
    )
    summary["rank_within_lot"] = (
        summary.groupby("lot_id").cumcount() + 1
    )
    summary["is_top_peak_hour"] = summary["rank_within_lot"] <= top_n

    return summary.reset_index(drop=True)


def summarize_peak_days(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare average occupancy across weekdays."""
    if frame.empty:
        return pd.DataFrame()

    data = add_occupancy_metrics(frame)

    result = (
        data.groupby(["day_of_week", "day_name"], as_index=False)
        .agg(
            mean_occupancy_pct=("occupancy_pct_100", "mean"),
            median_occupancy_pct=("occupancy_pct_100", "median"),
            observations=("timestamp", "count"),
            high_occupancy_share=(
                "occupancy_level",
                lambda values: (values == "high").mean(),
            ),
        )
    )

    result["mean_occupancy_pct"] = result["mean_occupancy_pct"].round(2)
    result["median_occupancy_pct"] = result["median_occupancy_pct"].round(2)
    result["high_occupancy_share"] = (
        100 * result["high_occupancy_share"]
    ).round(2)

    return result.sort_values(
        "mean_occupancy_pct", ascending=False
    ).reset_index(drop=True)


def find_high_occupancy_periods(
    frame: pd.DataFrame,
    threshold: float = HIGH_OCCUPANCY_THRESHOLD,
) -> pd.DataFrame:
    """Return lot-hour records at or above a utilization threshold."""
    if frame.empty:
        return pd.DataFrame()

    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1.")

    data = add_occupancy_metrics(frame)
    result = data.loc[data["occupancy_pct"] >= threshold].copy()

    columns = [
        "lot_id",
        "timestamp",
        "occupancy_count",
        "capacity",
        "occupancy_pct_100",
        "occupancy_level",
    ]
    if "bookings_count" in result.columns:
        columns.append("bookings_count")

    return result[columns].sort_values(
        ["occupancy_pct_100", "timestamp"],
        ascending=[False, True],
    ).reset_index(drop=True)


def peak_hour_narrative(
    system_peak_hours: pd.DataFrame,
    peak_days: pd.DataFrame,
) -> Dict[str, object]:
    """Generate short insights suitable for a dashboard."""
    insights: List[str] = []

    if not system_peak_hours.empty:
        top = system_peak_hours.iloc[0]
        hour = int(top["hour_of_day"])

        insights.append(
            f"The busiest average clock hour is {hour:02d}:00, "
            f"with mean occupancy of "
            f"{top['mean_occupancy_pct']:.1f}%."
        )

        high_hours = system_peak_hours.loc[
            system_peak_hours["mean_occupancy_pct"] >= 85
        ]

        if not high_hours.empty:
            labels = ", ".join(
                f"{int(value):02d}:00"
                for value in high_hours["hour_of_day"]
            )
            insights.append(
                f"Hours averaging at least 85% occupancy: {labels}."
            )
        else:
            insights.append(
                "No clock hour averages at least 85% occupancy."
            )

    if not peak_days.empty:
        top_day = peak_days.iloc[0]
        insights.append(
            f"The busiest average weekday is {top_day['day_name']}, "
            f"with mean occupancy of "
            f"{top_day['mean_occupancy_pct']:.1f}%."
        )

    return {
        "insights": insights,
        "interpretation": (
            "These are historical patterns, not a guarantee of future demand."
        ),
    }
