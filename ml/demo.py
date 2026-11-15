"""Generate synthetic parking data and run the complete ML demo pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from analytics.analytics import generate_analytics
from analytics.occupancy_trends import (
    calculate_recent_trend,
    calculate_trend_summary,
    forecast_next_hour,
    train_occupancy_model,
)
from analytics.occupany_anomaly import run_anomaly_analysis
from analytics.peak_hour_analysis import (
    find_high_occupancy_periods,
    peak_hour_narrative,
    summarize_peak_days,
    summarize_peak_hours,
    summarize_peak_hours_by_lot,
)
from analytics.schemas import validate_occupancy_data
from etl.aggregate import aggregate_booking_data
from etl.extract import save_raw_data
from etl.transform import transform_bookings
from validation.eda_monitor import generate_eda_summary
from validation.quality_check import run_quality_checks
from validation.validation_report import save_validation_report
from validation.schema_validation import validate_schema
from validation.timestamp_validation import validate_timestamps


ML_DIRECTORY = Path(__file__).resolve().parent
DEMO_DATA_DIRECTORY = ML_DIRECTORY / "data" / "demo"
DEMO_OUTPUT_DIRECTORY = ML_DIRECTORY / "outputs" / "demo"
DEMO_START = pd.Timestamp("2025-01-06T00:00:00Z")
DEMO_DAYS = 28


def generate_synthetic_data(
    directory: Path = DEMO_DATA_DIRECTORY,
) -> tuple[Path, Path]:
    """Write deterministic booking and hourly occupancy source datasets."""
    directory.mkdir(parents=True, exist_ok=True)
    random = np.random.default_rng(42)
    lots = {
        "LOT-001": {"capacity": 120, "hourly_rate": 45, "factor": 0.92},
        "LOT-002": {"capacity": 80, "hourly_rate": 35, "factor": 1.00},
        "LOT-003": {"capacity": 60, "hourly_rate": 30, "factor": 1.08},
    }

    occupancy_rows = []
    for lot_id, details in lots.items():
        for hour_offset in range(DEMO_DAYS * 24):
            timestamp = DEMO_START + pd.Timedelta(hours=hour_offset)
            hour = timestamp.hour
            if hour < 6:
                demand = 0.10
            elif hour < 10:
                demand = 0.42
            elif hour < 16:
                demand = 0.57
            elif hour < 20:
                demand = 0.84
            elif hour < 23:
                demand = 0.48
            else:
                demand = 0.24

            if timestamp.dayofweek >= 5:
                demand -= 0.08

            utilization = np.clip(
                demand * details["factor"] + random.normal(0, 0.025),
                0.03,
                0.96,
            )
            occupancy = int(round(details["capacity"] * utilization))
            occupancy_rows.append({
                "lot_id": lot_id,
                "timestamp": timestamp.isoformat(),
                "occupancy_count": occupancy,
                "capacity": details["capacity"],
                "bookings_count": int(random.poisson(max(1, occupancy / 18))),
                "revenue": round(
                    max(0, occupancy - 8) * details["hourly_rate"] * 0.08,
                    2,
                ),
            })

    occupancy_frame = pd.DataFrame(occupancy_rows)
    spike_time = DEMO_START + pd.Timedelta(days=17, hours=14)
    drop_time = DEMO_START + pd.Timedelta(days=24, hours=14)
    occupancy_frame.loc[
        (occupancy_frame["lot_id"] == "LOT-003")
        & (occupancy_frame["timestamp"] == spike_time.isoformat()),
        "occupancy_count",
    ] = lots["LOT-003"]["capacity"]
    occupancy_frame.loc[
        (occupancy_frame["lot_id"] == "LOT-001")
        & (occupancy_frame["timestamp"] == drop_time.isoformat()),
        "occupancy_count",
    ] = 0

    booking_rows = []
    demand_weights = np.array([
        0.3 if hour < 6 else
        1.8 if 7 <= hour < 10 else
        1.2 if 10 <= hour < 16 else
        2.5 if 16 <= hour < 20 else
        0.8
        for hour in range(24)
    ])
    demand_weights /= demand_weights.sum()

    for day_offset in range(DEMO_DAYS):
        day = DEMO_START + pd.Timedelta(days=day_offset)
        for booking_number in range(40):
            lot_id = list(lots)[(booking_number + day_offset) % len(lots)]
            hour = int(random.choice(24, p=demand_weights))
            start = day + pd.Timedelta(
                hours=hour,
                minutes=int(random.integers(0, 60)),
            )
            duration = int(random.integers(1, 5))
            end = start + pd.Timedelta(hours=duration)
            booking_rows.append({
                "booking_id": f"DEMO-{day_offset + 1:02d}-{booking_number + 1:03d}",
                "user_id": int(random.integers(1, 181)),
                "parking_lot_id": lot_id,
                "booking_time": (
                    start - pd.Timedelta(minutes=int(random.integers(5, 1440)))
                ).isoformat(),
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "amount": round(duration * lots[lot_id]["hourly_rate"] * 1.05, 2),
                "status": "completed",
                "payment_status": "succeeded",
                "vehicle_type": str(
                    random.choice(["car", "bike", "suv", "ev"])
                ),
            })

    bookings_path = directory / "demo_bookings.csv"
    occupancy_path = directory / "demo_occupancy.csv"
    pd.DataFrame(booking_rows).to_csv(bookings_path, index=False)
    occupancy_frame.to_csv(occupancy_path, index=False)
    return bookings_path, occupancy_path


def _json_safe(value):
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return _json_safe(value.item())
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as output:
        json.dump(_json_safe(payload), output, indent=2, allow_nan=False)


def run_demo(
    data_directory: Path = DEMO_DATA_DIRECTORY,
    output_directory: Path = DEMO_OUTPUT_DIRECTORY,
) -> dict:
    """Run synthetic data through booking ETL and occupancy analytics/models."""
    bookings_path, occupancy_path = generate_synthetic_data(data_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    raw_bookings = pd.read_csv(bookings_path)
    booking_schema = validate_schema(raw_bookings)
    booking_timestamps = validate_timestamps(raw_bookings)
    if booking_schema["status"] != "passed":
        raise ValueError(
            "Synthetic booking data failed schema validation: "
            f"{booking_schema['missing_required_columns']}"
        )
    if booking_timestamps["status"] != "passed":
        raise ValueError(
            "Synthetic booking data failed timestamp validation: "
            f"{booking_timestamps['errors']}"
        )

    raw_directory = output_directory / "raw"
    raw_frame = save_raw_data(
        raw_bookings.to_dict(orient="records"),
        raw_directory,
    )
    transformed = transform_bookings(raw_frame)

    processed_directory = output_directory / "processed"
    processed_directory.mkdir(parents=True, exist_ok=True)
    transformed.to_csv(
        processed_directory / "booking_features.csv",
        index=False,
    )
    aggregated = aggregate_booking_data(transformed)
    aggregated.to_csv(
        processed_directory / "booking_aggregated.csv",
        index=False,
    )

    booking_quality = run_quality_checks(transformed)
    booking_eda = generate_eda_summary(transformed)
    if booking_quality["overall_status"] != "PASSED":
        raise ValueError(
            "Synthetic booking data failed quality checks: "
            f"{booking_quality.get('failed_checks', [])}"
        )
    quality_report_path = save_validation_report(
        booking_quality,
        booking_eda,
        str(output_directory / "quality"),
    )
    booking_analytics = generate_analytics(transformed)
    _write_json(
        output_directory / "booking_analytics.json",
        booking_analytics,
    )

    occupancy_raw = pd.read_csv(occupancy_path)
    occupancy, occupancy_validation = validate_occupancy_data(
        occupancy_raw,
        source=str(occupancy_path),
    )
    occupancy.to_csv(
        processed_directory / "occupancy_features.csv",
        index=False,
    )

    trends = calculate_trend_summary(occupancy)
    recent_trends = calculate_recent_trend(occupancy)
    model, model_metrics, holdout = train_occupancy_model(occupancy)
    forecasts = forecast_next_hour(occupancy, model)
    anomaly_records, anomaly_summary, anomaly_insights = (
        run_anomaly_analysis(occupancy)
    )
    peak_hours = summarize_peak_hours(occupancy)
    peak_hours_by_lot = summarize_peak_hours_by_lot(occupancy)
    peak_days = summarize_peak_days(occupancy)
    high_occupancy = find_high_occupancy_periods(occupancy)
    peak_insights = peak_hour_narrative(peak_hours, peak_days)

    occupancy_outputs = {
        "occupancy_trends.csv": trends,
        "recent_trends.csv": recent_trends,
        "forecast_holdout.csv": holdout,
        "next_hour_forecasts.csv": forecasts,
        "anomaly_records.csv": anomaly_records,
        "anomaly_summary.csv": anomaly_summary,
        "peak_hours.csv": peak_hours,
        "peak_hours_by_lot.csv": peak_hours_by_lot,
        "peak_days.csv": peak_days,
        "high_occupancy_periods.csv": high_occupancy,
    }
    for filename, frame in occupancy_outputs.items():
        frame.to_csv(output_directory / filename, index=False)

    results = {
        "status": "success",
        "booking_data": {
            "source": str(bookings_path),
            "raw_rows": len(raw_bookings),
            "transformed_rows": len(transformed),
            "aggregated_rows": len(aggregated),
            "schema_status": booking_schema["status"],
            "timestamp_status": booking_timestamps["status"],
            "quality_status": booking_quality["overall_status"],
            "quality_score": booking_quality["quality_score"],
            "quality_report": str(quality_report_path),
            "analytics": booking_analytics,
        },
        "occupancy_data": {
            "source": str(occupancy_path),
            "validation": occupancy_validation.to_dict(),
            "trend_summary": trends.to_dict(orient="records"),
            "recent_trends": recent_trends.to_dict(orient="records"),
            "model": model_metrics,
            "forecast": forecasts.to_dict(orient="records"),
            "anomaly_records": len(anomaly_records),
            "anomaly_summary": anomaly_summary.to_dict(orient="records"),
            "anomaly_insights": anomaly_insights,
            "peak_hour_insights": peak_insights,
        },
        "outputs_directory": str(output_directory),
    }
    _write_json(output_directory / "demo_results.json", results)
    return results


if __name__ == "__main__":
    result = run_demo()
    print(json.dumps(_json_safe(result), indent=2))
