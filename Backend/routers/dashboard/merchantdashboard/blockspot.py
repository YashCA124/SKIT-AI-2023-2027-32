from fastapi import APIRouter, HTTPException

from background_tasks.blockspot import check_and_block_spot
from dependencies import DbSession, MerchantId
from errors import api_error, raise_if_error
from models import AvailableStatus, BookingStatus, Floor, ParkingLot, ParkingSpot
from schemas import AllID
from services.availability_checks import (
    validate_floor_active,
    validate_lot_active,
    validate_spot_blockable,
)

router = APIRouter(tags=["merchant"])


@router.post("/blockspot")
def block_spot(payload: AllID, db: DbSession, user_id: MerchantId):

    try:
        lot = (
            db.query(ParkingLot)
            .filter_by(id=payload.lot_id)
            .with_for_update()
            .first()
        )

        # NOTE: the Flask version called validate_lot_active(lot) before any
        # None check, which raised AttributeError -> 500 for a missing lot.
        if not lot:
            raise api_error(404, "Parking lot not found")

        if lot.user_id != user_id:
            raise api_error(403, "Unauthorized")

        raise_if_error(validate_lot_active(lot))

        floor = (
            db.query(Floor)
            .filter_by(parking_lot_id=payload.lot_id, floor_id=payload.floor_id)
            .with_for_update()
            .first()
        )

        if not floor:
            raise api_error(404, "Floor not found")

        raise_if_error(validate_floor_active(floor))

        spot = (
            db.query(ParkingSpot)
            .filter_by(floor_id=floor.id, spot_id=payload.spot_id)
            .with_for_update()
            .first()
        )

        if not spot:
            raise api_error(404, "Spot not found")

        raise_if_error(validate_spot_blockable(spot))

        occupied_spot = (
            db.query(ParkingSpot)
            .filter(
                ParkingSpot.id == spot.id,
                ParkingSpot.available == AvailableStatus.ACTIVE,
                ParkingSpot.status != BookingStatus.SPOT_AVAILABLE,
            )
            .with_for_update()
            .first()
        )

        if not occupied_spot:
            spot.available = AvailableStatus.BLOCK
            spot_status = "Blocked"
        else:
            spot.available = AvailableStatus.PENDING
            check_and_block_spot.delay(spot.id)
            spot_status = "Pending"

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": f"error : {str(e)}"})

    return {
        "spot_id": payload.spot_id,
        "status": spot_status,
        "message": "Block spot request processed",
    }
