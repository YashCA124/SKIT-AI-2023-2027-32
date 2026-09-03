from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @field_validator("email", "password", mode="before")
    @classmethod
    def strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v


class RegistrationRequest(BaseModel):

    name: str
    email: EmailStr
    phone_no: str
    password: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    location_permission_granted: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class TokenResponse(BaseModel):
    access_token: str


class LocationOut(BaseModel):
    latitude: float
    longitude: float


class UserOut(BaseModel):
    id: int
    name: str
    role: str


class LoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    user: UserOut


class UserLoginResponse(LoginResponse):
    location_updated: bool
    current_location: Optional[LocationOut] = None