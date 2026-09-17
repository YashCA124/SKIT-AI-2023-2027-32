from fastapi import APIRouter, HTTPException

from background_tasks.deletefloor import check_and_delete_floor
from dependencies import DbSession, MerchantId
from errors import api_error, raise_if_error
from models import AvailableStatus, BookingStatus, Floor, ParkingLot, ParkingSpot
from schemas import LotFloorSchema
from services.availability_checks import validate_floor_deletable, validate_lot_active

router = APIRouter(tags=["merchant"])


@router.post("/deletefloor")
def delete_floor(payload: LotFloorSchema, db: DbSession, user_id: MerchantId):

    try:
        lot = (
            db.query(ParkingLot)
            .filter_by(id=payload.lot_id)
            .with_for_update()
            .first()
        )

        if not lot:
            raise api_error(404, "Parking lot not found")

        if lot.user_id != user_id:
            raise api_error(403, "Unauthorized access")

        floor = (
            db.query(Floor)
            .filter_by(parking_lot_id=payload.lot_id, floor_id=payload.floor_id)
            .with_for_update()
            .first()
        )

        if not floor:
            raise api_error(404, "Floor not found")

        raise_if_error(validate_lot_active(lot))
        raise_if_error(validate_floor_deletable(floor))

        occupied_spot = (
            db.query(ParkingSpot)
            .filter(
                ParkingSpot.floor_id == floor.id,
                ParkingSpot.available == AvailableStatus.ACTIVE,
                ParkingSpot.status != BookingStatus.SPOT_AVAILABLE,
            )
            .with_for_update()
            .limit(1)
            .first()
        )

        if not occupied_spot:
            floor.available = AvailableStatus.DELETE
            floor_status = "Deleted"
        else:
            floor.available = AvailableStatus.PENDING
            check_and_delete_floor.delay(floor.id)
            floor_status = "Pending"

        floor_number = floor.floor_id
        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": f"error : {str(e)}"})

    return {
        "floor_id": floor_number,
        "status": floor_status,
        "message": "Delete floor request processed",
    }
