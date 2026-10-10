"""Shared helpers for the Pydantic schemas."""
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BeforeValidator, ConfigDict, PlainSerializer

# Marshmallow's `Decimal(as_string=True)` -> a JSON string such as "12.50".
DecimalStr = Annotated[
    Decimal,
    PlainSerializer(lambda v: str(v), return_type=str, when_used="always"),
]


def _enum_name(value: Any) -> Any:
    """Marshmallow `obj.status.name` equivalent: Enum member -> its name."""
    return value.name if isinstance(value, Enum) else value


# Enum member (or None) -> its `.name` string (or None).
EnumName = Annotated[Optional[str], BeforeValidator(_enum_name)]

# Base config for schemas that are built straight from SQLAlchemy objects.
ORM_CONFIG = ConfigDict(from_attributes=True, populate_by_name=True)


def dump(schema, obj, many: bool = False):
    """Replacement for marshmallow's `Schema(many=...).dump(obj)`.

    Returns plain JSON-safe data (Decimals as strings, enums as names), so the
    result can go straight into `json.dumps` / the Redis cache.
    """
    if many:
        return [schema.model_validate(o).model_dump(mode="json") for o in obj]
    return schema.model_validate(obj).model_dump(mode="json")
