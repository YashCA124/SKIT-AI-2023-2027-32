import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, selectinload

from database import get_db
from extensions import redis_client
from models import ParkingBooking, ParkingSpot, Floor, User, UserType, BookingStatus
from rolecheck.role_required import require_role
from schemas import ActiveBooking, CompletedBooking, UserSchema  # marshmallow, still used for serialization

router = APIRouter(tags=["Admin"])

CACHE_TTL = 120

active_schema = ActiveBooking(many=True)
completed_schema = CompletedBooking(many=True)
user_schema = UserSchema()


def _bookings_for(db: Session, user_id: int, status: BookingStatus):
    return (
        db.query(ParkingBooking)
        .options(
            selectinload(ParkingBooking.spot)
            .selectinload(ParkingSpot.floor)
            .selectinload(Floor.parking_lot)
        )
        .filter(ParkingBooking.user_id == user_id, ParkingBooking.status == status)
        .order_by(ParkingBooking.parking_timestamp)
        .all()
    )


@router.get(
    "/admin/search/user",
    dependencies=[Depends(require_role(UserType.ADMIN))],
)
def search_user(
    user_id: int = Query(..., gt=0),  # replaces the UserID marshmallow schema
    db: Session = Depends(get_db),
):
    cache_key = f"user:{user_id}"

    try:
        cache_data = redis_client.get(cache_key)
    except Exception:
        cache_data = None

    if cache_data:
        return json.loads(cache_data)

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return JSONResponse(status_code=404, content={"message": "User not found"})

    active_booking = _bookings_for(db, user_id, BookingStatus.BOOKING_ACTIVE)
    completed_booking = _bookings_for(db, user_id, BookingStatus.BOOKING_COMPLETED)

    result = {
        "message": "User Details along with parking history",
        "user_data": user_schema.dump(user),
        "active_booking": active_schema.dump(active_booking),
        "completed_booking": completed_schema.dump(completed_booking),
    }

    # The original didn't guard this call; a Redis outage shouldn't fail the request.
    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    except Exception:
        pass

    return result
