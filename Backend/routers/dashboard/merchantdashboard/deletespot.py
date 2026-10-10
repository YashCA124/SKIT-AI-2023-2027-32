from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
from schemas import AllID

router = APIRouter(tags=["merchant"])


@router.post("/deletespot")
def delete_spot(
    payload: AllID,
    current_user: User = Depends(
        require_user_role(UserType.MERCHANT)
    ),
    db: Session = Depends(get_db),
):
    try:
        lot = (
            db.query(ParkingLot)
            .filter_by(id=payload.lot_id)
            .with_for_update()
            .first()
        )

        if not lot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lot not found",
            )

        if lot.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized",
            )

        floor = (
            db.query(Floor)
            .filter_by(
                parking_lot_id=payload.lot_id,
                floor_id=payload.floor_id,
            )
            .with_for_update()
            .first()
        )

        if not floor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Floor not found",
            )

        spot = (
            db.query(ParkingSpot)
            .filter_by(
                floor_id=floor.id,
                spot_id=payload.spot_id,
            )
            .with_for_update()
            .first()
        )

        if not spot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Spot not found",
            )

        if (
            spot.available == AvailableStatus.ACTIVE
            and spot.status != BookingStatus.SPOT_AVAILABLE
        ):
            spot.available = AvailableStatus.PENDING
            spot_status = "Pending"
        else:
            spot.available = AvailableStatus.DELETE
            spot_status = "Deleted"

        db.commit()

        return {
            "spot_id": payload.spot_id,
            "status": spot_status,
            "message": "Delete spot request processed",
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )