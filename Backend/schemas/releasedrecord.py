from typing import List, Optional

from pydantic import AliasChoices, AliasPath, BaseModel, Field

from ._common import ORM_CONFIG, DecimalStr


class CompletedBooking(BaseModel):
    """Output schema for a completed ParkingBooking."""

    model_config = ORM_CONFIG

    user_id: int
    full_spot_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(AliasPath("spot", "full_spot_id"), "full_spot_id"),
    )
    parking_timestamp: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("get_local_parking_timestamp", "parking_timestamp"),
    )
    leaving_timestamp: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("get_local_leaving_timestamp", "leaving_timestamp"),
    )
    parking_timezone: str
    cost_per_unit: DecimalStr
    total_cost: Optional[DecimalStr] = Field(
        default=None, validation_alias=AliasChoices("get_total_cost", "total_cost")
    )
    total_hour: Optional[float] = Field(
        default=None, validation_alias=AliasChoices("get_total_hour", "total_hour")
    )
    lot_name: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("get_lot_name", "lot_name")
    )
    currency: str
    exchange_rate: DecimalStr
    base_currency: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("get_lot_currency", "base_currency"),
    )


# --- response model for GET /user/records/released -------------------------
class ReleasedRecordItem(BaseModel):
    id: int
    spot_id: int
    cost_per_unit: float
    currency: str
    parking_timestamp: Optional[str] = None
    leaving_timestamp: Optional[str] = None
    status: str


class ReleasedRecordResponse(BaseModel):
    message: str
    released_records: List[ReleasedRecordItem]
