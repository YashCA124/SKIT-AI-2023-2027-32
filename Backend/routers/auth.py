import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape
from geopy.geocoders import Nominatim

from core.db import get_db

from core.security import (
    create_access_token,
    create_refresh_token,
    get_current_claims,
    get_current_refresh_claims,
    blacklist_token,
    bearer_scheme,
)
from schemas.auth import (
    AdminLoginRequest,
    UserLoginRequest,
    RegistrationRequest,
    LoginResponse,
    UserLoginResponse,
)
from models import UserType

from models import Admin, User

router = APIRouter(tags=["auth"])
geolocator = Nominatim(user_agent="parking_app")


# ---------------------------------------------------------------------------
# POST /auth/adminlogin
# ---------------------------------------------------------------------------
@router.post("/adminlogin", response_model=LoginResponse)
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = (
        db.query(Admin)
        .filter_by(username=payload.username, password=payload.password)
        .first()
    )

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(
        identity=str(admin.id), additional_claims={"role": UserType.ADMIN.value}
    )
    refresh_token = create_refresh_token(
        identity=str(admin.id), additional_claims={"role": UserType.ADMIN.value}
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {"id": admin.id, "name": getattr(admin, "username", ""), "role": UserType.ADMIN.value},
    }


# ---------------------------------------------------------------------------
# POST /auth/userlogin
# ---------------------------------------------------------------------------
@router.post("/userlogin", response_model=UserLoginResponse)
def user_login(payload: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()

    if not user or not check_password_hash(user.password, payload.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    location_updated = False
    if (
        user.location_permission_granted
        and payload.latitude is not None
        and payload.longitude is not None
    ):
        try:
            user.current_location = WKTElement(
                f"POINT({payload.longitude} {payload.latitude})", srid=4326
            )
            user.last_location_update = datetime.now(timezone.utc)
            db.commit()
            location_updated = True
        except Exception as e:
            db.rollback()
            print(f"Failed to update login location: {e}")

    role = user.user_type.value if hasattr(user.user_type, "value") else str(user.user_type)

    access_token = create_access_token(identity=str(user.id), additional_claims={"role": role})
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims={"role": role})

    current_location = None
    if user.current_location:
        try:
            location = to_shape(user.current_location)
            current_location = {"latitude": location.y, "longitude": location.x}
        except Exception:
            current_location = None

    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "location_updated": location_updated,
        "current_location": current_location,
        "user": {"id": user.id, "name": user.name, "role": role},
    }


# ---------------------------------------------------------------------------
# POST /auth/registration
# ---------------------------------------------------------------------------
@router.post("/registration", status_code=status.HTTP_201_CREATED)
def registration(payload: RegistrationRequest, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    if db.query(User).filter_by(phone_no=payload.phone_no).first():
        raise HTTPException(status_code=409, detail="Phone already exists")

    user = User(
        name=payload.name,
        email=payload.email,
        phone_no=payload.phone_no,
        password=generate_password_hash(payload.password),
        city=payload.city,
        state=payload.state,
        country=payload.country,
        location_permission_granted=payload.location_permission_granted,
    )

    try:
        if payload.location_permission_granted:
            if payload.latitude is None or payload.longitude is None:
                raise HTTPException(
                    status_code=422, detail="latitude/longitude required when location permission is granted"
                )
            point_wkt = WKTElement(f"POINT({payload.longitude} {payload.latitude})", srid=4326)
        else:
            search_query = f"{payload.city}, {payload.state}, {payload.country}"
            geo_res = geolocator.geocode(search_query)

            if not geo_res:
                raise HTTPException(status_code=422, detail="Unable to determine location from address")

            point_wkt = WKTElement(f"POINT({geo_res.longitude} {geo_res.latitude})", srid=4326)

        user.current_location = point_wkt
        user.last_location_update = datetime.now(timezone.utc)

        db.add(user)
        db.commit()
        db.refresh(user)

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate email or phone")
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.user_type.name,
        },
    }


# ---------------------------------------------------------------------------
# POST /auth/logoutcurrent
# ---------------------------------------------------------------------------
@router.post("/logoutcurrent")
def logout_current(claims: dict = Depends(get_current_claims)):
    blacklist_token(claims["jti"], expires_seconds=3600)
    return {"message": "Access token successfully logged out"}


# ---------------------------------------------------------------------------
# POST /auth/logoutrefresh
# ---------------------------------------------------------------------------
@router.post("/logoutrefresh")
def logout_refresh(claims: dict = Depends(get_current_refresh_claims)):
    blacklist_token(claims["jti"], expires_seconds=3600)
    return {"message": "Refresh token successfully logged out"}
