import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ML_ROOT = Path(__file__).resolve().parent

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:8000"
)

BOOKINGS_ENDPOINT = (
    f"{BACKEND_URL}/api/ml/bookings"
)

RAW_DATA_PATH = ML_ROOT / "data" / "raw"

PROCESSED_DATA_PATH = ML_ROOT / "data" / "processed" / "booking_features.csv"

AGGREGATED_DATA_PATH = ML_ROOT / "data" / "processed" / "booking_aggregated.csv"

FEATURE_COLUMNS = [
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
    "is_weekend",
    "occupancy_pct",
    "occupancy_lag_1",
    "occupancy_lag_2",
    "occupancy_lag_3",
    "occupancy_lag_24",
    "occupancy_rolling_mean_3",
    "occupancy_rolling_mean_6",
    "occupancy_rolling_mean_24",
]

FORECAST_HORIZON_HOURS = 1
MIN_HOURS_FOR_FORECAST = 25
MIN_TRAINING_SAMPLES = 50
PREVIOUS_WINDOW_HOURS = 24
RANDOM_STATE = 42
RECENT_WINDOW_HOURS = 24
TEST_FRACTION = 0.2

HIGH_OCCUPANCY_THRESHOLD = 0.85
MEDIUM_OCCUPANCY_THRESHOLD = 0.65
PEAK_TOP_N_HOURS = 5