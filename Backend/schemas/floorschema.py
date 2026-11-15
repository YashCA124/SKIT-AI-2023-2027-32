from marshmallow import Schema, fields, pre_load, validate

from models.available_status import AvailableStatus


class FloorSchema(Schema):
    floor_number = fields.Integer(required=True, validate=validate.Range(min=-10, max=50))
    total_number_of_spots = fields.Integer(
        required=True, validate=validate.Range(min=1, max=1000)
    )
    available = fields.String(
        load_default="ACTIVE",
        validate=validate.OneOf([status.value for status in AvailableStatus]),
    )

    @pre_load
    def normalize_available(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get("available"), str):
            data = dict(data)
            data["available"] = data["available"].upper()
        return data
