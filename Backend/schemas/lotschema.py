
import re
from typing import List, Optional

import pycountry
from geoalchemy2.elements import WKTElement
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlalchemy.orm import Session

from models import ParkingLot, Floor, ParkingSpot, AvailableStatus, BookingStatus
from filehandling import postal_patterns


# ---------------------------------------------------------------------------
# Floor sub-schema (adjust fields to match your actual FloorSchema)
# ---------------------------------------------------------------------------
class FloorCreate(BaseModel):
    floor_id: int
    total_spots: int
    available: str = "ACTIVE"

    # Any FloorSchema-specific field validators should be added here.


# ---------------------------------------------------------------------------
# Lot schema
# ---------------------------------------------------------------------------
class LotCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    location_name: str
    price: float

    country: str
    city: str
    state: str
    address: str
    pincode: str

    available: str = "ACTIVE"

    floors: List[FloorCreate]

    latitude: float
    longitude: float

    # -- per-field validators (equivalent of @validates(...)) --------------

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Price cannot be negative")
        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, value: str) -> str:
        try:
            pycountry.countries.search_fuzzy(value)
        except Exception:
            raise ValueError("Invalid country")
        return value

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise ValueError("Invalid state")
        return value

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise ValueError("Invalid city")
        return value

    @field_validator("available")
    @classmethod
    def validate_available(cls, value: str) -> str:
        if value.upper() not in [e.value for e in AvailableStatus]:
            raise ValueError("Invalid availability")
        return value

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, value: str, info) -> str:
        country = info.data.get("country")

        if not country:
            raise ValueError("Country required")

        country_code = pycountry.countries.search_fuzzy(country)[0].alpha_2
        pattern = postal_patterns.get(country_code)

        if pattern and not re.match(pattern, value):
            raise ValueError("Invalid postal code")

        return value

    # -- cross-field validation (equivalent of @validates_schema) ----------

    @model_validator(mode="after")
    def validate_lot(self) -> "LotCreate":
        if not (-90 <= self.latitude <= 90):
            raise ValueError("Invalid latitude range")

        if not (-180 <= self.longitude <= 180):
            raise ValueError("Invalid longitude range")

        if not self.floors:
            raise ValueError("At least one floor required")

        seen = set()
        for f in self.floors:
            if f.floor_id in seen:
                raise ValueError(f"Duplicate floor_id: {f.floor_id}")
            seen.add(f.floor_id)

            if f.total_spots <= 0:
                raise ValueError("total_spots must be > 0")

        return self


def build_lot(payload: LotCreate, db: Session) -> ParkingLot:
   
    country_ = pycountry.countries.search_fuzzy(payload.country)[0]

    point = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)

    lot = ParkingLot(
        location_name=payload.location_name,
        price=payload.price,
        country=country_.alpha_2,
        city=payload.city.lower(),
        state=payload.state.lower(),
        address=payload.address,
        pincode=payload.pincode,
        available=AvailableStatus(payload.available.upper()),
        location_coordinates=point,
    )

    all_spots = []

    for floor_data in payload.floors:
        floor = Floor(
            floor_id=floor_data.floor_id,
            available=AvailableStatus(floor_data.available.upper()),
        )
        lot.floors.append(floor)

        for i in range(1, floor_data.total_spots + 1):
            spot = ParkingSpot(
                spot_id=i,
                floor=floor,
                status=BookingStatus.SPOT_AVAILABLE,
                available=AvailableStatus.ACTIVE,
            )
            all_spots.append(spot)

    db.bulk_save_objects(all_spots)

    return lot