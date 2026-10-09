from pydantic import BaseModel, Field


class LotID(BaseModel):
    lot_id: int = Field(gt=0, description="Only positive lot IDs allowed")
