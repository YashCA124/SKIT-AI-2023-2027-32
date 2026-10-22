
"""Historical occupancy trends and next-hour forecasting."""
from __future__ import annotations

import json
from datetime import timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from config import (
    FEATURE_COLUMNS,
    FORECAST_HORIZON_HOURS,
    MIN_HOURS_FOR_FORECAST,
    MIN_TRAINING_SAMPLES,
    PREVIOUS_WINDOW_HOURS,
    RANDOM_STATE,
    RECENT_WINDOW_HOURS,
    TEST_FRACTION,
)
from schemas import ModelMetrics


def calculate_trend_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize utilization, variability, and observed records per lot."""
    if frame.empty:
        return pd.DataFrame()

    data = frame.copy()
    data["occupancy_pct"] = (
        100 * data["occupancy_count"] / data["capacity"]
    )

    result = (
        data.groupby("lot_id", as_index=False)
        .agg(
            mean_occupancy_pct=("occupancy_pct", "mean"),
            median_occupancy_pct=("occupancy_pct", "median"),
            max_occupancy_pct=("occupancy_pct", "max"),
            min_occupancy_pct=("occupancy_pct", "min"),
            occupancy_std_pct=("occupancy_pct", "std"),
            average_occupied_spaces=("occupancy_count", "mean"),
            average_capacity=("capacity", "mean"),
            observations=("timestamp", "count"),
            first_observation=("timestamp", "min"),
            last_observation=("timestamp", "max"),
        )
    )

    numeric_columns = [
        "mean_occupancy_pct",
        "median_occupancy_pct",
        "max_occupancy_pct",
        "min_occupancy_pct",
        "occupancy_std_pct",
        "average_occupied_spaces",
        "average_capacity",
    ]
    result[numeric_columns] = result[numeric_columns].round(2)

    return result.sort_values(
        "mean_occupancy_pct", ascending=False
    ).reset_index(drop=True)


def calculate_recent_trend(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare each lot's recent 24 hours with its previous 24 hours."""
    if frame.empty:
        return pd.DataFrame()

    rows = []
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)

    for lot_id, group in data.groupby("lot_id"):
        group = group.sort_values("timestamp")
        latest_time = group["timestamp"].max()

        recent_start = latest_time - pd.Timedelta(
            hours=RECENT_WINDOW_HOURS
        )
        previous_start = recent_start - pd.Timedelta(
            hours=PREVIOUS_WINDOW_HOURS
        )

        recent = group[
            (group["timestamp"] > recent_start)
            & (group["timestamp"] <= latest_time)
        ]
        previous = group[
            (group["timestamp"] > previous_start)
            & (group["timestamp"] <= recent_start)
        ]

        recent_pct = (
            100 * recent["occupancy_count"] / recent["capacity"]
        ).mean()
        previous_pct = (
            100 * previous["occupancy_count"] / previous["capacity"]
        ).mean()

        if recent.empty or previous.empty:
            direction = "insufficient_history"
            change = np.nan
        else:
            change = recent_pct - previous_pct
            if change > 2:
                direction = "increasing"
            elif change < -2:
                direction = "decreasing"
            else:
                direction = "stable"

        rows.append({
            "lot_id": lot_id,
            "latest_timestamp": latest_time,
            "recent_mean_occupancy_pct": (
                round(float(recent_pct), 2)
                if pd.notna(recent_pct) else np.nan
            ),
            "previous_mean_occupancy_pct": (
                round(float(previous_pct), 2)
                if pd.notna(previous_pct) else np.nan
            ),
            "change_percentage_points": (
                round(float(change), 2)
                if pd.notna(change) else np.nan
            ),
            "trend_direction": direction,
            "recent_observations": len(recent),
            "previous_observations": len(previous),
        })

    return pd.DataFrame(rows)


