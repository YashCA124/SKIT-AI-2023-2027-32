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

__all__ = [
    "AdminLoginRequest",
    "UserLoginRequest",
    "RegistrationRequest",
    "TokenResponse",
    "LocationOut",
    "UserOut",
    "LoginResponse",
    "UserLoginResponse",
    "FloorCreate",
    "LotCreate",
]


def __getattr__(name):
    if name in {"FloorCreate", "LotCreate"}:
        from .lotschema import FloorCreate, LotCreate

        return {"FloorCreate": FloorCreate, "LotCreate": LotCreate}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
