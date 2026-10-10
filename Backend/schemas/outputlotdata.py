from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field

from ._common import ORM_CONFIG, EnumName
from .outputuserdata import User


class Spot(BaseModel):
    model_config = ORM_CONFIG

    id: int
    spot: str = Field(validation_alias=AliasChoices("full_spot_id", "spot"))
    status: EnumName = None
    available: EnumName = None


class Floor(BaseModel):
    model_config = ORM_CONFIG

    id: int
    label: str
    total_spot_count: int
    floor_id: int
    available: EnumName = None
    spots: List[Spot] = []


class Lot(BaseModel):
    model_config = ORM_CONFIG

    id: int
    location_name: str
    price: float
    address: str = Field(validation_alias=AliasChoices("full_address", "address"))
    available: EnumName = None
    floors: List[Floor] = []
    owner: Optional[User] = None
