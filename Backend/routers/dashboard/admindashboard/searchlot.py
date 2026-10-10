import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from core.db import get_db
from core.redis_client import redis_client
from core.role_check import require_role
from models import Floor, ParkingLot, User as UserModel, UserType
from schemas import Lot, User as UserSchema

router = APIRouter(tags=["Admin"])

CACHE_TTL = 120

lot_schema = Lot()
user_schema = UserSchema()


@router.get(
    "/admin/search/lot",
    dependencies=[Depends(require_role(UserType.ADMIN))],
)
def search_parking_lot(
    lot_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    cache_key = f"parkinglot:{lot_id}"

    try:
        cache_data = redis_client.get(cache_key)
        if cache_data:
            if isinstance(cache_data, bytes):
                cache_data = cache_data.decode("utf-8")
            return json.loads(cache_data)
    except (Exception, ValueError):
        pass

    parking_lot = (
        db.query(ParkingLot)
        .options(
            selectinload(ParkingLot.floors).selectinload(Floor.spots)
        )
        .filter(ParkingLot.id == lot_id)
        .first()
    )

    if not parking_lot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parking lot not found",
        )

    user_data = db.get(UserModel, parking_lot.user_id)

    result = {
        "message": "Parking lot details retrieved successfully",
        "parking_lot": lot_schema.dump(parking_lot),
        "user": user_schema.dump(user_data) if user_data else None,
    }

    try:
        redis_client.setex(
            cache_key,
            CACHE_TTL,
            json.dumps(result),
        )
    except Exception:
        pass

    return result