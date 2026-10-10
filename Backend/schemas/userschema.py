import re
from typing import Literal, Optional

import pycountry
import phonenumbers
from phonenumbers import NumberParseException
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticCustomError
from zxcvbn import zxcvbn

from models import UserType, User
from filehandling import postal_patterns


class UserCreate(BaseModel):
    """Input schema (replaces the load side of the marshmallow UserSchema).

    NOTE: field order matters. `country` must be declared before `phone_no`
    and `pincode` so its normalized value is available in `info.data`.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str
    email: EmailStr
    password: str = Field(exclude=True)  # never serialized (load_only)

    country: str
    phone_no: str
    state: str
    city: str
    address: str
    pincode: str

    user_type: Literal["U", "M"]

    location_permission_granted: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # ---------- single-field validators ----------

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-']{2,100}$", v):
            raise ValueError(
                "Name must contain only letters, spaces, hyphens, or apostrophes"
            )
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Invalid state format")
        return v.lower()

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError("Invalid city format")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")

        result = zxcvbn(v)
        if result["score"] < 3:
            # Extra data is available via exc.errors()[i]["ctx"]
            raise PydanticCustomError(
                "weak_password",
                "Password is too weak",
                {
                    "suggestions": result["feedback"].get("suggestions", []),
                    "warning": result["feedback"].get("warning", ""),
                },
            )
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        try:
            # Normalize to alpha-2 code (was done in post_load)
            return pycountry.countries.search_fuzzy(v)[0].alpha_2
        except LookupError:
            raise ValueError("Invalid country name")

    # ---------- validators that depend on country ----------

    @field_validator("phone_no")
    @classmethod
    def validate_phone(cls, v: str, info: ValidationInfo) -> str:
        country_code = info.data.get("country")
        if not country_code:  # country itself failed validation
            return v
        try:
            parsed = phonenumbers.parse(v, country_code)
        except NumberParseException:
            raise ValueError("Invalid phone number format")
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number for selected country")
        return v

    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str, info: ValidationInfo) -> str:
        country_code = info.data.get("country")
        if not country_code:
            return v
        pattern = postal_patterns.get(country_code)
        if pattern and not re.match(pattern, v):
            raise ValueError("Invalid postal code for selected country")
        return v

    # ---------- cross-field validation ----------

    @model_validator(mode="after")
    def validate_location_logic(self) -> "UserCreate":
        if self.location_permission_granted is True:
            if self.latitude is None or self.longitude is None:
                raise ValueError(
                    "Latitude and longitude required when permission is granted"
                )
            if not (-90 <= self.latitude <= 90):
                raise ValueError("Invalid latitude range")
            if not (-180 <= self.longitude <= 180):
                raise ValueError("Invalid longitude range")
        return self

    # ---------- replaces @post_load ----------

    def to_user(self) -> User:
        data = self.model_dump(exclude={"latitude", "longitude"})
        data["password"] = self.password  # excluded from model_dump
        data["user_type"] = (
            UserType.PARKING_USER
            if self.user_type == "U"
            else UserType.PARKING_MERCHANT
        )
        return User(**data)


class UserRead(BaseModel):
    """Output schema (replaces dump side; id was dump_only, password load_only)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone_no: str
    country: str
    state: str
    city: str
    address: str
    pincode: str
    user_type: UserType
    location_permission_granted: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
