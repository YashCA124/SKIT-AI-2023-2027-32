from marshmallow import Schema, fields, validate


class LotFloorSchema(Schema):
    lot_id = fields.Integer(required=True, validate=validate.Range(min=1))
    floor_id = fields.Integer(required=True, validate=validate.Range(min=-10, max=50))
