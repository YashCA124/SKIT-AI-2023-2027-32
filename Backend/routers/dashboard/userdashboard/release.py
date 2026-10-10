from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from core.db import get_db
from core.role_check import require_role
from core.redis_client import redis_client
# from background_tasks import (
#     check_and_delete_spot, check_and_block_floor,
#     check_and_block_lot, check_and_block_spot,
#     check_and_delete_floor, check_and_delete_lot
# )
from models import (
    ParkingSpot, ParkingBooking, ParkingLot, Floor,
    BookingStatus, UserType, AvailableStatus, User
)
from schemas import AllIDSchema, ReleaseResponse

router = APIRouter(prefix="/booking", tags=["Booking Release"])

@router.post("/release", response_model=ReleaseResponse)
def release_spot(
    data: AllIDSchema,
    current_user: User = Depends(require_role(UserType.PARKING_USER)),
    db: Session = Depends(get_db)
):
    floor_key = None
    redis_updated = False

    try:
        lot = db.query(ParkingLot).filter(
            ParkingLot.id == data.lot_id,
            ParkingLot.available.in_([AvailableStatus.ACTIVE, AvailableStatus.PENDING])
        ).first()
        if not lot:
            raise HTTPException(status_code=404, detail="Lot not found")

        floor = db.query(Floor).filter(
            Floor.parking_lot_id == data.lot_id,
            Floor.floor_id == data.floor_id,
            Floor.available.in_([AvailableStatus.ACTIVE, AvailableStatus.PENDING])
        ).first()
        if not floor:
            raise HTTPException(status_code=404, detail="Floor not found")

        spot = db.query(ParkingSpot).filter(
            ParkingSpot.floor_id == floor.id,
            ParkingSpot.spot_id == data.spot_id,
            ParkingSpot.available.in_([AvailableStatus.ACTIVE, AvailableStatus.PENDING])
        ).with_for_update().first()

        if not spot:
            raise HTTPException(status_code=404, detail="Spot not found")

        if spot.status != BookingStatus.SPOT_BOOKED:
            raise HTTPException(status_code=400, detail="Spot is not currently occupied")

        curr_booking = db.query(ParkingBooking).filter_by(
            user_id=current_user.id,
            spot_id=spot.id,
            status=BookingStatus.BOOKING_ACTIVE
        ).with_for_update().first()

        if not curr_booking:
            raise HTTPException(status_code=403, detail="No active booking found")

        leaving_timestamp = curr_booking.leaving_timestamp or datetime.now(timezone.utc)
        curr_booking.leaving_timestamp = leaving_timestamp
        curr_booking.status = BookingStatus.BOOKING_COMPLETED
        spot.status = BookingStatus.SPOT_AVAILABLE

        booking_currency = curr_booking.currency
        exchange_rate = curr_booking.exchange_rate
        total_hour = curr_booking.get_total_hour
        total_cost = curr_booking.get_total_cost

        floor_key = f"floor:{floor.id}:available_spots"

        db.commit()

        if redis_client.exists(floor_key):
            redis_client.incr(floor_key)
        else:
            actual = db.query(func.count(ParkingSpot.id)).filter(
                ParkingSpot.floor_id == floor.id,
                ParkingSpot.status == BookingStatus.SPOT_AVAILABLE
            ).scalar()
            redis_client.setex(floor_key, 300, actual)

        redis_updated = True

        redis_client.delete(f"user:{current_user.id}:active_booking")
        redis_client.delete(f"user:{current_user.id}:active_dashboard:v1")
        redis_client.delete(f"user:{current_user.id}:released_records:v1")

        # check_and_block_spot.delay(spot.id)
        # check_and_delete_spot.delay(spot.id)
        # check_and_block_floor.delay(floor.id)
        # check_and_delete_floor.delay(floor.id)
        # check_and_block_lot.delay(lot.id)
        # check_and_delete_lot.delay(lot.id)

        return {
            "message": "Booking successfully completed",
            "booking_id": curr_booking.id,
            "total_cost": round(total_cost, 2),
            "currency": booking_currency,
            "exchange_rate": round(exchange_rate, 4),
            "total_time_in_hours": total_hour
        }

    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        if redis_updated and floor_key:
            try:
                redis_client.decr(floor_key)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Release failed: {str(e)}")