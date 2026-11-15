from marshmallow import Schema, fields

from ._common import enum_name, get_value
from .outputuserdata import User


class Spot(Schema):
    id = fields.Integer()
    spot = fields.Method("get_spot")
    status = fields.Method("get_status")
    available = fields.Method("get_available")

    def get_spot(self, obj):
        return get_value(obj, "full_spot_id", "spot")

    def get_status(self, obj):
        return enum_name(get_value(obj, "status"))

    def get_available(self, obj):
        return enum_name(get_value(obj, "available"))


class Floor(Schema):
    id = fields.Integer()
    label = fields.String()
    total_spot_count = fields.Integer()
    floor_id = fields.Integer()
    available = fields.Method("get_available")
    spots = fields.Nested(Spot, many=True)

    def get_available(self, obj):
        return enum_name(get_value(obj, "available"))


class Lot(Schema):
    id = fields.Integer()
    location_name = fields.String()
    price = fields.Float()
    address = fields.Method("get_address")
    available = fields.Method("get_available")
    floors = fields.Nested(Floor, many=True)
    owner = fields.Nested(User, allow_none=True)

    def get_address(self, obj):
        return get_value(obj, "full_address", "address")

    def get_available(self, obj):
        return enum_name(get_value(obj, "available"))
