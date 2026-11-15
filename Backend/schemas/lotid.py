from marshmallow import Schema, fields, validate


class LotID(Schema):
    lot_id = fields.Integer(
        required=True, validate=validate.Range(min=1, error="Only positive lot IDs allowed")
    )
