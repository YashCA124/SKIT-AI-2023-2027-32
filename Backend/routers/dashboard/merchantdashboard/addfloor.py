from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from dependencies import DbSession, MerchantId
from errors import api_error, raise_if_error
from models import AvailableStatus, BookingStatus, Floor, ParkingLot, ParkingSpot
from schemas import AddFloorSchema
from services.availability_checks import validate_lot_active

router = APIRouter(tags=["merchant"])


@router.post("/addfloor", status_code=status.HTTP_201_CREATED)
def add_floor(payload: AddFloorSchema, db: DbSession, user_id: MerchantId):

    lot = db.get(ParkingLot, payload.lot_id)

    if not lot:
        raise api_error(404, "Parking lot not found")

    if lot.user_id != user_id:
        raise api_error(403, "Unauthorized access")

    raise_if_error(validate_lot_active(lot))

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
        raise api_error(
            409, "Duplicate floor number already exists in this parking lot"
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"message": "Something went wrong", "error": str(e)},
        )

    return {"message": "Floor successfully created"}
