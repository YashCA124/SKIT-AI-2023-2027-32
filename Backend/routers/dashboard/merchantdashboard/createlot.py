from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from geopy.geocoders import Nominatim
from pydantic import BaseModel, ConfigDict

from core.db import get_db                    
from models import UserType, ParkingLot, User
from auth import require_role, get_current_user  
from schemas import LotCreate, build_lot 


geolocator = Nominatim(user_agent="parking_app")

router = APIRouter()


@router.post(
    "/lots",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new parking lot",
)
def create_lot(
    payload: LotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserType.PARKING_MERCHANT)),
):

    lot = build_lot(payload, db)

    lot.user_id = current_user.id

    existing_lot = (
        db.query(ParkingLot)
        .filter(
            func.ST_DWithin(
                ParkingLot.location_coordinates,
                lot.location_coordinates,
                50,
            )
        )
        .first()
    )

    if existing_lot:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A parking lot already exists at this location",
        )

    try:
        db.add(lot)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate data exists",
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Lot created successfully"},
    )