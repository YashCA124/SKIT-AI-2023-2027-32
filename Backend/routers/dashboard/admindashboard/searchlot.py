import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload

from database import get_db
from extensions import redis_client
from models import ParkingLot, Floor, User as UserModel, UserType
from rolecheck.role_required import require_role
from schemas import Lot, User as UserSchema  # marshmallow schemas, still used for serialization

router = APIRouter(tags=["Admin"])

CACHE_TTL = 120

lot_schema = Lot()
user_schema = UserSchema()


@router.get(
    "/admin/search/lot",
    dependencies=[Depends(require_role(UserType.ADMIN))],
)
def search_parking_lot(
    lot_id: int = Query(..., gt=0),  # replaces the LotID marshmallow schema
    db: Session = Depends(get_db),
):
    cache_key = f"parkinglot:{lot_id}"

    try:
        cache_data = redis_client.get(cache_key)
    except Exception:
        cache_data = None

    if cache_data:
        return json.loads(cache_data)

    parking_lot = (
        db.query(ParkingLot)
        .options(selectinload(ParkingLot.floors).selectinload(Floor.spots))
        .filter(ParkingLot.id == lot_id)
        .first()
    )

    if not parking_lot:
        return JSONResponse(status_code=404, content={"message": "Parking lot not found"})

    user_data = db.get(UserModel, parking_lot.user_id)

    result = {
        "message": "Parking lot details retrieved successfully",
        "parking_lot": lot_schema.dump(parking_lot),
        "user": user_schema.dump(user_data),
    }

    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    except Exception:
        pass

    return result
