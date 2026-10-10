from typing import Optional

from pydantic import BaseModel, field_validator


class AllID(BaseModel):
    lot_id: int
    floor_id: int
    spot_id: int

    @field_validator("lot_id")
    @classmethod
    def validate_lot(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Invalid lot_id")
        return value

    @field_validator("floor_id")
    @classmethod
    def validate_floor(cls, value: int) -> int:
        if value < -10 or value > 50:
            raise ValueError("Invalid floor_id")
        return value

    @field_validator("spot_id")
    @classmethod
    def validate_spot(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Invalid spot_id")
        return value


# release.py imports it under this name
AllIDSchema = AllID


# --- response model for POST /user/booking/release -------------------------
class ReleaseResponse(BaseModel):
    message: str
    booking_id: int
    total_cost: Optional[float] = None
    currency: str
    exchange_rate: float
    total_time_in_hours: Optional[float] = None
