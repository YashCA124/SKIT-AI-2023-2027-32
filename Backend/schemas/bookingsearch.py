from marshmallow import Schema, fields, validate


class BookingSearchSchema(Schema):
    radius_km = fields.Float(
        load_default=5.0, validate=validate.Range(min=0, min_inclusive=False, max=50)
    )


class NearbyLot(Schema):
    lot_id = fields.Integer(required=True)
    location_name = fields.String(required=True)
    original_price = fields.Float(required=True)
    original_currency = fields.String(required=True)
    converted_price = fields.Float(required=True)
    user_currency = fields.String(required=True)
    exchange_rate = fields.Float(required=True)
    distance_km = fields.Float(required=True)
    eta_minutes = fields.Integer(required=True)
    available_spots = fields.Integer(required=True)
    address = fields.String(required=True)


class BookingSearchResponse(Schema):
    radius_km = fields.Float(required=True)
    total_results = fields.Integer(required=True)
    parking_lots = fields.List(fields.Nested(NearbyLot), required=True)
    conversion = fields.Boolean(required=True)
