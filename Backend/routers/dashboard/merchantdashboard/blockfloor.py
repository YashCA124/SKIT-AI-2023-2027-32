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
from schemas import LotFloorSchema

router = APIRouter(tags=["merchant"])


@router.post("/blockfloor")
def block_floor(
    payload: LotFloorSchema,
    current_user: User = Depends(
        require_user_role(UserType.MERCHANT)
    ),
    db: Session = Depends(get_db),
):
    try:
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

        occupied_spot = (
            db.query(ParkingSpot)
            .filter(
                ParkingSpot.floor_id == floor.id,
                ParkingSpot.available == AvailableStatus.ACTIVE,
                ParkingSpot.status != BookingStatus.SPOT_AVAILABLE,
            )
            .with_for_update()
            .first()
        )

        if occupied_spot is None:
            floor.available = AvailableStatus.BLOCK
            spot_status = "Blocked"
        else:
            floor.available = AvailableStatus.PENDING
            # check_and_block_floor.delay(floor.id)
            spot_status = "Pending"

        floor_number = floor.floor_id
        db.commit()

        return {
            "floor_id": floor_number,
            "status": spot_status,
            "message": "Block floor request processed",
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