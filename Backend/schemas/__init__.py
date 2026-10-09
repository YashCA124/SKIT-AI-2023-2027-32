from .auth import (
    AdminLoginRequest,
    UserLoginRequest,
    RegistrationRequest,
    TokenResponse,
    LocationOut,
    UserOut,
    LoginResponse,
    UserLoginResponse,
)

from .outputuserdata import User
from .outputlotdata import Lot
from .activebooking import ActiveBooking
from .releasedrecord import CompletedBooking, ReleasedRecordResponse
from .allid import AllID, AllIDSchema, ReleaseResponse
from .bookingcreate import BookingCreateSchema, BookingCreateResponse
from .bookingextension import ExtendBookingSchema, ExtendBookingResponse
from .bookingsearch import BookingSearchSchema, BookingSearchResponse
from .floorschema import FloorSchema
from .addfloor import AddFloorSchema
from .floorspot import FloorSpotSchema, AddSpotsSchema
from .lotid import LotID
from .lotfloor import LotFloorSchema
from .userschema import UserCreate, UserRead

__all__ = [
    "User",
    "Lot",
    "ActiveBooking",
    "CompletedBooking",
    "ReleasedRecordResponse",
    "AllID",
    "AllIDSchema",
    "ReleaseResponse",
    "BookingCreateSchema",
    "BookingCreateResponse",
    "ExtendBookingSchema",
    "ExtendBookingResponse",
    "BookingSearchSchema",
    "BookingSearchResponse",
    "FloorSchema",
    "AddFloorSchema",
    "FloorSpotSchema",
    "AddSpotsSchema",
    "AdminLoginRequest",
    "UserLoginRequest",
    "RegistrationRequest",
    "TokenResponse",
    "LocationOut",
    "UserOut",
    "LoginResponse",
    "UserLoginResponse",
    "LotID",
    "LotFloorSchema",
    "UserCreate",
    "UserRead",
    "FloorCreate",
    "LotCreate",
    "build_lot",
]


def __getattr__(name):
    if name in {"FloorCreate", "LotCreate", "build_lot"}:
        from . import lotschema

        return getattr(lotschema, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")