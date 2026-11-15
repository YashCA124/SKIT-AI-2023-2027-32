import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from analytics.occupancy_trends import build_supervised_frame
from analytics.schemas import validate_occupancy_data
from demo import run_demo
from demo import generate_synthetic_data
from scheduler.tasks import run_analytics
from validation.timestamp_validation import validate_timestamps


class OccupancyPipelineTests(unittest.TestCase):
    def test_timestamp_validation_fails_when_required_columns_are_missing(self):
        result = validate_timestamps(pd.DataFrame({"start_time": []}))

        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            result["errors"],
            [{"type": "missing_end_time", "count": 1}],
        )

    def test_scheduled_booking_task_runs_with_quality_checks(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            bookings_path, _ = generate_synthetic_data(root / "source")
            bookings = pd.read_csv(bookings_path).to_dict(orient="records")
            previous_directory = Path.cwd()
            try:
                os.chdir(root)
                with (
                    patch("scheduler.tasks.fetch_bookings", return_value=bookings),
                    patch("scheduler.tasks.RAW_DATA_PATH", root / "raw"),
                    patch(
                        "scheduler.tasks.PROCESSED_DATA_PATH",
                        root / "processed" / "features.csv",
                    ),
                    patch(
                        "scheduler.tasks.AGGREGATED_DATA_PATH",
                        root / "processed" / "aggregated.csv",
                    ),
                    patch(
                        "scheduler.tasks.save_validation_report",
                        return_value=str(root / "quality.json"),
                    ),
                ):
                    analytics = run_analytics.run()
            finally:
                os.chdir(previous_directory)

            self.assertEqual(analytics["status"], "success")
            self.assertEqual(analytics["total_bookings"], len(bookings))
            self.assertTrue((root / "processed" / "aggregated.csv").exists())

    def test_calendar_features_describe_the_forecast_hour(self):
        timestamps = pd.date_range(
            "2025-01-09T00:00:00Z",
            periods=50,
            freq="h",
        )
        frame = pd.DataFrame({
            "lot_id": "LOT-TEST",
            "timestamp": timestamps,
            "occupancy_count": np.arange(50) % 80,
            "capacity": 100,
        })

        supervised = build_supervised_frame(frame)
        row = supervised.loc[
            supervised["timestamp"] == pd.Timestamp("2025-01-10T23:00:00Z")
        ].iloc[0]

        self.assertAlmostEqual(row["hour_sin"], 0.0, places=7)
        self.assertAlmostEqual(
            row["day_sin"],
            np.sin(2 * np.pi * 5 / 7),
            places=7,
        )
        self.assertEqual(row["is_weekend"], 1)

    def test_occupancy_contract_removes_bad_and_exact_duplicate_rows(self):
        frame = pd.DataFrame([
            {
                "lot_id": "LOT-1",
                "timestamp": "2025-01-01T00:00:00Z",
                "occupancy_count": 5,
                "capacity": 10,
            },
            {
                "lot_id": "LOT-1",
                "timestamp": "2025-01-01T00:00:00Z",
                "occupancy_count": 5,
                "capacity": 10,
            },
            {
                "lot_id": "LOT-1",
                "timestamp": "not-a-date",
                "occupancy_count": 5,
                "capacity": 10,
            },
        ])

        cleaned, summary = validate_occupancy_data(frame)

        self.assertEqual(len(cleaned), 1)
        self.assertEqual(summary.duplicates_removed, 1)
        self.assertEqual(summary.invalid_rows_removed, 1)
        self.assertEqual(cleaned["timestamp"].dt.tz is not None, True)

    def test_synthetic_data_runs_through_etl_and_occupancy_models(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            results = run_demo(root / "data", root / "outputs")

            bookings = results["booking_data"]
            occupancy = results["occupancy_data"]
            self.assertEqual(results["status"], "success")
            self.assertEqual(bookings["schema_status"], "passed")
            self.assertEqual(bookings["timestamp_status"], "passed")
            self.assertEqual(bookings["quality_status"], "PASSED")
            self.assertGreater(bookings["transformed_rows"], 0)
            self.assertGreater(bookings["aggregated_rows"], 0)
            self.assertEqual(occupancy["validation"]["rows_kept"], 3 * 28 * 24)
            self.assertEqual(len(occupancy["forecast"]), 3)
            self.assertGreater(occupancy["anomaly_records"], 0)
            self.assertGreater(
                occupancy["model"]["forecast_model_training_rows"],
                occupancy["model"]["training_rows"],
            )
            anomalies = pd.read_csv(
                root / "outputs" / "anomaly_records.csv"
            )
            detected = set(
                zip(anomalies["lot_id"], anomalies["timestamp"])
            )
            self.assertIn(
                ("LOT-003", "2025-01-23 14:00:00+00:00"),
                detected,
            )
            self.assertIn(
                ("LOT-001", "2025-01-30 14:00:00+00:00"),
                detected,
            )
            self.assertEqual(occupancy["anomaly_records"], 2)
            self.assertEqual(bookings["quality_score"], 100.0)
            self.assertLess(
                occupancy["model"]["training_last_target_timestamp"],
                occupancy["model"]["testing_first_timestamp"],
            )
            self.assertTrue(
                (root / "outputs" / "processed" / "booking_features.csv").exists()
            )
            self.assertTrue(
                (root / "outputs" / "next_hour_forecasts.csv").exists()
            )


if __name__ == "__main__":
    unittest.main()
