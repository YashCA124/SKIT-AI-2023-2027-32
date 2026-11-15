from marshmallow import Schema, fields

from ._common import get_value


class ActiveBooking(Schema):
    """Output schema for an active ParkingBooking."""

    user_id = fields.Integer()
    full_spot_id = fields.Method("get_full_spot_id")
    parking_timestamp = fields.Method("get_parking_timestamp")
    parking_timezone = fields.String()
    cost_per_unit = fields.Decimal(as_string=True)
    lot_name = fields.Method("get_lot_name")
    currency = fields.String()
    exchange_rate = fields.Decimal(as_string=True)
    base_currency = fields.Method("get_base_currency")

    def get_full_spot_id(self, obj):
        return get_value(obj, "spot.full_spot_id", "full_spot_id")

    def get_parking_timestamp(self, obj):
        return get_value(obj, "get_local_parking_timestamp", "parking_timestamp")

    def get_lot_name(self, obj):
        return get_value(obj, "get_lot_name", "lot_name")

    def get_base_currency(self, obj):
        return get_value(obj, "get_lot_currency", "base_currency")
