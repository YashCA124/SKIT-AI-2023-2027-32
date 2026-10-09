from typing import List

from pydantic import BaseModel, field_validator

from .floorschema import FloorSchema


class AddFloorSchema(BaseModel):
    lot_id: int
    floor: List[FloorSchema]

    @field_validator("lot_id")
    @classmethod
    def validate_lot_id(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Only positive lot IDs allowed")
        return value

    @field_validator("floor")
    @classmethod
    def validates_floor_list(cls, value: List[FloorSchema]) -> List[FloorSchema]:
        if not value:
            raise ValueError("Floor data is required")

        seen = set()
        for f in value:
            if f.floor_number in seen:
                raise ValueError(f"Duplicate floor number {f.floor_number}")
            seen.add(f.floor_number)
        return value
