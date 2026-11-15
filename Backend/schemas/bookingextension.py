from datetime import datetime

from marshmallow import Schema, ValidationError, fields, validate


def _must_be_future(value: datetime) -> None:
    if value <= datetime.now(value.tzinfo):
        raise ValidationError("New leaving time must be in future")


class ExtendBookingSchema(Schema):
    lot_id = fields.Integer(required=True, validate=validate.Range(min=1))
    floor_id = fields.Integer(required=True, validate=validate.Range(min=-10, max=50))
    spot_id = fields.Integer(required=True, validate=validate.Range(min=1))
    new_leaving_timestamp = fields.DateTime(
        required=True, validate=_must_be_future
    )


class ExtendBookingResponse(Schema):
    message = fields.String(required=True)
    booking_id = fields.Integer(required=True)
    previous_leaving_timestamp = fields.String(required=True)
    new_leaving_timestamp = fields.String(required=True)
