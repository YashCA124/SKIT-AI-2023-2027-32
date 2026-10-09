"""Per-floor payload used by AddFloorSchema.

NOTE: reconstructed from how routers/.../addfloor.py uses it
(floor_number, total_number_of_spots, available) because floorschema.py was
not provided. Replace with the real conversion if the old rules differ.
"""
from pydantic import BaseModel, field_validator

from models.available_status import AvailableStatus


class FloorSchema(BaseModel):
    floor_number: int
    total_number_of_spots: int
    available: str = "ACTIVE"

    @field_validator("floor_number")
    @classmethod
    def validate_floor_number(cls, value: int) -> int:
        if value < -10:
            raise ValueError("Too many basement levels")
        if value > 50:
            raise ValueError("Too many floors")
        return value

    @field_validator("total_number_of_spots")
    @classmethod
    def validate_total_spots(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Total number of spots must be greater than 0")
        if value > 1000:
            raise ValueError("Too many spots")
        return value

    @field_validator("available")
    @classmethod
    def validate_available(cls, value: str) -> str:
        value = value.upper()
        if value not in [e.value for e in AvailableStatus]:
            raise ValueError("Invalid availability")
        return value
