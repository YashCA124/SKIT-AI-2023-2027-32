from marshmallow import Schema, fields

from ._common import get_value


class CompletedBooking(Schema):
    """Output schema for a completed ParkingBooking."""

    user_id = fields.Integer()
    full_spot_id = fields.Method("get_full_spot_id")
    parking_timestamp = fields.Method("get_parking_timestamp")
    leaving_timestamp = fields.Method("get_leaving_timestamp")
    parking_timezone = fields.String()
    cost_per_unit = fields.Decimal(as_string=True)
    total_cost = fields.Method("get_total_cost")
    total_hour = fields.Method("get_total_hour")
    lot_name = fields.Method("get_lot_name")
    currency = fields.String()
    exchange_rate = fields.Decimal(as_string=True)
    base_currency = fields.Method("get_base_currency")

    def get_full_spot_id(self, obj):
        return get_value(obj, "spot.full_spot_id", "full_spot_id")

    def get_parking_timestamp(self, obj):
        return get_value(obj, "get_local_parking_timestamp", "parking_timestamp")

    def get_leaving_timestamp(self, obj):
        return get_value(obj, "get_local_leaving_timestamp", "leaving_timestamp")

    def get_total_cost(self, obj):
        value = get_value(obj, "get_total_cost", "total_cost")
        return None if value is None else str(value)

    def get_total_hour(self, obj):
        return get_value(obj, "get_total_hour", "total_hour")

    def get_lot_name(self, obj):
        return get_value(obj, "get_lot_name", "lot_name")

    def get_base_currency(self, obj):
        return get_value(obj, "get_lot_currency", "base_currency")


class ReleasedRecordItem(Schema):
    id = fields.Integer()
    spot_id = fields.Integer()
    cost_per_unit = fields.Float()
    currency = fields.String()
    parking_timestamp = fields.String(allow_none=True)
    leaving_timestamp = fields.String(allow_none=True)
    status = fields.String()


class ReleasedRecordResponse(Schema):
    message = fields.String()
    released_records = fields.Nested(ReleasedRecordItem, many=True)
