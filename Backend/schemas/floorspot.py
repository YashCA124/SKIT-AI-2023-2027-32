from typing import List

from pydantic import BaseModel, field_validator


class FloorSpotSchema(BaseModel):
    floor_number: int
    new_spots: int

    @field_validator("floor_number")
    @classmethod
    def validate_floor_number(cls, value: int) -> int:
        if value < -10:
            raise ValueError("Too many basement levels")
        if value > 50:
            raise ValueError("Too many floors")
        return value

    @field_validator("new_spots")
    @classmethod
    def validate_new_spots(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("New spots must be greater than 0")
        if value > 1000:
            raise ValueError("Too many spots to add at once")
        return value


class AddSpotsSchema(BaseModel):
    """Body of POST /merchant/addspots.

    NOTE: reconstructed from routers/.../addspots.py (lot_id + floor list);
    the original file for it was not provided. Replace if it differs.
    """

    lot_id: int
    floor: List[FloorSpotSchema]

    @field_validator("lot_id")
    @classmethod
    def validate_lot_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Only positive lot IDs allowed")
        return value

    @field_validator("floor")
    @classmethod
    def validate_floor_list(cls, value: List[FloorSpotSchema]) -> List[FloorSpotSchema]:
        if not value:
            raise ValueError("Floor data is required")
        seen = set()
        for f in value:
            if f.floor_number in seen:
                raise ValueError(f"Duplicate floor number {f.floor_number}")
            seen.add(f.floor_number)
        return value
