import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload

from core.db import get_db
from core.redis_client import redis_client
from models import ParkingBooking, ParkingSpot, Floor, BookingStatus, UserType
from core.role_check import require_role
from schemas.activebooking import ActiveBooking

router = APIRouter()

schema = ActiveBooking(many=True)  # existing marshmallow schema reused
CACHE_TTL = 30


@router.get("/dashboard")
def get_user_dashboard(
    current_user=Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db),
):
    # role_required returns the authenticated user (replaces get_jwt_identity)
    user_id = int(current_user.id)

    cache_key = f"user:{user_id}:active_dashboard:v1"

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
            user_id=user_id,
            status=BookingStatus.BOOKING_ACTIVE,
        )
        .order_by(ParkingBooking.parking_timestamp)
        .all()
    )

    result = {
        "active_bookings": schema.dump(records),
        "user_id": user_id,
    }

    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    except Exception:
        pass

    return result
