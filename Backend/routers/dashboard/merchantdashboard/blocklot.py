from fastapi import APIRouter, HTTPException

from background_tasks.blocklot import check_and_block_lot
from dependencies import DbSession, MerchantId
from errors import api_error, raise_if_error
from models import AvailableStatus, BookingStatus, Floor, ParkingLot, ParkingSpot
from schemas import LotID
from services.availability_checks import validate_lot_blockable

router = APIRouter(tags=["merchant"])


@router.post("/blocklot")
def block_lot(payload: LotID, db: DbSession, user_id: MerchantId):

    lot_id = payload.lot_id

    try:
        lot = db.query(ParkingLot).filter_by(id=lot_id).with_for_update().first()

        if not lot:
            raise api_error(404, "Parking lot not found")

        if lot.user_id != user_id:
            raise api_error(403, "Unauthorized")

        raise_if_error(validate_lot_blockable(lot))

        occupied_spot = (
            db.query(ParkingSpot)
            .join(Floor, ParkingSpot.floor_id == Floor.id)
            .filter(
                Floor.parking_lot_id == lot_id,
                ParkingSpot.available == AvailableStatus.ACTIVE,
                ParkingSpot.status != BookingStatus.SPOT_AVAILABLE,
            )
            .with_for_update()
            .limit(1)
            .first()
        )

        if not occupied_spot:
            lot.available = AvailableStatus.BLOCK
            lot_status = "Blocked"
        else:
            lot.available = AvailableStatus.PENDING
            check_and_block_lot.delay(lot.id)
            lot_status = "Pending"

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"message": f"error : {str(e)}"})

    return {"status": lot_status, "message": "Block lot request processed"}
