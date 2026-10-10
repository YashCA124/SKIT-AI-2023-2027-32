from pydantic import BaseModel, Field


class LotFloorSchema(BaseModel):
    lot_id: int = Field(gt=0)
    floor_id: int = Field(ge=-10, le=50)
