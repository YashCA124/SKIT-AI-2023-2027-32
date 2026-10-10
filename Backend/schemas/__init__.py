from importlib import import_module

_SCHEMA_MODULES = {
    "AdminLoginRequest": "auth",
    "UserLoginRequest": "auth",
    "RegistrationRequest": "auth",
    "TokenResponse": "auth",
    "LocationOut": "auth",
    "UserOut": "auth",
    "LoginResponse": "auth",
    "UserLoginResponse": "auth",
    "User": "outputuserdata",
    "Lot": "outputlotdata",
    "ActiveBooking": "activebooking",
    "CompletedBooking": "releasedrecord",
    "ReleasedRecordResponse": "releasedrecord",
    "AllID": "allid",
    "AllIDSchema": "allid",
    "ReleaseResponse": "allid",
    "BookingCreateSchema": "bookingcreate",
    "BookingCreateResponse": "bookingcreate",
    "ExtendBookingSchema": "bookingextension",
    "ExtendBookingResponse": "bookingextension",
    "BookingSearchSchema": "bookingsearch",
    "BookingSearchResponse": "bookingsearch",
    "FloorSchema": "floorschema",
    "AddFloorSchema": "addfloor",
    "FloorSpotSchema": "floorspot",
    "AddSpotsSchema": "floorspot",
    "LotID": "lotid",
    "LotFloorSchema": "lotfloor",
    "UserCreate": "userschema",
    "UserRead": "userschema",
    "FloorCreate": "lotschema",
    "LotCreate": "lotschema",
    "build_lot": "lotschema",
}

__all__ = list(_SCHEMA_MODULES)


def __getattr__(name):
    module_name = _SCHEMA_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f".{module_name}", __name__)
    return getattr(module, name)
