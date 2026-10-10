import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from core.db import get_db
from core.role_check import require_role
from core.redis_client import redis_client
from models import ParkingBooking, ParkingSpot, Floor, UserType, BookingStatus, User
from schemas import ReleasedRecordResponse

router = APIRouter(prefix="/records", tags=["Released Records"])

@router.get("/released", response_model=ReleasedRecordResponse)
def get_released_records(
    current_user: User = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db)
):
    cache_key = f"user:{current_user.id}:released_records:v1"

    try:
        cached_data = redis_client.get(cache_key)
    except Exception:
        cached_data = None

    if cached_data:
        return json.loads(cached_data)

    records = (
        db.query(ParkingBooking)
        .options(
            selectinload(ParkingBooking.spot)
            .selectinload(ParkingSpot.floor)
            .selectinload(Floor.parking_lot)
        )
        .filter_by(
            user_id=current_user.id,
            status=BookingStatus.BOOKING_COMPLETED
        )
        .order_by(ParkingBooking.parking_timestamp)
        .all()
    )

    serialized_records = [
        {
            "id": r.id,
            "spot_id": r.spot_id,
            "cost_per_unit": round(r.cost_per_unit, 2),
            "currency": r.currency,
            "parking_timestamp": r.parking_timestamp.isoformat() if r.parking_timestamp else None,
            "leaving_timestamp": r.leaving_timestamp.isoformat() if r.leaving_timestamp else None,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status)
        }
        for r in records
    ]

    result = {
        "message": "Released record list",
        "released_records": serialized_records
    }

    try:
        redis_client.setex(cache_key, 120, json.dumps(result))
    except Exception:
        pass

    return result