from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BookingCreate(BaseModel):
    spot_id: int = Field(gt=0)
    parking_timezone: str = "UTC"

    @field_validator("parking_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Use a valid IANA time zone, such as Asia/Kolkata") from exc
        return value


class FloorCreate(BaseModel):
    floor_id: int = Field(ge=-10, le=100)
    total_spots: int = Field(gt=0, le=500)


class LotCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    location_name: str = Field(min_length=2, max_length=120)
    price: float = Field(ge=0, le=100000)
    currency: str = Field(min_length=3, max_length=3)
    country: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=255)
    pincode: str = Field(min_length=1, max_length=20)
    floors: list[FloorCreate] = Field(min_length=1, max_length=20)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @field_validator("country")
    @classmethod
    def validate_country_code(cls, value: str) -> str:
        normalized = value.upper()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("Country must be a two-letter ISO code")
        return normalized

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("Currency must be a three-letter ISO code")
        return normalized

    @model_validator(mode="after")
    def validate_unique_floors(self):
        floor_ids = [floor.floor_id for floor in self.floors]
        if len(floor_ids) != len(set(floor_ids)):
            raise ValueError("Floor numbers must be unique within a lot")
        return self


class LotUpdate(BaseModel):
    price: float | None = Field(default=None, ge=0, le=100000)
    available: Literal["ACTIVE", "BLOCK"] | None = None

    @model_validator(mode="after")
    def require_update(self):
        if self.price is None and self.available is None:
            raise ValueError("Provide a price or availability status to update")
        return self


class LotStatusUpdate(BaseModel):
    available: Literal["ACTIVE", "BLOCK"]


class UserRoleUpdate(BaseModel):
    role: Literal["M"]
