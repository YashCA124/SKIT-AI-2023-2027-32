from datetime import datetime

from pydantic import BaseModel, field_validator


class ExtendBookingSchema(BaseModel):
    lot_id: int
    floor_id: int
    spot_id: int

    new_leaving_timestamp: datetime

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

    @field_validator("new_leaving_timestamp")
    @classmethod
    def validate_time(cls, value: datetime) -> datetime:
        if value <= datetime.now(value.tzinfo):
            raise ValueError("New leaving time must be in future")
        return value


# --- response model for POST /user/booking/extend --------------------------
class ExtendBookingResponse(BaseModel):
    message: str
    booking_id: int
    previous_leaving_timestamp: str
    new_leaving_timestamp: str
