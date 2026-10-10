from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.db import get_db
from core.role_check import require_user_role
from models import Floor, ParkingLot, ParkingSpot, User, UserType
from schemas import AddSpotsSchema

router = APIRouter(tags=["merchant"])


@router.post("/addspots", status_code=status.HTTP_200_OK)
def add_spots(
    payload: AddSpotsSchema,
    current_user: User = Depends(
        require_user_role(UserType.MERCHANT)
    ),
    db: Session = Depends(get_db),
):
    lot_id = payload.lot_id
    lot = db.get(ParkingLot, lot_id)

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
            floor = (
                db.query(Floor)
                .filter_by(
                    parking_lot_id=lot_id,
                    floor_id=floor_data.floor_number,
                )
                .with_for_update()
                .first()
            )

            if not floor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Floor {floor_data.floor_number} is not available",
                )

            last_spot = (
                db.query(func.max(ParkingSpot.spot_id))
                .filter(ParkingSpot.floor_id == floor.id)
                .scalar()
                or 0
            )

            all_spots.extend(
                ParkingSpot(
                    floor_id=floor.id,
                    spot_id=last_spot + i + 1,
                )
                for i in range(floor_data.new_spots)
            )

        db.add_all(all_spots)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate spot detected",
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong",
        )

    return {"message": "Spots successfully added"}