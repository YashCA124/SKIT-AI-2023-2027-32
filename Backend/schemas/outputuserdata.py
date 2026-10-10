from typing import Optional

from pydantic import BaseModel

from ._common import ORM_CONFIG


class User(BaseModel):
    """Output schema for a user row (no password / location)."""

    model_config = ORM_CONFIG

    id: int
    name: str
    email: str
    phone_no: str
    country: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    pincode: Optional[str] = None
