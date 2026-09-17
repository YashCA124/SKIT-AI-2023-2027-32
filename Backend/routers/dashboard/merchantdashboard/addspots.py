from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from dependencies import DbSession, MerchantId
from errors import api_error, raise_if_error
from models import Floor, ParkingLot, ParkingSpot
from schemas import AddSpotsSchema
from services.availability_checks import validate_floor_active, validate_lot_active

router = APIRouter(tags=["merchant"])


@router.post("/addspots")
def add_spots(payload: AddSpotsSchema, db: DbSession, user_id: MerchantId):

    lot_id = payload.lot_id
    lot = db.get(ParkingLot, lot_id)

    if not lot:
        raise api_error(404, "Parking lot not found")

    if lot.user_id != user_id:
        raise api_error(403, "Unauthorized access")

    raise_if_error(validate_lot_active(lot))

    try:
        all_spots = []

        for floor_data in payload.floor:

            floor = (
                db.query(Floor)
                .filter_by(parking_lot_id=lot_id, floor_id=floor_data.floor_number)
                .with_for_update()
                .first()
            )

            if not floor:
                raise api_error(
                    404, f"Floor {floor_data.floor_number} is not available"
                )

            raise_if_error(validate_floor_active(floor))

            last_spot = (
                db.query(func.max(ParkingSpot.spot_id))
                .filter(ParkingSpot.floor_id == floor.id)
                .with_for_update()
                .scalar()
                or 0
            )

            all_spots.extend(
                ParkingSpot(floor_id=floor.id, spot_id=last_spot + i + 1)
                for i in range(floor_data.new_spots)
            )

        db.add_all(all_spots)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise api_error(409, "Duplicate spot detected")

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"message": "Something went wrong", "error": str(e)},
        )

    return {"message": "Spots successfully added"}
