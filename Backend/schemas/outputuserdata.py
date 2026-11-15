from marshmallow import Schema, fields


class User(Schema):
    """Output schema for a user row (no password or location)."""

    id = fields.Integer()
    name = fields.String()
    email = fields.String()
    phone_no = fields.String()
    country = fields.String(allow_none=True)
    state = fields.String(allow_none=True)
    city = fields.String(allow_none=True)
    address = fields.String(allow_none=True)
    pincode = fields.String(allow_none=True)
