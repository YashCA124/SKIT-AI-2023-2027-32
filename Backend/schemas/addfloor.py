from marshmallow import Schema, ValidationError, fields, validates_schema

from .floorschema import FloorSchema


class AddFloorSchema(Schema):
    lot_id = fields.Integer(required=True)
    floor = fields.List(fields.Nested(FloorSchema), required=True)

    @validates_schema
    def validate_floors(self, data, **kwargs):
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
