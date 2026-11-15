from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from marshmallow import Schema, ValidationError, fields, validate, validates_schema


class BookingCreateSchema(Schema):
    lot_id = fields.Integer(required=True, validate=validate.Range(min=1))
    floor_id = fields.Integer(required=True, validate=validate.Range(min=-10, max=50))
    spot_id = fields.Integer(required=True, validate=validate.Range(min=1))
    timezone = fields.String(load_default="UTC")
    parking_timestamp = fields.DateTime(allow_none=True, load_default=None)
    leaving_timestamp = fields.DateTime(allow_none=True, load_default=None)

    @validates_schema
    def validate_timestamps(self, data, **kwargs):
        timezone = data["timezone"]
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValidationError({"timezone": ["Invalid timezone"]}) from exc

        parking = data.get("parking_timestamp")
        leaving = data.get("leaving_timestamp")
        if (
            parking
            and leaving
            and (parking.tzinfo is None) == (leaving.tzinfo is None)
            and leaving <= parking
        ):
            raise ValidationError(
                {"leaving_timestamp": ["leaving_timestamp must be after parking_timestamp"]}
            )


class BookingCreated(Schema):
    booking_id = fields.Integer(required=True)
    spot = fields.String(required=True)
    cost = fields.Float(required=True)
    parking_timestamp = fields.String(allow_none=True, load_default=None)


class BookingCreateResponse(Schema):
    message = fields.String(required=True)
    booking = fields.Nested(BookingCreated, required=True)