def add_time_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Create calendar features from each record's timestamp."""
    data = frame.copy()
    timestamp = pd.to_datetime(data["timestamp"], utc=True)

    data["hour"] = timestamp.dt.hour
    data["day_of_week"] = timestamp.dt.dayofweek
    data["day_of_month"] = timestamp.dt.day
    data["month"] = timestamp.dt.month
    data["is_weekend"] = timestamp.dt.dayofweek.isin([5, 6]).astype(int)

    data["hour_sin"] = np.sin(2 * np.pi * data["hour"] / 24)
    data["hour_cos"] = np.cos(2 * np.pi * data["hour"] / 24)
    data["day_sin"] = np.sin(2 * np.pi * data["day_of_week"] / 7)
    data["day_cos"] = np.cos(2 * np.pi * data["day_of_week"] / 7)

    data["occupancy_pct"] = (
        data["occupancy_count"] / data["capacity"]
    ).clip(0, 1)

    return data


def build_supervised_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Build lag features and a true next-hour occupancy target.

    Rows without a genuine observation exactly one hour later are excluded.
    This prevents the model from treating a multi-hour gap as a one-hour
    prediction target.
    """
    if frame.empty:
        return pd.DataFrame()

    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data = data.sort_values(["lot_id", "timestamp"]).reset_index(drop=True)
    data = add_time_features(data)

    grouped = data.groupby("lot_id", group_keys=False)

    for lag in (1, 2, 3, 24):
        data[f"occupancy_lag_{lag}"] = grouped["occupancy_count"].shift(lag)

    for window in (3, 6, 24):
        data[f"occupancy_rolling_mean_{window}"] = (
            data.groupby("lot_id")["occupancy_count"]
            .transform(
                lambda values: values.shift(1).rolling(
                    window=window, min_periods=window
                ).mean()
            )
        )

    data["target_occupancy"] = grouped["occupancy_count"].shift(-1)
    data["target_timestamp"] = grouped["timestamp"].shift(-1)

    is_next_hour = (
        data["target_timestamp"] - data["timestamp"]
    ).eq(pd.Timedelta(hours=FORECAST_HORIZON_HOURS))

    data = data.loc[is_next_hour].copy()
    data = data.dropna(
        subset=FEATURE_COLUMNS + ["target_occupancy"]
    )

    return data.reset_index(drop=True)


def _metrics(y_true, y_pred, model_name, train_count, test_count):
    """Calculate regression metrics with JSON-safe numeric values."""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else 0.0

    return ModelMetrics(
        model_name=model_name,
        mae=round(float(mae), 4),
        rmse=round(float(rmse), 4),
        r2=round(float(r2), 4),
        training_rows=int(train_count),
        testing_rows=int(test_count),
    )


def train_occupancy_model(frame: pd.DataFrame):
    """Train and evaluate a Random Forest against a dummy baseline.

    The split is chronological: earlier records train the model, and later
    records evaluate it. This is more appropriate for time series than a
    random train/test split.
    """
    supervised = build_supervised_frame(frame)

    if len(supervised) < MIN_TRAINING_SAMPLES:
        raise ValueError(
            f"Need at least {MIN_TRAINING_SAMPLES} supervised rows; "
            f"found {len(supervised)}. Supply more hourly history."
        )

    supervised = supervised.sort_values(
        ["timestamp", "lot_id"]
    ).reset_index(drop=True)

    split_at = int(len(supervised) * (1 - TEST_FRACTION))
    split_at = max(1, min(split_at, len(supervised) - 1))

    train = supervised.iloc[:split_at]
    test = supervised.iloc[split_at:]

    if len(train) < MIN_TRAINING_SAMPLES:
        raise ValueError("Not enough training rows after chronological split.")

    x_train = train[FEATURE_COLUMNS]
    y_train = train["target_occupancy"]
    x_test = test[FEATURE_COLUMNS]
    y_test = test["target_occupancy"]

    baseline = DummyRegressor(strategy="mean")
    baseline.fit(x_train, y_train)
    baseline_predictions = baseline.predict(x_test)
    baseline_metrics = _metrics(
        y_test, baseline_predictions, "dummy_mean_baseline",
        len(train), len(test)
    )

    forest = RandomForestRegressor(
        n_estimators=250,
        max_depth=14,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    forest.fit(x_train, y_train)
    forest_predictions = forest.predict(x_test)
    forest_metrics = _metrics(
        y_test, forest_predictions, "random_forest",
        len(train), len(test)
    )

    # Do not automatically prefer a complex model if it performs worse.
    if forest_metrics.mae <= baseline_metrics.mae:
        selected_model = forest
        selected_metrics = forest_metrics
        selected_name = "random_forest"
    else:
        selected_model = baseline
        selected_metrics = baseline_metrics
        selected_name = "dummy_mean_baseline"

    holdout = test[
        ["lot_id", "timestamp", "target_timestamp", "target_occupancy"]
    ].copy()
    holdout["predicted_occupancy"] = selected_model.predict(x_test)
    holdout["predicted_occupancy"] = holdout[
        "predicted_occupancy"
    ].clip(lower=0)
    holdout["absolute_error"] = (
        holdout["target_occupancy"] - holdout["predicted_occupancy"]
    ).abs()

    metadata = {
        "selected_model": selected_name,
        "selected_metrics": selected_metrics.to_dict(),
        "baseline_metrics": baseline_metrics.to_dict(),
        "random_forest_metrics": forest_metrics.to_dict(),
        "feature_columns": FEATURE_COLUMNS,
        "forecast_horizon_hours": FORECAST_HORIZON_HOURS,
        "training_rows": int(len(train)),
        "testing_rows": int(len(test)),
        "evaluated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "note": (
            "Metrics are a chronological holdout estimate. Validate on "
            "real data before using predictions for operational decisions."
        ),
    }

    return selected_model, metadata, holdout


def forecast_next_hour(
    frame: pd.DataFrame,
    model,
) -> pd.DataFrame:
    """Predict each lot's occupancy for its next hour."""
    if frame.empty:
        return pd.DataFrame()

    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)
    data = data.sort_values(["lot_id", "timestamp"])

    # Build features on the full available history. The target is not needed
    # for inference, but lag and rolling features are.
    featured = add_time_features(data)
    for lag in (1, 2, 3, 24):
        featured[f"occupancy_lag_{lag}"] = (
            featured.groupby("lot_id")["occupancy_count"].shift(lag)
        )

    for window in (3, 6, 24):
        featured[f"occupancy_rolling_mean_{window}"] = (
            featured.groupby("lot_id")["occupancy_count"]
            .transform(
                lambda values: values.shift(1).rolling(
                    window=window, min_periods=window
                ).mean()
            )
        )

    latest = (
        featured.sort_values("timestamp")
        .groupby("lot_id", as_index=False)
        .tail(1)
        .copy()
    )
    latest = latest.dropna(subset=FEATURE_COLUMNS)

    if latest.empty:
        return pd.DataFrame()

    predictions = model.predict(latest[FEATURE_COLUMNS])
    latest["predicted_occupancy"] = predictions.clip(min=0)
    latest["predicted_occupancy"] = np.minimum(
        latest["predicted_occupancy"],
        latest["capacity"],
    ).round(0).astype(int)

    latest["forecast_timestamp"] = (
        latest["timestamp"]
        + pd.Timedelta(hours=FORECAST_HORIZON_HOURS)
    )
    latest["predicted_occupancy_pct"] = (
        100 * latest["predicted_occupancy"] / latest["capacity"]
    ).round(2)

    return latest[
        [
            "lot_id", "timestamp", "forecast_timestamp", "capacity",
            "occupancy_count", "predicted_occupancy",
            "predicted_occupancy_pct",
        ]
    ].reset_index(drop=True)
