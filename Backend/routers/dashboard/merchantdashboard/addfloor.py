from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from core.db import get_db
from core.role_check import require_user_role
from models import (
    AvailableStatus,
    BookingStatus,
    Floor,
    ParkingLot,
    ParkingSpot,
    User,
    UserType,
)
from schemas import AddFloorSchema

router = APIRouter(tags=["merchant"])


@router.post("/addfloor", status_code=status.HTTP_201_CREATED)
def add_floor(
    payload: AddFloorSchema,
    current_user: User = Depends(
        require_user_role(UserType.MERCHANT)
    ),
    db: Session = Depends(get_db),
):
    lot = db.get(ParkingLot, payload.lot_id)

    if not lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking lot not found",
        )

    if lot.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access",
        )

    try:
        all_spots = []

        for floor_data in payload.floor:
            floor = Floor(
                parking_lot_id=lot.id,
                floor_id=floor_data.floor_number,
                available=AvailableStatus(floor_data.available),
            )

            db.add(floor)
            db.flush()

            for i in range(1, floor_data.total_number_of_spots + 1):
                all_spots.append(
                    ParkingSpot(
                        floor_id=floor.id,
                        spot_id=i,
                        status=BookingStatus.SPOT_AVAILABLE,
                        available=AvailableStatus.ACTIVE,
                    )
                )

        db.add_all(all_spots)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate floor number or database constraint violation",
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return {"message": "Floor successfully created"}