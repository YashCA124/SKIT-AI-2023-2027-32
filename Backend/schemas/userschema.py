import re
from typing import Any

import phonenumbers
import pycountry
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    post_load,
    pre_load,
    validate,
    validates_schema,
)
from phonenumbers import NumberParseException
from zxcvbn import zxcvbn

from filehandling import postal_patterns
from models import User, UserType


def _validate_name(value: str) -> None:
    if not re.fullmatch(r"[a-zA-Z\s\-']{2,100}", value):
        raise ValidationError(
            "Name must contain only letters, spaces, hyphens, or apostrophes"
        )


def _validate_state(value: str) -> None:
    if not re.fullmatch(r"[a-zA-Z\s\-']+", value):
        raise ValidationError("Invalid state format")


def _validate_city(value: str) -> None:
    if not re.fullmatch(r"[a-zA-Z\s\-']+", value):
        raise ValidationError("Invalid city format")


def _validate_password(value: str) -> None:
    if len(value) < 6:
        raise ValidationError("Password must be at least 6 characters")

    result = zxcvbn(value)
    if result["score"] < 3:
        raise ValidationError(
            {
                "message": "Password is too weak",
                "suggestions": result["feedback"].get("suggestions", []),
                "warning": result["feedback"].get("warning", ""),
            }
        )


class UserCreate(Schema):
    """Validate registration data and build the corresponding User model."""

    name = fields.String(required=True, validate=_validate_name)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True, validate=_validate_password)
    country = fields.String(required=True)
    phone_no = fields.String(required=True)
    state = fields.String(required=True, validate=_validate_state)
    city = fields.String(required=True, validate=_validate_city)
    address = fields.String(required=True)
    pincode = fields.String(required=True)
    user_type = fields.String(required=True, validate=validate.OneOf(("U", "M")))
    location_permission_granted = fields.Boolean(allow_none=True, load_default=None)
    latitude = fields.Float(allow_none=True, load_default=None)
    longitude = fields.Float(allow_none=True, load_default=None)

    class Meta:
        unknown = EXCLUDE

    @pre_load
    def normalize_input(self, data: Any, **_kwargs: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }
        for field_name in ("state", "city"):
            if isinstance(normalized.get(field_name), str):
                normalized[field_name] = normalized[field_name].lower()

        country = normalized.get("country")
        if isinstance(country, str):
            try:
                normalized["country"] = pycountry.countries.search_fuzzy(country)[
                    0
                ].alpha_2
            except LookupError as exc:
                raise ValidationError({"country": ["Invalid country name"]}) from exc

        return normalized

    @validates_schema
    def validate_related_fields(self, data: dict[str, Any], **_kwargs: Any) -> None:
        errors: dict[str, list[str]] = {}
        country_code = data.get("country")

        if country_code and "phone_no" in data:
            try:
                parsed = phonenumbers.parse(data["phone_no"], country_code)
            except NumberParseException:
                errors["phone_no"] = ["Invalid phone number format"]
            else:
                if not phonenumbers.is_valid_number(parsed):
                    errors["phone_no"] = [
                        "Invalid phone number for selected country"
                    ]

        if country_code and "pincode" in data:
            pattern = postal_patterns.get(country_code)
            if pattern and not re.match(pattern, data["pincode"]):
                errors["pincode"] = ["Invalid postal code for selected country"]

        if data.get("location_permission_granted") is True:
            if data.get("latitude") is None or data.get("longitude") is None:
                errors["latitude"] = [
                    "Latitude and longitude required when permission is granted"
                ]
                errors["longitude"] = [
                    "Latitude and longitude required when permission is granted"
                ]
            else:
                if not -90 <= data["latitude"] <= 90:
                    errors["latitude"] = ["Invalid latitude range"]
                if not -180 <= data["longitude"] <= 180:
                    errors["longitude"] = ["Invalid longitude range"]

        if errors:
            raise ValidationError(errors)

    @post_load
    def make_user(self, data: dict[str, Any], **_kwargs: Any) -> User:
        data.pop("latitude", None)
        data.pop("longitude", None)
        data["user_type"] = UserType(data["user_type"])
        return User(**data)


class UserRead(Schema):
    """Serialize a user without exposing its password."""

    id = fields.Integer(dump_only=True)
    name = fields.String(dump_only=True)
    email = fields.Email(dump_only=True)
    phone_no = fields.String(dump_only=True)
    country = fields.String(dump_only=True)
    state = fields.String(dump_only=True)
    city = fields.String(dump_only=True)
    address = fields.String(dump_only=True)
    pincode = fields.String(dump_only=True)
    user_type = fields.Enum(UserType, by_value=True, dump_only=True)
    location_permission_granted = fields.Boolean(
        allow_none=True, dump_default=None, dump_only=True
    )
    latitude = fields.Float(allow_none=True, dump_default=None, dump_only=True)
    longitude = fields.Float(allow_none=True, dump_default=None, dump_only=True)


UserSchema = UserRead
