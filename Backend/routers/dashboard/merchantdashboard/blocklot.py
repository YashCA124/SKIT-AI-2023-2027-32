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
from schemas import LotID

router = APIRouter(tags=["merchant"])


@router.post("/blocklot")
def block_lot(
    payload: LotID,
    current_user: User = Depends(
        require_user_role(UserType.MERCHANT)
    ),
    db: Session = Depends(get_db),
):
    lot_id = payload.lot_id

    try:
        lot = (
            db.query(ParkingLot)
            .filter_by(id=lot_id)
            .with_for_update()
            .first()
        )

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

        occupied_spot = (
            db.query(ParkingSpot)
            .join(Floor, ParkingSpot.floor_id == Floor.id)
            .filter(
                Floor.parking_lot_id == lot_id,
                ParkingSpot.available == AvailableStatus.ACTIVE,
                ParkingSpot.status != BookingStatus.SPOT_AVAILABLE,
            )
            .first()
        )

        if occupied_spot is None:
            lot.available = AvailableStatus.BLOCK
            lot_status = "Blocked"
        else:
            lot.available = AvailableStatus.PENDING
            lot_status = "Pending"

        db.commit()

        return {
            "status": lot_status,
            "message": "Block lot request processed",
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