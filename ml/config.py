import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://localhost:5000"
)

BOOKINGS_ENDPOINT = (
    f"{BACKEND_URL}/api/ml/bookings"
)

RAW_DATA_PATH = "data/raw/bookings.csv"

PROCESSED_DATA_PATH = (
    "data/processed/booking_features.csv"
)

AGGREGATED_DATA_PATH = (
    "data/processed/booking_aggregated.csv"
)