from marshmallow import Schema, ValidationError, fields, validates_schema


class FloorSpotSchema(Schema):
    floor_number = fields.Integer(required=True)
    new_spots = fields.Integer(required=True)

    @validates_schema
    def validate_values(self, data, **kwargs):
        errors = {}
        floor_number = data.get("floor_number")
        if floor_number is not None and not -10 <= floor_number <= 50:
            errors["floor_number"] = ["Too many basement levels" if floor_number < -10 else "Too many floors"]
        new_spots = data.get("new_spots")
        if new_spots is not None and new_spots <= 0:
            errors["new_spots"] = ["New spots must be greater than 0"]
        elif new_spots is not None and new_spots > 1000:
            errors["new_spots"] = ["Too many spots to add at once"]
        if errors:
            raise ValidationError(errors)


class AddSpotsSchema(Schema):
    """Request body for adding spaces to multiple floors."""

    lot_id = fields.Integer(required=True)
    floor = fields.List(fields.Nested(FloorSpotSchema), required=True)

    @validates_schema
    def validate_floor_list(self, data, **kwargs):
        errors = {}
        if data.get("lot_id", 0) <= 0:
            errors["lot_id"] = ["Only positive lot IDs allowed"]
        floors = data.get("floor", [])
        if not floors:
            errors["floor"] = ["Floor data is required"]
        seen = set()
        duplicate_numbers = []
        for floor in floors:
            floor_number = floor["floor_number"]
            if floor_number in seen:
                duplicate_numbers.append(floor_number)
            seen.add(floor_number)
        if duplicate_numbers:
            errors["floor"] = [
                f"Duplicate floor number {floor_number}"
                for floor_number in duplicate_numbers
            ]
        if errors:
            raise ValidationError(errors)
