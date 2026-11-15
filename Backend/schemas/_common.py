from collections.abc import Mapping
from enum import Enum
from types import SimpleNamespace
from typing import Any

from fastapi import Body, Depends, HTTPException
from marshmallow import Schema, ValidationError


def _validation_details(errors: Any, path: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    if isinstance(errors, dict):
        details = []
        for key, value in errors.items():
            next_path = path if key == "_schema" else (*path, key)
            details.extend(_validation_details(value, next_path))
        return details
    if isinstance(errors, list):
        if all(isinstance(error, str) for error in errors):
            return [
                {
                    "loc": ["body", *path],
                    "msg": error,
                    "type": "value_error",
                }
                for error in errors
            ]
        details = []
        for index, value in enumerate(errors):
            details.extend(_validation_details(value, (*path, index)))
        return details
    return [{"loc": ["body", *path], "msg": str(errors), "type": "value_error"}]


def enum_name(value: Any) -> Any:
    return value.name if isinstance(value, Enum) else value


def get_value(obj: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        value = obj
        try:
            for part in name.split("."):
                value = value[part] if isinstance(value, Mapping) else getattr(value, part)
        except (AttributeError, KeyError, TypeError):
            continue
        if value is not None:
            return value
    return default


def _namespace(value: Any) -> Any:
    if isinstance(value, Mapping):
        return SimpleNamespace(**{key: _namespace(item) for key, item in value.items()})
    if isinstance(value, list):
        return [_namespace(item) for item in value]
    return value


def load_payload(schema_type: type[Schema], payload: dict) -> Any:
    try:
        return _namespace(schema_type().load(payload))
    except ValidationError as exc:
        raise HTTPException(
            status_code=422, detail=_validation_details(exc.messages)
        ) from exc


def load_body(schema_type: type[Schema]):
    async def dependency(payload: dict = Body(...)) -> Any:
        return load_payload(schema_type, payload)

    return Depends(dependency)


def dump(schema: Schema, obj: Any, many: bool = False) -> Any:
    return schema.dump(obj, many=many)
