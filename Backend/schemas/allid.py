from marshmallow import Schema, fields, validate


class AllID(Schema):
    lot_id = fields.Integer(required=True, validate=validate.Range(min=1))
    floor_id = fields.Integer(required=True, validate=validate.Range(min=-10, max=50))
    spot_id = fields.Integer(required=True, validate=validate.Range(min=1))


AllIDSchema = AllID


class ReleaseResponse(Schema):
    message = fields.String(required=True)
    booking_id = fields.Integer(required=True)
    total_cost = fields.Float(allow_none=True, load_default=None)
    currency = fields.String(required=True)
    exchange_rate = fields.Float(required=True)
    total_time_in_hours = fields.Float(allow_none=True, load_default=None)
