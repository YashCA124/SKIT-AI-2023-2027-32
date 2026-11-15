from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates_schema,
)


def _strip_strings(data):
    if isinstance(data, dict):
        return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }
    return data


class BookingCreate(Schema):
    spot_id = fields.Integer(required=True, validate=validate.Range(min=1))
    parking_timezone = fields.String(load_default="UTC")

    @pre_load
    def strip_input(self, data, **kwargs):
        return _strip_strings(data)

    @validates_schema
    def validate_timezone(self, data, **kwargs):
        try:
            ZoneInfo(data["parking_timezone"])
        except ZoneInfoNotFoundError as exc:
            raise ValidationError(
                {"parking_timezone": ["Use a valid IANA time zone, such as Asia/Kolkata"]}
            ) from exc


class DemoPaymentSimulation(Schema):
    outcome = fields.String(required=True, validate=validate.OneOf(("SUCCESS", "FAILED")))


class FloorCreate(Schema):
    floor_id = fields.Integer(required=True, validate=validate.Range(min=-10, max=100))
    total_spots = fields.Integer(required=True, validate=validate.Range(min=1, max=500))


class LotCreate(Schema):
    location_name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    price = fields.Float(required=True, validate=validate.Range(min=0, max=100000))
    currency = fields.String(required=True, validate=validate.Length(equal=3))
    country = fields.String(required=True, validate=validate.Length(equal=2))
    city = fields.String(required=True, validate=validate.Length(min=1, max=100))
    state = fields.String(required=True, validate=validate.Length(min=1, max=100))
    address = fields.String(required=True, validate=validate.Length(min=1, max=255))
    pincode = fields.String(required=True, validate=validate.Length(min=1, max=20))
    floors = fields.List(
        fields.Nested(FloorCreate),
        required=True,
        validate=validate.Length(min=1, max=20),
    )
    latitude = fields.Float(required=True, validate=validate.Range(min=-90, max=90))
    longitude = fields.Float(required=True, validate=validate.Range(min=-180, max=180))

    @pre_load
    def strip_input(self, data, **kwargs):
        return _strip_strings(data)

    @validates_schema
    def validate_codes_and_floors(self, data, **kwargs):
        errors = {}
        country = data.get("country")
        currency = data.get("currency")
        if country and (len(country) != 2 or not country.isalpha()):
            errors["country"] = ["Country must be a two-letter ISO code"]
        if currency and (len(currency) != 3 or not currency.isalpha()):
            errors["currency"] = ["Currency must be a three-letter ISO code"]
        floors = data.get("floors", [])
        floor_ids = [floor["floor_id"] for floor in floors]
        if len(floor_ids) != len(set(floor_ids)):
            errors["floors"] = ["Floor numbers must be unique within a lot"]
        if errors:
            raise ValidationError(errors)
        if country:
            data["country"] = country.upper()
        if currency:
            data["currency"] = currency.upper()


class LotUpdate(Schema):
    price = fields.Float(
        allow_none=True, load_default=None, validate=validate.Range(min=0, max=100000)
    )
    available = fields.String(
        allow_none=True,
        load_default=None,
        validate=validate.OneOf(("ACTIVE", "BLOCK")),
    )

    @validates_schema
    def require_update(self, data, **kwargs):
        if data.get("price") is None and data.get("available") is None:
            raise ValidationError("Provide a price or availability status to update")


class LotStatusUpdate(Schema):
    available = fields.String(
        required=True, validate=validate.OneOf(("ACTIVE", "BLOCK"))
    )


class AdminLotUpdate(Schema):
    location_name = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(min=2, max=120)
    )
    price = fields.Float(
        allow_none=True, load_default=None, validate=validate.Range(min=0, max=100000)
    )
    currency = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(equal=3)
    )
    country = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(equal=2)
    )
    city = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(min=1, max=100)
    )
    state = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(min=1, max=100)
    )
    address = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(min=1, max=255)
    )
    pincode = fields.String(
        allow_none=True, load_default=None, validate=validate.Length(min=1, max=20)
    )
    owner_id = fields.Integer(
        allow_none=True, load_default=None, validate=validate.Range(min=1)
    )

    @pre_load
    def strip_input(self, data, **kwargs):
        return _strip_strings(data)

    @validates_schema
    def require_update(self, data, **kwargs):
        if not any(value is not None for value in data.values()):
            raise ValidationError("Provide at least one parking-lot field to update")

    @validates_schema
    def normalize_codes(self, data, **kwargs):
        for field_name in ("country", "currency"):
            value = data.get(field_name)
            if value and not value.isalpha():
                raise ValidationError(
                    {field_name: [f"{field_name.capitalize()} must contain letters only"]}
                )
            if value:
                data[field_name] = value.upper()


class UserRoleUpdate(Schema):
    role = fields.String(required=True, validate=validate.OneOf(("U", "M")))
