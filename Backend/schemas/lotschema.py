import re
from typing import Any

import pycountry
from geoalchemy2.elements import WKTElement
from marshmallow import (
    Schema,
    ValidationError,
    fields,
    pre_load,
    validates_schema,
)
from sqlalchemy.orm import Session

from filehandling import postal_patterns
from models import AvailableStatus, BookingStatus, Floor, ParkingLot, ParkingSpot


class FloorCreate(Schema):
    floor_id = fields.Integer(required=True)
    total_spots = fields.Integer(required=True)
    available = fields.String(load_default="ACTIVE")

    @pre_load
    def normalize_available(self, data: Any, **kwargs: Any) -> Any:
        if isinstance(data, dict) and isinstance(data.get("available"), str):
            data = dict(data)
            data["available"] = data["available"].upper()
        return data

    @validates_schema
    def validate_floor(self, data, **kwargs):
        errors = {}
        total_spots = data.get("total_spots")
        if total_spots is not None and total_spots <= 0:
            errors["total_spots"] = ["total_spots must be > 0"]
        if errors:
            raise ValidationError(errors)


class LotCreate(Schema):
    location_name = fields.String(required=True)
    price = fields.Float(required=True)
    country = fields.String(required=True)
    city = fields.String(required=True)
    state = fields.String(required=True)
    address = fields.String(required=True)
    pincode = fields.String(required=True)
    available = fields.String(load_default="ACTIVE")
    floors = fields.List(fields.Nested(FloorCreate), required=True)
    latitude = fields.Float(required=True)
    longitude = fields.Float(required=True)

    @pre_load
    def normalize_input(self, data: Any, **kwargs: Any) -> Any:
        if not isinstance(data, dict):
            return data
        normalized = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }
        if isinstance(normalized.get("available"), str):
            normalized["available"] = normalized["available"].upper()
        return normalized

    @validates_schema
    def validate_lot(self, data, **kwargs):
        errors = {}
        if data.get("price", 0) < 0:
            errors["price"] = ["Price cannot be negative"]
        country = data.get("country")
        country_code = None
        if country:
            if not re.fullmatch(r"[a-zA-Z\s\-']+", data.get("state", "")):
                errors["state"] = ["Invalid state"]
            if not re.fullmatch(r"[a-zA-Z\s\-']+", data.get("city", "")):
                errors["city"] = ["Invalid city"]
            try:
                country_code = pycountry.countries.search_fuzzy(country)[0].alpha_2
            except LookupError:
                errors["country"] = ["Invalid country"]
        if data.get("available") not in {status.value for status in AvailableStatus}:
            errors["available"] = ["Invalid availability"]
        if country_code:
            pattern = postal_patterns.get(country_code)
            if pattern and not re.match(pattern, data.get("pincode", "")):
                errors["pincode"] = ["Invalid postal code"]
        if not -90 <= data.get("latitude", 0) <= 90:
            errors["latitude"] = ["Invalid latitude range"]
        if not -180 <= data.get("longitude", 0) <= 180:
            errors["longitude"] = ["Invalid longitude range"]
        floors = data.get("floors", [])
        if not floors:
            errors["floors"] = ["At least one floor required"]
        floor_ids = [floor["floor_id"] for floor in floors]
        if len(floor_ids) != len(set(floor_ids)):
            errors["floors"] = ["Duplicate floor_id"]
        if errors:
            raise ValidationError(errors)


def build_lot(payload: Any, db: Session) -> ParkingLot:
    country = pycountry.countries.search_fuzzy(payload.country)[0]
    point = WKTElement(
        f"POINT({payload.longitude} {payload.latitude})", srid=4326
    )
    lot = ParkingLot(
        location_name=payload.location_name,
        price=payload.price,
        country=country.alpha_2,
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
        for spot_number in range(1, floor_data.total_spots + 1):
            spot = ParkingSpot(
                spot_id=spot_number,
                floor=floor,
                status=BookingStatus.SPOT_AVAILABLE,
                available=AvailableStatus.ACTIVE,
            )
            all_spots.append(spot)
    db.bulk_save_objects(all_spots)
    return lot
