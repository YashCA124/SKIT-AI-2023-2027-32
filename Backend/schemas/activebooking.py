from typing import Optional

from pydantic import AliasChoices, AliasPath, BaseModel, Field

from ._common import ORM_CONFIG, DecimalStr


class ActiveBooking(BaseModel):
    """Output schema for an active ParkingBooking."""

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
    parking_timezone: str
    cost_per_unit: DecimalStr
    lot_name: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("get_lot_name", "lot_name"),
    )
    currency: str
    exchange_rate: DecimalStr
    base_currency: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("get_lot_currency", "base_currency"),
    )
