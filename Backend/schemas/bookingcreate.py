from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, field_validator, model_validator


class BookingCreateSchema(BaseModel):
    lot_id: int
    floor_id: int
    spot_id: int

    timezone: str = "UTC"

    parking_timestamp: Optional[datetime] = None
    leaving_timestamp: Optional[datetime] = None

    @field_validator("lot_id")
    @classmethod
    def validate_lot_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Invalid lot_id")
        return value

    @field_validator("floor_id")
    @classmethod
    def validate_floor_id(cls, value: int) -> int:
        if value < -10 or value > 50:
            raise ValueError("Invalid floor_id")
        return value

    @field_validator("spot_id")
    @classmethod
    def validate_spot_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Invalid spot_id")
        return value

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except Exception:
            raise ValueError("Invalid timezone")
        return value

    @model_validator(mode="after")
    def validate_timestamps(self) -> "BookingCreateSchema":
        pt, lt = self.parking_timestamp, self.leaving_timestamp
        if pt and lt and (pt.tzinfo is None) == (lt.tzinfo is None) and lt <= pt:
            raise ValueError("leaving_timestamp must be after parking_timestamp")
        return self


# --- response model for POST /user/booking ---------------------------------
class BookingCreated(BaseModel):
    booking_id: int
    spot: str
    cost: float
    parking_timestamp: Optional[str] = None


class BookingCreateResponse(BaseModel):
    message: str
    booking: BookingCreated
