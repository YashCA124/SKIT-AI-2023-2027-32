from typing import List

from pydantic import BaseModel, field_validator


class BookingSearchSchema(BaseModel):
    radius_km: float = 5.0

    @field_validator("radius_km")
    @classmethod
    def validate_radius(cls, value: float) -> float:
        if value <= 0 or value > 50:
            raise ValueError("radius_km must be > 0 and <= 50")
        return value


# --- response model for POST /user/booking/search --------------------------
class NearbyLot(BaseModel):
    lot_id: int
    location_name: str
    original_price: float
    original_currency: str
    converted_price: float
    user_currency: str
    exchange_rate: float
    distance_km: float
    eta_minutes: int
    available_spots: int
    address: str


class BookingSearchResponse(BaseModel):
    radius_km: float
    total_results: int
    parking_lots: List[NearbyLot]
    conversion: bool
